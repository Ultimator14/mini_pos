#!/usr/bin/python3.10

# region includes
from __future__ import annotations  # required for type hinting of classes in itself
from typing import Optional
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import os.path
import json
import pickle
# endregion includes


# region types
AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, Optional[int], Optional[int], Optional[str]]
TablesGridT = list[list[Optional[TablesGridTupleT]]]
# endregion types


# region config
CONFIG_FILE: str = "config.json"
DATABASE_FILE: str = "data.pkl"

tables_size: tuple[int, int]
tables_grid: TablesGridT = []
tables: list[str]
available_products: AvailableProductsT = dict()
category_map: dict[int, str] = dict()

show_category_names: bool = False
split_categories: bool = False
persistence: bool = False


def load_config():
    log_info("Loading configuration...")
    with open("config.json", "r") as afile:
        config_data = json.load(afile)

        Order.auto_close = config_data["ui"]["auto_close"]
        Order.show_completed = config_data["ui"]["show_completed"]  # zero = don't show
        Order.timeout_warn = config_data["ui"]["timeout"][0]
        Order.timeout_crit = config_data["ui"]["timeout"][1]

        global tables_size, tables_grid, tables
        tables_size = tuple(config_data["table"]["size"])

        # parse tables
        grid: TablesGridT = [[None for x in range(tables_size[0])] for y in range(tables_size[1])]

        for x, y, xlen, ylen, name in config_data["table"]["names"]:
            if xlen < 1 or ylen < 1:
                log_error("Invalid config option. Table can't have length < 1")
                exit(1)
            if x + xlen > tables_size[0] or y + ylen > tables_size[1]:
                log_error("Table can't be placed outside the grid")
                exit(1)

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        log_warn(f"Duplicate table position {str(i)}/{str(j)}. Check your config")
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        tables_grid = grid

        tables = [name for _, _, _, _, name in config_data["table"]["names"]]

        global available_products, category_map
        available_products = dict(enumerate(
            [tuple(product) for product in config_data["product"]["available"]]
            , start=1))
        category_map = {index: name for index, name in config_data["product"]["categories"]}

        global split_categories, show_category_names
        split_categories = config_data["ui"]["split_categories"]
        show_category_names = config_data["ui"]["show_category_names"]

        global persistence
        persistence = config_data["persistence"]
# endregion config


# region persistence
def persist_data() -> None:
    log_info("Persisting data...")
    with open(DATABASE_FILE, "wb") as afile:
        pickle.dump((orders, completed_orders, Order.counter, Product.counter), afile)


def restore_data() -> None:
    log_info("Restoring data...")
    with open(DATABASE_FILE, "rb") as afile:
        global orders, completed_orders
        orders, completed_orders, Order.counter, Product.counter = pickle.load(afile)

        log_info(f"Order counter: {str(Order.counter)}")
        log_info(f"Product counter: {str(Product.counter)}")
# endregion persistence


# region helper
def _green(prompt: str) -> str:
    return f"\033[32;1m{prompt}\033[0m"


def _yellow(prompt: str) -> str:
    return f"\033[33;1m{prompt}\033[0m"


def _red(prompt: str) -> str:
    return f"\033[31;1m{prompt}\033[0m"


def log_info(msg: str) -> None:
    print(_green(f"*** Info ***: {msg}"))


def log_warn(msg: str) -> None:
    print(_yellow(f"*** Warning! ***: {msg}"))


def log_error(msg: str) -> None:
    print(_red(f"*** Error! ***: {msg}"))
# endregion helper


# region products
class Product:
    counter: int = 1

    @staticmethod
    def next_product_num() -> int:
        next_num = Product.counter
        Product.counter += 1

        return next_num

    def __init__(self, name: str, price: float, amount: int, comment=""):
        self._num: int = Product.next_product_num()

        self._name: str = name
        self._price: float = price
        self._amount: int = amount
        self._comment: str = comment

        self._completed: bool = False

    @property
    def num(self) -> int:
        return self._num

    @property
    def name(self) -> str:
        return self._name

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def comment(self) -> str:
        return self._comment

    @property
    def completed(self) -> bool:
        return self._completed

    def complete(self) -> None:
        if not self._completed:
            self._completed = True
            log_info(f"Completed product {str(self._num)}")


def handle_product_completed_event(completed_data: str, order_data: str) -> None:
    if not completed_data.isdigit() or not order_data.isdigit():
        log_error("POST in /bar but filetype not convertible to integer")
        return

    order = orders.get_order_by_num(int(request.form["order"]))

    if order is None:
        log_error("POST in /bar but no matching Order found")
        return

    product = order.get_product_by_num(int(request.form["product-completed"]))

    if product is None:
        log_error("POST in /bar but no matching Product for order found")
        return

    product.complete()

    if Order.auto_close:
        if all([p.completed for p in order.products]):
            log_info("Last Product completed. Attempting auto_close")
            order.complete()
# endregion products


# region orders
class Order:
    counter: int = 1

    # set defaults
    auto_close: bool
    overview: bool
    show_completed: int
    timeout_warn: int
    timeout_crit: int

    @staticmethod
    def next_order_num() -> int:
        next_num = Order.counter
        Order.counter += 1

        return next_num

    def __init__(self, table: str):
        self._num: int = Order.next_order_num()
        self._table: str = table
        self._products: list[Product] = []
        self._date: datetime = datetime.now()
        self._completed_at: Optional[datetime] = None

    @property
    def num(self) -> int:
        return self._num

    @property
    def table(self) -> str:
        return self._table

    @property
    def products(self) -> list[Product]:
        return self._products

    @property
    def active_since(self) -> str:
        timediff = datetime.now() - self._date
        if timediff > timedelta(minutes=60):
            return ">60min"

        seconds_aligned = timediff.seconds // 5 * 5  # align by 5 seconds (easy way to circumvent javascript timers)
        seconds = str(seconds_aligned % 60).rjust(2, '0')
        minutes = str(seconds_aligned // 60).rjust(2, '0')

        return f"{minutes}:{seconds}"

    @property
    def active_since_timeout_class(self) -> str:
        timediff = datetime.now() - self._date
        if timediff > timedelta(seconds=Order.timeout_crit):
            return "timeout_crit"
        elif timediff > timedelta(seconds=Order.timeout_warn):
            return "timeout_warn"
        else:
            return "timeout_ok"

    @property
    def completed_at(self) -> str:
        if self._completed_at is None:
            log_warn(f"completed_at for order {str(self._num)} called but order is not completed")
            return ""

        return self._completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def add_products(self, *products: Product) -> None:
        for product in products:
            self._products.append(product)
            log_info(f"Added product {str(product.num)}")

    def add(self) -> None:
        orders.append(self)
        log_info(f"Added order {str(self._num)}")
        if persistence:
            persist_data()

    def complete(self) -> None:
        for product in self._products:
            product.complete()

        self._completed_at = datetime.now()

        completed_orders.append(self)
        orders.remove(self)

        log_info(f"Completed order {str(self._num)}")
        if persistence:
            persist_data()

    def get_product_by_num(self, num) -> Optional[Product]:
        return next((p for p in self.products if num == p.num), None)


def handle_order_completed_event(completed_data: str) -> None:
    if not completed_data.isdigit():
        log_error("POST in /bar but filetype not convertible to integer")
        return

    order = orders.get_order_by_num(int(request.form["order-completed"]))

    if order is None:
        log_error("POST in /bar but no matching Order to complete")
        return

    order.complete()


class Orders:
    def __init__(self):
        self._order_list: list[Order] = []

    def __iter__(self):
        return iter(self._order_list)  # for order in orders

    def __getitem__(self, item):
        return self._order_list.__getitem__(item)  # x = order[0]

    def __setitem__(self, key, value):
        return self._order_list.__setitem__(key, value)  # order[0] = x

    def append(self, order: Order) -> None:
        self._order_list.append(order)

    def remove(self, order: Order) -> None:
        self._order_list.remove(order)

    def get_order_by_num(self, num) -> Optional[Order]:
        return next((o for o in self._order_list if num == o.num), None)
# endregion orders


orders = Orders()
completed_orders = Orders()

if not os.path.isfile(CONFIG_FILE):
    log_error("No config file found. Abort execution")
    exit(1)
load_config()  # must be after class and function definitions to prevent type error

if persistence and not os.path.isfile(DATABASE_FILE):
    log_info("No database file found. Skipping data restore")
elif persistence:
    restore_data()
else:
    log_info("Persistence disabled")

# region flask
app: Flask = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bar", strict_slashes=False)
def bar():
    return render_template("bar.html", orders=orders,
                           completed_orders=completed_orders[:-(Order.show_completed + 1):-1],
                           show_completed=bool(Order.show_completed))


@app.route("/bar", methods=["POST"])
def bar_submit():
    if "order-completed" in request.form and "product-completed" in request.form:
        log_info("POST in /bar with order and product completion data. Using order...")

    if "order-completed" in request.form:
        handle_order_completed_event(request.form["order-completed"])
    elif "product-completed" in request.form:
        if "order" in request.form:
            handle_product_completed_event(request.form["product-completed"], request.form["order"])
        else:
            log_error("POST in /bar but missing order data for completed product")
    else:
        log_error("POST in /bar but missing completion data")

    return redirect(url_for("bar"))


@app.route("/service", strict_slashes=False)
def service():
    return render_template("service.html", tables_size=tables_size, tables_grid=tables_grid,
                           active_tables={order.table for order in orders})


@app.route("/service/<table>")
def service_table(table):
    if table not in tables:
        log_error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    return render_template("service_table.html", table=table,
                           orders=[[f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "")
                                    for p in o.products if not p.completed] for o in orders if o.table == table],
                           available_products=[(p, available_products[p][0], available_products[p][1],
                                                available_products[p][2]) for p in available_products],
                           category_map=category_map,
                           split_categories=split_categories,
                           show_category_names=show_category_names,
                           split_categories_init=available_products[1][2] if len(available_products) > 0 else 0
                           )


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    if table not in tables:
        log_error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    new_order = Order(table)

    for available_product in range(1, len(available_products) + 1):
        if f"amount-{available_product}" not in request.form:
            log_warn(f"POST in /service/<table> but missing amount-{available_product} event. Skipping...")
            continue

        if not request.form[f"amount-{available_product}"].isdigit():
            log_warn("POST in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(request.form[f"amount-{available_product}"])

        if f"comment-{available_product}" not in request.form:
            log_warn(f"POST in /service/<table> but missing comment-{available_product} event")
            comment = ""
        else:
            comment = request.form[f"comment-{available_product}"]

        if amount > 0:
            name, price, _ = available_products[available_product]
            product = Product(name, price, amount, comment)
            new_order.add_products(product)

    if not new_order.products:
        log_warn("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        new_order.add()

    return redirect(url_for("service"))


@app.route("/admin", strict_slashes=False)
def admin():
    return render_template("admin.html")


@app.route("/admin", methods=["POST"])
def admin_submit():
    if "reload_config" in request.form:
        log_info("Reloading config...")
        load_config()
    else:
        log_warn("POST in /admin but nothing to do")

    return redirect(url_for("admin"))
# endregion flask


if __name__ == "__main__":
    # for production run
    # sysctl -w net.ipv4.ip_unprivileged_port_start=80
    # gunicorn --bind 0.0.0.0:80 app:app
    # sysctl -w net.ipv4.ip_unprivileged_port_start=1024
    #
    app.run()
