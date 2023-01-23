#!/usr/bin/python3.10

# region includes
from __future__ import annotations  # required for type hinting of classes in itself

import os.path
from typing import Optional

from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import json
import pickle
# endregion includes


# region types
TemplateProductsT = dict[int, tuple[str, float]]
# endregion types


# region config
CONFIG_FILE: str = "config.json"
DATABASE_FILE: str = "data.pkl"
DEFAULT_AUTO_CLOSE: bool = True
DEFAULT_SHOW_COMPLETED: int = 5
DEFAULT_TIMEOUT_WARN: int = 120
DEFAULT_TIMEOUT_CRIT: int = 300

tables_x: str
tables_y: str
tables: list[str] = []
template_products: TemplateProductsT = dict()
template_products_unavailable: TemplateProductsT = dict()
persistence: bool = False


def load_config():
    log_info("Loading configuration...")
    with open("config.json", "r") as afile:
        config_data = json.load(afile)

        Order.auto_close = config_data["order"]["auto_close"]
        Order.show_completed = config_data["order"]["show_completed"]  # zero = don't show
        Order.timeout_warn = config_data["order"]["timeout"][0]
        Order.timeout_crit = config_data["order"]["timeout"][1]

        global tables_x, tables_y, tables
        tables_x = config_data["tables"][0]
        tables_y = config_data["tables"][1]
        tables = [f"{x}{y}" for x in tables_x for y in tables_y]  # tables 1A-9F

        global template_products, template_products_unavailable
        template_products = dict(enumerate([(p[0], p[1]) for p in config_data["products"]], start=1))

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

        self._name = name
        self._price = price
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


def handle_product_completed_event(completed_data: str, order_data: str):
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
    auto_close: bool = DEFAULT_AUTO_CLOSE
    show_completed: int = DEFAULT_SHOW_COMPLETED
    timeout_warn: int = DEFAULT_TIMEOUT_WARN
    timeout_crit: int = DEFAULT_TIMEOUT_CRIT

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

    def add_products(self, *products: Product):
        for product in products:
            self._products.append(product)
            log_info(f"Added product {str(product.num)}")

    def add(self):
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


@app.route("/bar")
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


@app.route("/service")
def service():
    return render_template("service.html", tables_x=tables_x, tables_y=tables_y,
                           active_tables={order.table for order in orders})


@app.route("/service/<table>")
def service_table(table):
    if table not in tables:
        log_error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    return render_template("service_table.html", table=table,
                           orders=[[f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "")
                                    for p in o.products if not p.completed] for o in orders if o.table == table],
                           template_products=[(p, template_products[p][0], template_products[p][1])
                                              for p in template_products])


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    if table not in tables:
        log_error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    new_order = Order(table)

    for template_product in range(1, len(template_products) + 1):
        if f"amount-{template_product}" not in request.form:
            log_warn(f"POST in /service/<table> but missing amount-{template_product} event. Skipping...")
            continue

        if not request.form[f"amount-{template_product}"].isdigit():
            log_warn("POST in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(request.form[f"amount-{template_product}"])

        if f"comment-{template_product}" not in request.form:
            log_warn(f"POST in /service/<table> but missing comment-{template_product} event")
            comment = ""
        else:
            comment = request.form[f"comment-{template_product}"]

        if amount > 0:
            name, price = template_products[template_product]
            product = Product(name, price, amount, comment)
            new_order.add_products(product)

    if not new_order.products:
        log_warn("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        new_order.add()

    return redirect(url_for("service"))
# endregion flask


if __name__ == "__main__":
    # for production run
    # gunicorn --bind 0.0.0.0:5000 app:app
    #
    app.run()
