#!/usr/bin/python3.10

# region includes
from __future__ import annotations  # required for type hinting of classes in itself
import json
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

from typing import Union
# endregion includes

# region config
CONFIG_FILE = "config.json"

config_file = open("config.json", "r")
config_data = json.load(config_file)
config_file.close()
# endregion config


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


# region types
Template_Products = dict[int, tuple[str, float]]
# endregion types


# region products
template_products: Template_Products = dict(enumerate([(p[0], p[1]) for p in config_data["products"]], start=1))
num_template_products: int = len(template_products)


class Product:
    product_counter: int = 1

    @staticmethod
    def next_product_num() -> int:
        next_num = Product.product_counter
        Product.product_counter += 1

        return next_num

    def __init__(self, template_product: int, amount: int, comment="", num=None):
        if num:
            self._num: int = num
        else:
            self._num: int = Product.next_product_num()

        self._template_product: int = template_product
        self._amount: int = amount
        self._comment: str = comment

        self._completed: bool = False

    @property
    def num(self) -> int:
        return self._num

    @property
    def name(self) -> str:
        if self._template_product != 0:
            return template_products[self._template_product][0]
        else:
            return "Invalid"

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
        self._completed = True


def handle_product_completed_event(completed_data: str, order_data: str):
    if not completed_data.isdigit() or not order_data.isdigit():
        log_error("POST in /bar but filetype not convertible to integer")
        return

    order: Union[Order, None] = next((order for order in orders if int(request.form["order"]) == order.num), None)

    if order is None:
        log_error("POST in /bar but no matching Order found")
        return

    product: Union[Product, None] = next((p for p in order.products if int(request.form["product-completed"]) == p.num), None)

    if product is None:
        log_error("POST in /bar but no matching Product for order found")
        return

    product.complete()
    log_info(f"Completed product {str(product.num)}")

    if all([p.completed for p in order.products]):
        complete_order(order)
# endregion products


# region orders
class Order:
    order_counter: int = 1

    @staticmethod
    def next_order_num() -> int:
        next_num = Order.order_counter
        Order.order_counter += 1

        return next_num

    def __init__(self, table: str, num=None, date=None):
        self._table: str = table
        self._products: list[Product] = []
        self._product_counter: int = 0

        if num is not None:
            self._num: int = num
        else:
            self._num: int = Order.next_order_num()

        if date is not None:
            self._date: datetime = date
        else:
            self._date: datetime = datetime.now()

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
        if timediff > timedelta(minutes=10):
            return ">10min"

        seconds_aligned = timediff.seconds // 5 * 5  # align by 5 seconds (easy way to circumvent javascript timers)
        seconds = str(seconds_aligned % 60).rjust(2, '0')
        minutes = str(seconds_aligned // 60).rjust(2, '0')

        return f"{minutes}:{seconds}"

    def add_products(self, *products: Product):
        for product in products:
            self._products.append(product)
            self._product_counter += 1

    def copy_empty(self) -> Order:
        return Order(self._table, self._num)


orders: list[Order] = []
#completed_orders: List[Order] = []


def add_order(order: Order) -> None:
    """Add order to orders list"""
    orders.append(order)


def complete_order(order: Order) -> None:
    # completed_orders.append(completed_order)
    orders.remove(order)
    log_info(f"Completed order {str(order.num)}")


def handle_order_completed_event(completed_data: str) -> None:
    if not completed_data.isdigit():
        log_error("POST in /bar but filetype not convertible to integer")
        return

    order: Union[Order, None] = next((o for o in orders if int(request.form["order-completed"]) == o.num), None)

    if order is None:
        log_error("POST in /bar but no matching Order to complete")
        return

    complete_order(order)
# endregion orders


# region tables
tables_x: str = config_data["tables"][0]
tables_y: str = config_data["tables"][1]
tables: list[str] = [f"{x}{y}" for x in tables_x for y in tables_y]  # tables 1A-9F
# endregion tables


# region flask
app: Flask = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bar")
def bar():
    return render_template("bar.html", orders=orders)


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
                           orders=[[f"{p.amount}x {p.name}" +
                                    (f" ({p.comment})" if p.comment else "")
                                    for p in o.products if not p.completed]
                                   for o in orders if o.table == table],
                           template_products=[(p, template_products[p][0], template_products[p][1]) for p in template_products])


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    if table not in tables:
        log_error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    new_order = Order(table)

    for template_product in range(1, num_template_products + 1):
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
            product = Product(template_product, amount, comment)
            new_order.add_products(product)

    if not new_order.products:
        log_warn("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        add_order(new_order)

    return redirect(url_for("service"))
# endregion flask


if __name__ == "__main__":
    # for production run
    # gunicorn --bind 0.0.0.0:5000 app:app
    #
    app.run()
