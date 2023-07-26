#!/usr/bin/python3.11

from __future__ import annotations  # required for type hinting of classes in itself

import json
import os.path
import pickle
import sys
from datetime import datetime, timedelta
from random import randint

from flask import Flask, redirect, render_template, request, url_for, jsonify

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]


CONFIG_FILE: str = "config.json"
DATABASE_FILE: str = "data.pkl"

tables_size: tuple[int, int]
tables_grid: TablesGridT = []
tables: list[str]
available_products: AvailableProductsT = {}
category_map: dict[int, str] = {}

show_category_names: bool = False
split_categories: bool = False
persistence: bool = False

def _green(prompt: str) -> str:
    return f"\033[32;1m{prompt}\033[0m"  # ]]


def _yellow(prompt: str) -> str:
    return f"\033[33;1m{prompt}\033[0m"  # ]]


def _red(prompt: str) -> str:
    return f"\033[31;1m{prompt}\033[0m"  # ]]


def log_info(msg: str) -> None:
    print(_green(f"*** Info ***: {msg}"))  # ]]


def log_warn(msg: str) -> None:
    print(_yellow(f"*** Warning! ***: {msg}"))  # ]]


def log_error(msg: str) -> None:
    print(_red(f"*** Error! ***: {msg}"))  # ]]


def load_config():
    log_info("Loading configuration...")
    with open("config.json", encoding="utf-8") as afile:
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
                sys.exit(1)
            if x + xlen > tables_size[0] or y + ylen > tables_size[1]:
                log_warn("Table can't be placed outside the grid. Adjusting grid size.")
                tables_size[0] = max(tables_size[0], x + xlen)
                tables_size[1] = max(tables_size[1], y + ylen)

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        log_warn(f"Duplicate table position {i!s}/{j!s}. Check your config")
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        tables_grid = grid

        tables = [name for _, _, _, _, name in config_data["table"]["names"]]

        if len(set(tables)) != len(tables):
            log_error("Duplicate table name found. Tables names must be unique")
            sys.exit(1)

        global available_products, category_map
        available_products = dict(
            enumerate([tuple(product) for product in config_data["product"]["available"]], start=1)
        )
        category_map = dict(config_data["product"]["categories"])

        global split_categories, show_category_names
        split_categories = config_data["ui"]["split_categories"]
        show_category_names = config_data["ui"]["show_category_names"]

        global persistence
        persistence = config_data["persistence"]


def persist_data() -> None:
    log_info("Persisting data...")
    with open(DATABASE_FILE, "wb") as afile:
        pickle.dump((orders, completed_orders, Order.counter, Product.counter), afile)


def restore_data() -> None:
    log_info("Restoring data...")
    with open(DATABASE_FILE, "rb") as afile:
        global orders, completed_orders
        orders, completed_orders, Order.counter, Product.counter = pickle.load(afile)

        log_info(f"Order counter: {Order.counter!s}")
        log_info(f"Product counter: {Product.counter!s}")



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
            log_info(f"Completed product {self._num!s}")


def handle_product_completed_event(product_id: int, order_id: int) -> None:
    order = orders.get_order_by_num(order_id)

    if order is None:
        log_error("POST in /bar but no matching Order found")
        return

    product = order.get_product_by_num(product_id)

    if product is None:
        log_error("POST in /bar but no matching Product for order found")
        return

    product.complete()

    if Order.auto_close and all(p.completed for p in order.products):
        log_info("Last Product completed. Attempting auto_close")
        order.complete()


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

    def __init__(self, table: str, nonce: int):
        self._nonce = nonce
        self._num: int = Order.next_order_num()
        self._table: str = table
        self._products: list[Product] = []
        self._date: datetime = datetime.now()
        self._completed_at: datetime | None = None

    @property
    def nonce(self) -> int:
        return self._nonce

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
        seconds = str(seconds_aligned % 60).rjust(2, "0")
        minutes = str(seconds_aligned // 60).rjust(2, "0")

        return f"{minutes}:{seconds}"

    @property
    def active_since_timeout_class(self) -> str:
        timediff = datetime.now() - self._date
        if timediff > timedelta(seconds=Order.timeout_crit):
            return "timeout_crit"
        if timediff > timedelta(seconds=Order.timeout_warn):
            return "timeout_warn"
        return "timeout_ok"

    @property
    def completed_at(self) -> str:
        if self._completed_at is None:
            log_warn(f"completed_at for order {self._num!s} called but order is not completed")
            return ""

        return self._completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def add_products(self, *products: Product) -> None:
        for product in products:
            self._products.append(product)
            log_info(f"Added product {product.num!s}")

    def add(self) -> None:
        orders.append(self)
        log_info(f"Added order {self._num!s}")
        if persistence:
            persist_data()

    def complete(self) -> None:
        for product in self._products:
            product.complete()

        self._completed_at = datetime.now()

        completed_orders.append(self)
        orders.remove(self)

        log_info(f"Completed order {self._num!s}")
        if persistence:
            persist_data()

    def get_product_by_num(self, num) -> Product | None:
        return next((p for p in self.products if num == p.num), None)


def handle_order_completed_event(order_id: int) -> None:
    order = orders.get_order_by_num(order_id)

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

    def __len__(self):
        return self._order_list.__len__()

    def append(self, order: Order) -> None:
        self._order_list.append(order)

    def remove(self, order: Order) -> None:
        self._order_list.remove(order)

    def get_order_by_num(self, num) -> Order | None:
        return next((o for o in self._order_list if num == o.num), None)


orders = Orders()
completed_orders = Orders()

if not os.path.isfile(CONFIG_FILE):
    log_error("No config file found. Abort execution")
    sys.exit(1)
load_config()  # must be after class and function definitions to prevent type error

if persistence and not os.path.isfile(DATABASE_FILE):
    log_info("No database file found. Skipping data restore")
elif persistence:
    restore_data()
else:
    log_info("Persistence disabled")

app: Flask = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bar", strict_slashes=False)
def bar():
    return render_template(
        "bar.html",
        orders=orders,
        completed_orders=completed_orders[: -(Order.show_completed + 1) : -1],
        show_completed=bool(Order.show_completed),
    )


@app.route("/fetch/bar", strict_slashes=False)
def fetch_bar():
    return render_template(
        "bar_body.html",
        orders=orders,
        completed_orders=completed_orders[: -(Order.show_completed + 1) : -1],
        show_completed=bool(Order.show_completed),
    )


@app.route("/bar", methods=["POST"])
def bar_submit():
    if "order-completed" in request.form and "product-completed" in request.form:
        log_info("POST in /bar with order and product completion data. Using order...")

    if "order-completed" in request.form:
        if not (order_id := request.form["order-completed"]).isdigit():
            log_error("POST in /bar but filetype not convertible to integer")
        else:
            handle_order_completed_event(int(order_id))

    elif "product-completed" in request.form:
        if "order" in request.form:
            if not (product_id := request.form["product-completed"]).isdigit() \
            or not (order_id := request.form["order"]).isdigit():
                log_error("POST in /bar but filetype not convertible to integer")
            else:
                handle_product_completed_event(int(product_id), int(order_id))
        else:
            log_error("POST in /bar but missing order data for completed product")

    else:
        log_error("POST in /bar but missing neither order nor product specified")

    return redirect(url_for("bar"))


@app.route("/service", strict_slashes=False)
def service():
    return render_template(
        "service.html",
        tables_size=tables_size,
        tables_grid=tables_grid,
        active_tables={order.table for order in orders},
    )


@app.route("/fetch/service", strict_slashes=False)
def fetch_service():
    active_tables = [order.table for order in orders]

    return jsonify(active_tables)


@app.route("/service/<table>")
def service_table(table):
    if table not in tables:
        log_error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    # Generate random number per order to prevent duplicate orders
    nonce = randint(0, 2**32 - 1)  # 32 bit random number

    return render_template(
        "service_table.html",
        table=table,
        orders=[
            [f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "") for p in o.products if not p.completed]
            for o in orders
            if o.table == table
        ],
        available_products=[(p, pval[0], pval[1], pval[2]) for p, pval in available_products.items()],
        category_map=category_map,
        split_categories=split_categories,
        show_category_names=show_category_names,
        split_categories_init=available_products[1][2] if len(available_products) > 0 else 0,
        nonce=nonce,
    )


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    if table not in tables:
        log_error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    if not (nonce := request.form["nonce"]):
        log_warn("POST in /service/<table> but missing nonce. Skipping...")
        return "Error! Missing nonce"

    if any(o.nonce == nonce for o in orders):
        log_warn(f"Catched duplicate order by nonce {nonce}")
        return redirect(url_for("service"))

    new_order = Order(table, nonce)

    for available_product in range(1, len(available_products) + 1):
        if f"amount-{available_product}" not in request.form:
            log_warn(f"POST in /service/<table> but missing amount-{available_product} event. Skipping...")
            continue

        if not (amount_param := request.form[f"amount-{available_product}"]).isdigit():
            log_warn("POST in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(amount_param)

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


if __name__ == "__main__":
    # for production run
    # sysctl -w net.ipv4.ip_unprivileged_port_start=80
    # gunicorn --bind 0.0.0.0:80 app:app
    # sysctl -w net.ipv4.ip_unprivileged_port_start=1024
    #
    app.run()
