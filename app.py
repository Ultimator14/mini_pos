#!/usr/bin/python3.11

from __future__ import annotations  # required for type hinting of classes in itself

import json
import os.path
import sys
from datetime import datetime, timedelta
from random import randint
from typing import NoReturn

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]

CONFIG_FILE: str = "config.json"
DATABASE_FILE: str = "data.db"

tables_size: tuple[int, int]
tables_grid: TablesGridT = []
tables: list[str]
available_products: AvailableProductsT = {}
category_map: dict[int, str] = {}


class Config:
    auto_close: bool = True
    show_completed: int = 5
    timeout_warn: int = 120
    timeout_crit: int = 600
    split_categories: bool = False
    show_category_names: bool = False


    @classmethod
    def set_options(cls, config_data) -> None:
        ui = config_data.get("ui")

        if ui is None:
            log_warn("ui section is missing in config file. Using defaults.")
            return

        cls.auto_close = ui.get("auto_close", cls.auto_close)
        cls.show_completed = ui.get("show_completed", cls.show_completed)  # zero = don't show
        cls.timeout_warn, cls.timeout_crit = ui.get("timeout", (cls.timeout_warn, cls.timeout_crit))
        cls.split_categories = ui.get("split_categories", cls.split_categories)
        cls.show_category_names = ui.get("show_category_names", cls.show_category_names)


app: Flask = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE}"
db = SQLAlchemy(app)


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

def log_error_exit(msg: str) -> NoReturn:
    log_error(msg)
    sys.exit(1)


def load_config() -> None:
    log_info("Loading configuration...")
    with open("config.json", encoding="utf-8") as afile:
        config_data = json.load(afile)

        Config.set_options(config_data)

        global tables_size, tables_grid, tables
        tables_size = tuple(config_data["table"]["size"])

        # parse tables
        grid: TablesGridT = [[None for x in range(tables_size[0])] for y in range(tables_size[1])]

        for x, y, xlen, ylen, name in config_data["table"]["names"]:
            if xlen < 1 or ylen < 1:
                log_error_exit("Invalid config option. Table can't have length < 1")
            if x + xlen > tables_size[0] or y + ylen > tables_size[1]:
                log_error_exit("Table can't be placed outside the grid")

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        log_warn(f"Duplicate table position {i!s}/{j!s}. Check your config")
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        tables_grid = grid

        tables = [name for _, _, _, _, name in config_data["table"]["names"]]

        if len(set(tables)) != len(tables):
            log_error_exit("Duplicate table name found. Tables names must be unique")

        global available_products, category_map
        available_products = dict(
            enumerate([tuple(product) for product in config_data["product"]["available"]], start=1)
        )
        category_map = dict(config_data["product"]["categories"])


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.Integer)
    table = db.Column(db.String)
    date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    @classmethod
    def create(cls, table: str, nonce: int) -> Order:
        return cls(table=table, nonce=nonce, date=datetime.now(), completed_at=None)

    @property
    def products(self) -> list[Product]:
        return list(db.session.execute(db.select(Product).filter_by(order_id=self.id)).scalars())

    @property
    def active_since(self) -> str:
        timediff = datetime.now() - self.date
        if timediff > timedelta(minutes=60):
            return ">60min"

        seconds_aligned = timediff.seconds // 5 * 5  # align by 5 seconds (easy way to circumvent javascript timers)
        seconds = str(seconds_aligned % 60).rjust(2, "0")
        minutes = str(seconds_aligned // 60).rjust(2, "0")

        return f"{minutes}:{seconds}"

    @property
    def active_since_timeout_class(self) -> str:
        timediff = datetime.now() - self.date
        if timediff > timedelta(seconds=Config.timeout_crit):
            return "timeout_crit"
        if timediff > timedelta(seconds=Config.timeout_warn):
            return "timeout_warn"
        return "timeout_ok"

    @property
    def completed_timestamp(self) -> str:
        if self.completed_at is None:
            log_warn(f"completed_at for order {self.id!s} called but order is not completed")
            return " "

        return self.completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def complete(self) -> None:
        products = db.session.execute(db.select(Product).filter_by(order_id=self.id,completed=False)).scalars()
        for product in products:
            product.complete()

        self.completed_at = datetime.now()

        db.session.commit()

        log_info(f"Completed order {self.id!s}")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(Order.id))
    name = db.Column(db.String)
    price = db.Column(db.Float)
    amount = db.Column(db.Integer)
    comment = db.Column(db.String)
    completed = db.Column(db.Boolean)

    @classmethod
    def create(cls, order_id: int, name: str, price: float, amount: int, comment="") -> Product:
        return cls(order_id=order_id, name=name, price=price, amount=amount, comment=comment, completed=False)

    def complete(self) -> None:
        if not self.completed:
            self.completed = True
            db.session.commit()
            log_info(f"Completed product {self.id!s}")


def get_open_orders() -> list[Order]:
    return list(db.session.execute(db.select(Order).filter_by(completed_at=None)).scalars())

def get_order_by_id(order_id: int) -> Order | None:
    return db.session.execute(db.select(Order).filter_by(id=order_id)).scalar_one_or_none()


def get_open_orders_by_table(table: str) -> list[Order]:
    return list(db.session.execute(db.select(Order).filter_by(table=table, completed_at=None)).scalars())


def get_open_order_nonces() -> list[int]:
    return list(db.session.execute(db.select(Order.nonce).filter_by(completed_at=None)).scalars())


def get_active_tables() -> list[str]:
    return list(db.session.execute(db.select(Order.table).filter_by(completed_at=None).distinct()).scalars())


def get_last_completed_orders() -> list[Order]:
    return list(db.session.execute(
        db.select(Order)
        .filter(Order.completed_at != None)  # this must be != and not 'is not'
        .order_by(Order.completed_at.desc())
        .limit(Config.show_completed)
    ).scalars())


def get_product_by_id(product_id: int) -> Product | None:
    return db.session.execute(db.select(Product).filter_by(id=product_id)).scalar_one_or_none()


def get_open_products_by_order_id(order_id: int) -> list[Product]:
    return list(db.session.execute(db.select(Product).filter_by(completed=False, order_id=order_id)).scalars())


def get_open_product_lists_by_table(table: str) -> list[list[str]]:
    return [
        [
            f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "")
            for p in get_open_products_by_order_id(o.id)
        ]
        for o in get_open_orders_by_table(table)
    ]


def handle_product_completed_event(product_id: int, order_id: int) -> None:
    order = get_order_by_id(order_id)

    if order is None:
        log_error("POST in /bar but no matching Order found")
        return

    product = get_product_by_id(product_id)

    if product is None:
        log_error("POST in /bar but no matching Product for order found")
        return

    product.complete()

    if Config.auto_close and len(get_open_products_by_order_id(order.id)) == 0:
        log_info("Last Product completed. Attempting auto_close")
        order.complete()


def handle_order_completed_event(order_id: int) -> None:
    order = get_order_by_id(order_id)

    if order is None:
        log_error("POST in /bar but no matching Order to complete")
        return

    order.complete()


if not os.path.isfile(CONFIG_FILE):
    log_error_exit("No config file found. Abort execution")
load_config()  # must be after class and function definitions to prevent type error

if not os.path.isfile(f"instance/{DATABASE_FILE}"):
    log_info("No database file found. Creating database.")
    with app.app_context():
        db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bar", strict_slashes=False)
def bar():
    return render_template(
        "bar.html",
        orders=get_open_orders(),
        completed_orders=get_last_completed_orders(),
        show_completed=bool(Config.show_completed),
    )


@app.route("/fetch/bar", strict_slashes=False)
def fetch_bar():
    return render_template(
        "bar_body.html",
        orders=get_open_orders(),
        completed_orders=get_last_completed_orders(),
        show_completed=bool(Config.show_completed),
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
            if (
                not (product_id := request.form["product-completed"]).isdigit()
                or not (order_id := request.form["order"]).isdigit()
            ):
                log_error("POST in /bar but filetype not convertible to integer")
            else:
                handle_product_completed_event(int(product_id), int(order_id))
        else:
            log_error("POST in /bar but missing order data for completed product")

    else:
        log_error("POST in /bar but neither order nor product specified")

    return redirect(url_for("bar"))


@app.route("/service", strict_slashes=False)
def service():
    return render_template(
        "service.html",
        tables_size=tables_size,
        tables_grid=tables_grid,
        active_tables=get_active_tables(),
    )


@app.route("/fetch/service", strict_slashes=False)
def fetch_service():
    active_tables = get_active_tables()

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
        open_product_lists=get_open_product_lists_by_table(table),
        available_products=[(p, pval[0], pval[1], pval[2]) for p, pval in available_products.items()],
        category_map=category_map,
        split_categories=Config.split_categories,
        show_category_names=Config.show_category_names,
        split_categories_init=available_products[1][2] if len(available_products) > 0 else 0,
        nonce=nonce,
    )


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    if table not in tables:
        log_error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    if "nonce" not in request.form:
        log_error("POST in /service/<table> but missing nonce. Skipping...")
        return "Error! Missing nonce"

    if not (nonce := request.form["nonce"]).isdigit():
        log_error("POST in /service/<table> but nonce not convertible to integer. Skipping...")
        return "Error! Nonce is not int"

    if int(nonce) in get_open_order_nonces():
        log_warn(f"Catched duplicate order by nonce {nonce}")
        return redirect(url_for("service"))

    new_order = Order.create(table, nonce)
    db.session.add(new_order)
    db.session.flush()  # enforce creation of id, required to assign order_id to product
    product_added = False

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
            product = Product.create(new_order.id, name, price, amount, comment)
            db.session.add(product)
            db.session.flush()  # enforce creation of id, required for log
            product_added = True
            log_info(f"Queued product {product.id!s} for order {new_order.id!s}")

    if not product_added:
        log_warn("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        db.session.commit()
        log_info(f"Added order {new_order.id!s}")

    return redirect(url_for("service"))


if __name__ == "__main__":
    # for production run
    # sysctl -w net.ipv4.ip_unprivileged_port_start=80
    # gunicorn --bind 0.0.0.0:80 --workers=4 app:app
    # sysctl -w net.ipv4.ip_unprivileged_port_start=1024
    #
    app.run()
