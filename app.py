#!/usr/bin/python3.10

# region includes
import json
from flask import Flask, render_template, request, redirect, url_for
from typing import List
# endregion includes

# region config
CONFIG_FILE = "config.json"

config_file = open("config.json", "r")
config_data = json.load(config_file)
config_file.close()
# endregion config


# region helper

# endregion helper


# region products
template_products = dict(enumerate(config_data["products"], start=1))
num_template_products = len(template_products)


class Product:
    product_counter = 1

    @staticmethod
    def next_product_num():
        next_num = Product.product_counter
        Product.product_counter += 1

        return next_num

    def __init__(self, template_product, amount, comment="", num=None):
        if num:
            self._num = num
        else:
            self._num = Product.next_product_num()

        self._template_product = template_product
        self._amount = amount
        self._comment = comment

        self._completed = False

    @property
    def num(self):
        return self._num

    @property
    def name(self):
        if self._template_product != 0:
            return template_products[self._template_product][0]
        else:
            return "Invalid"

    @property
    def amount(self):
        return self._amount

    @property
    def comment(self):
        return self._comment

    @property
    def completed(self):
        return self._completed

    def complete(self):
        self._completed = True
# endregion products


# region orders
class Order:
    order_counter = 1

    @staticmethod
    def next_order_num():
        next_num = Order.order_counter
        Order.order_counter += 1

        return next_num

    def __init__(self, table, num=None):
        self._table = table
        self._products: List[Product] = []
        self._product_counter = 0
        if num:
            self._num = num
        else:
            self._num = Order.next_order_num()

    @property
    def num(self):
        return self._num

    @property
    def table(self):
        return self._table

    @property
    def products(self):
        return self._products

    def add_products(self, *products: Product):
        for product in products:
            self._products.append(product)
            self._product_counter += 1

    def copy_empty(self):
        return Order(self._table, self._num)


orders: List[Order] = []
#completed_orders: List[Order] = []


def add_order(order: Order):
    """Add order to orders list"""
    orders.append(order)
# endregion orders


# region tables
tables_x = config_data["tables"][0]
tables_y = config_data["tables"][1]
tables = [f"{x}{y}" for x in tables_x for y in tables_y]  # tables 1A-9F
# endregion tables


# region flask
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bar")
def bar():
    return render_template("bar.html", orders=orders)


@app.route("/bar", methods=["POST"])
def bar_submit():
    if "completed" in request.form:
        if not request.form["completed"].isdigit():
            print("Warning! POST request in /bar with filetype not convertible to integer")
        else:
            completed_order = next((order for order in orders if int(request.form["completed"]) == order.num), None)

            if completed_order is None:
                print("Warning! POST complete request in /bar but no matching Order found")
            else:
                # completed_orders.append(completed_order)
                orders.remove(completed_order)
                print(f"Removed order {str(completed_order.num)}")
    elif "product-completed" in request.form:
        if "order" not in request.form:
            print("Warning! POST request in /bar but missing order for completed product")
        if not request.form["product-completed"].isdigit() or not request.form["order"].isdigit():
            print("Warning! POST request in /bar with filetype not convertible to integer")
        else:
            order = next((order for order in orders if int(request.form["order"]) == order.num), None)

            if order is None:
                print("Warning! POST complete request in /bar but no matching Order found")
            else:
                product = next((p for p in order.products if int(request.form["product-completed"]) == p.num), None)

                if product is None:
                    print("Warning! POST complete request in /bar but no matching Product for order found")
                else:
                    product.complete()
                    print(f"Completed product {str(product.num)}")
                    if all([p.completed for p in order.products]):
                        # completed_orders.append(completed_order)
                        orders.remove(order)
                        print(f"Removed order {str(order.num)}")

    else:
        # somehow a post request occured but the request did not contain a completed event
        # this should not happen
        print("Warning! POST request in /bar but missing completed event")

    return redirect(url_for("bar"))


@app.route("/service")
def service():
    return render_template("service.html", tables_x=tables_x, tables_y=tables_y,
                           active_tables={order.table for order in orders})


@app.route("/service/<table>")
def service_table(table):
    if table not in tables:
        print("Warning! Get request in /service/<table> but matching table not found")
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
        print(f"Error! POST request in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    new_order = Order(table)

    for template_product in range(1, num_template_products + 1):
        if f"amount-{template_product}" not in request.form:
            print(f"Warning! POST request in /service/<table> but missing amount-{template_product} event. Skipping...")
            continue
        if not request.form[f"amount-{template_product}"].isdigit():
            print("Warning! POST request in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(request.form[f"amount-{template_product}"])

        if f"comment-{template_product}" not in request.form:
            print(f"Warning! POST request in /service/<table> but missing comment-{template_product} event")
            comment = ""
        else:
            comment = request.form[f"comment-{template_product}"]

        if amount > 0:
            product = Product(template_product, amount, comment)
            new_order.add_products(product)

    if not new_order.products:
        print(f"Warning! POST request in /service/<table> but order does not contain any product. Skipping...")
    else:
        add_order(new_order)

    return redirect(url_for("service"))
# endregion flask


if __name__ == "__main__":
    # for production run
    # gunicorn --bind 0.0.0.0:5000 app:app
    #
    app.run()
