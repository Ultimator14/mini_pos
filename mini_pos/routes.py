#!/usr/bin/python3.11

from random import randint

from flask import jsonify, redirect, render_template, request, url_for

from . import Config, app, db
from .models import Order, Product
from .helpers import log_debug, log_info, log_warn, log_error
from .query import (
    get_active_tables,
    get_last_completed_orders,
    get_open_order_nonces,
    get_open_orders,
    get_open_product_lists_by_table,
    get_open_products_by_order_id,
    get_order_by_id,
    get_product_by_id,
)


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

    if Config.UI.auto_close and len(get_open_products_by_order_id(order.id)) == 0:
        log_info("Last Product completed. Attempting auto_close")
        order.complete()


def handle_order_completed_event(order_id: int) -> None:
    order = get_order_by_id(order_id)

    if order is None:
        log_error("POST in /bar but no matching Order to complete")
        return

    order.complete()


@app.route("/")
def home():
    log_debug("GET /")
    return render_template("index.html")


@app.route("/bar", strict_slashes=False)
def bar():
    log_debug("GET /bar")
    return render_template(
        "bar.html",
        orders=get_open_orders(),
        completed_orders=get_last_completed_orders(),
        show_completed=bool(Config.UI.show_completed),
    )


@app.route("/fetch/bar", strict_slashes=False)
def fetch_bar():
    log_debug("GET /fetch/bar")
    return render_template(
        "bar_body.html",
        orders=get_open_orders(),
        completed_orders=get_last_completed_orders(),
        show_completed=bool(Config.UI.show_completed),
    )


@app.route("/bar", methods=["POST"])
def bar_submit():
    log_debug("POST /bar")
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
    log_debug("GET /service")
    return render_template(
        "service.html",
        tables_size=Config.Table.size,
        tables_grid=Config.Table.grid,
        active_tables=get_active_tables(),
    )


@app.route("/fetch/service", strict_slashes=False)
def fetch_service():
    log_debug("GET /fetch/service")
    return jsonify(get_active_tables())


@app.route("/service/<table>")
def service_table(table):
    log_debug("GET /service/<table>")
    if table not in Config.Table.names:
        log_error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    # Generate random number per order to prevent duplicate orders
    nonce = randint(0, 2**32 - 1)  # 32 bit random number

    return render_template(
        "service_table.html",
        table=table,
        open_product_lists=get_open_product_lists_by_table(table),
        available_products=[(p, pval[0], pval[1], pval[2]) for p, pval in Config.Product.available.items()],
        category_map=Config.Product.category_map,
        split_categories=Config.UI.split_categories,
        show_category_names=Config.UI.show_category_names,
        split_categories_init=Config.Product.available[1][2] if len(Config.Product.available) > 0 else 0,
        nonce=nonce,
    )


@app.route("/service/<table>", methods=["POST"])
def service_table_submit(table):
    log_debug("POST /service/<table>")
    if table not in Config.Table.names:
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

    for available_product in range(1, len(Config.Product.available) + 1):
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
            name, price, _ = Config.Product.available[available_product]
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
