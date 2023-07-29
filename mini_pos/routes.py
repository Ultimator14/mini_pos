#!/usr/bin/python3.11

from random import randint

from flask import current_app as app
from flask import jsonify, redirect, render_template, request, url_for

from . import Config, db
from .models import Order, Product


def handle_product_completed_event(product_id: int, order_id: int) -> None:
    order = Order.get_order_by_id(order_id)

    if order is None:
        app.logger.error("POST in /bar but no matching Order found")
        return

    product = Product.get_product_by_id(product_id)

    if product is None:
        app.logger.error("POST in /bar but no matching Product for order found")
        return

    product.complete()

    if Config.UI.auto_close and len(Product.get_open_products_by_order_id(order.id)) == 0:
        app.logger.info("Last Product completed. Attempting auto_close")
        order.complete()


def handle_order_completed_event(order_id: int) -> None:
    order = Order.get_order_by_id(order_id)

    if order is None:
        app.logger.error("POST in /bar but no matching Order to complete")
        return

    order.complete()


@app.route("/")
def home():
    app.logger.debug("GET /")
    return render_template("index.html")


@app.route("/bar", strict_slashes=False)
def bar():
    app.logger.debug("GET /bar")
    return render_template(
        "bar.html",
        orders=Order.get_open_orders(),
        completed_orders=Order.get_last_completed_orders(),
        show_completed=bool(Config.UI.show_completed),
    )


@app.route("/fetch/bar", strict_slashes=False)
def fetch_bar():
    app.logger.debug("GET /fetch/bar")
    return render_template(
        "bar_body.html",
        orders=Order.get_open_orders(),
        completed_orders=Order.get_last_completed_orders(),
        show_completed=bool(Config.UI.show_completed),
    )


@app.route("/bar", methods=["POST"])
def bar_submit():
    app.logger.debug("POST /bar")
    if "order-completed" in request.form and "product-completed" in request.form:
        app.logger.info("POST in /bar with order and product completion data. Using order...")

    if "order-completed" in request.form:
        if not (order_id := request.form["order-completed"]).isdigit():
            app.logger.error("POST in /bar but filetype not convertible to integer")
        else:
            handle_order_completed_event(int(order_id))

    elif "product-completed" in request.form:
        if "order" in request.form:
            if (
                not (product_id := request.form["product-completed"]).isdigit()
                or not (order_id := request.form["order"]).isdigit()
            ):
                app.logger.error("POST in /bar but filetype not convertible to integer")
            else:
                handle_product_completed_event(int(product_id), int(order_id))
        else:
            app.logger.error("POST in /bar but missing order data for completed product")

    else:
        app.logger.error("POST in /bar but neither order nor product specified")

    return redirect(url_for("bar"))


@app.route("/service", strict_slashes=False)
def service():
    app.logger.debug("GET /service")
    return render_template(
        "service.html",
        tables_size=Config.Table.size,
        tables_grid=Config.Table.grid,
        active_tables=Order.get_active_tables(),
    )


@app.route("/fetch/service", strict_slashes=False)
def fetch_service():
    app.logger.debug("GET /fetch/service")
    return jsonify(Order.get_active_tables())


@app.route("/service/<table>")
def service_table(table):
    app.logger.debug("GET /service/<table>")
    if table not in Config.Table.names:
        app.logger.error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    # Generate random number per order to prevent duplicate orders
    nonce = randint(0, 2**32 - 1)  # 32 bit random number

    return render_template(
        "service_table.html",
        table=table,
        open_product_lists=Product.get_open_product_lists_by_table(table),
        available_products=[(p, pval[0], pval[1], pval[2]) for p, pval in Config.Product.available.items()],
        category_map=Config.Product.category_map,
        split_categories=Config.UI.split_categories,
        show_category_names=Config.UI.show_category_names,
        split_categories_init=Config.Product.available[1][2] if len(Config.Product.available) > 0 else 0,
        nonce=nonce,
    )


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    app.logger.debug("POST /service/<table>")
    if table not in Config.Table.names:
        app.logger.error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    if "nonce" not in request.form:
        app.logger.error("POST in /service/<table> but missing nonce. Skipping...")
        return "Error! Missing nonce"

    if not (nonce := request.form["nonce"]).isdigit():
        app.logger.error("POST in /service/<table> but nonce not convertible to integer. Skipping...")
        return "Error! Nonce is not int"

    if int(nonce) in Order.get_open_order_nonces():
        app.logger.warning(f"Catched duplicate order by nonce {nonce}")
        return redirect(url_for("service"))

    new_order = Order.create(table, nonce)
    db.session.add(new_order)
    db.session.flush()  # enforce creation of id, required to assign order_id to product
    product_added = False

    for available_product in range(1, len(Config.Product.available) + 1):
        if f"amount-{available_product}" not in request.form:
            app.logger.warning(f"POST in /service/<table> but missing amount-{available_product} event. Skipping...")
            continue

        if not (amount_param := request.form[f"amount-{available_product}"]).isdigit():
            app.logger.warning("POST in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(amount_param)

        if f"comment-{available_product}" not in request.form:
            app.logger.warning(f"POST in /service/<table> but missing comment-{available_product} event")
            comment = ""
        else:
            comment = request.form[f"comment-{available_product}"]

        if amount > 0:
            name, price, _ = Config.Product.available[available_product]
            product = Product.create(new_order.id, name, price, amount, comment)
            db.session.add(product)
            db.session.flush()  # enforce creation of id, required for log
            product_added = True
            app.logger.info(f"Queued product {product.id!s} for order {new_order.id!s}")

    if not product_added:
        app.logger.warning("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        db.session.commit()
        app.logger.info(f"Added order {new_order.id!s}")

    return redirect(url_for("service"))
