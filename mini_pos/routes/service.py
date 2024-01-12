from random import randint

from flask import Blueprint, make_response, redirect, render_template, request, url_for
from flask import current_app as app

from mini_pos.models import Order, Product, db

service_bp = Blueprint("service", __name__, template_folder="templates")


@service_bp.route("/", strict_slashes=False)
def service():
    app.logger.debug("GET /service")

    return render_template(
        "service.html",
        tables_size=app.config["minipos"].table.size,
        tables_grid=app.config["minipos"].table.grid,
        active_tables=Order.get_active_tables(),
    )


@service_bp.route("/trylogin", strict_slashes=False)
def service_trylogin():
    if "waiter" not in request.cookies:
        return redirect(url_for("service.service_login"))

    return redirect(url_for("service.service"))


@service_bp.route("/login", strict_slashes=False)
def service_login():
    waiter = request.cookies.get("waiter", "")
    return render_template("service_login.html", waiter=waiter)


@service_bp.route("/login", methods=["POST"], strict_slashes=False)
def service_login_submit():
    waiter = request.form.get("waiter")

    if waiter is None:
        app.logger.error("POST in /service/login but missing waiter name. Skipping...")
        return "Error! Missing waiter name"

    response = make_response(render_template("service_login.html", waiter=waiter))
    response.set_cookie("waiter", waiter, max_age=60 * 60 * 24 * 7)  # 1 week
    return response


@service_bp.route("/<table>", strict_slashes=False)
def service_table(table):
    app.logger.debug("GET /service/<table>")
    if table not in app.config["minipos"].table.names:
        app.logger.error("GET in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    # Generate random number per order to prevent duplicate orders
    nonce = randint(0, 2**32 - 1)  # 32 bit random number

    return render_template(
        "service_table.html",
        table=table,
        open_product_lists=Product.get_open_product_lists_by_table(table),
        available_products=[
            (p, pval[0], pval[1], pval[2]) for p, pval in app.config["minipos"].product.available.items()
        ],
        category_map=app.config["minipos"].product.category_map,
        split_categories=app.config["minipos"].ui.split_categories,
        show_category_names=app.config["minipos"].ui.show_category_names,
        split_categories_init=app.config["minipos"].product.available[1][2]
        if len(app.config["minipos"].product.available) > 0
        else 0,
        nonce=nonce,
    )


@service_bp.route("/<table>", methods=["POST"], strict_slashes=False)
def service_table_submit(table):
    app.logger.debug("POST /service/<table>")
    if table not in app.config["minipos"].table.names:
        app.logger.error("POST in /service/<table> but invalid table. Skipping...")
        return "Error! Invalid table"

    nonce = request.form.get("nonce")

    if nonce is None:
        app.logger.error("POST in /service/<table> but missing nonce. Skipping...")
        return "Error! Missing nonce"

    if not nonce.isdigit():
        app.logger.error("POST in /service/<table> but nonce not convertible to integer. Skipping...")
        return "Error! Nonce is not int"

    if int(nonce) in Order.get_open_order_nonces():
        app.logger.warning("Catched duplicate order by nonce %s", nonce)
        return redirect(url_for("service.service"))

    waiter = request.cookies.get("waiter", "")
    new_order = Order.create(waiter, table, nonce)
    db.session.add(new_order)
    db.session.flush()  # enforce creation of id, required to assign order_id to product
    product_added = False

    for available_product in range(1, len(app.config["minipos"].product.available) + 1):
        amount_param = request.form.get(f"amount-{available_product}")

        if amount_param is None:
            app.logger.warning("POST in /service/<table> but missing amount-%s event. Skipping...", available_product)
            continue

        if not amount_param.isdigit():
            app.logger.warning("POST in /service/<table> with filetype not convertible to integer. Skipping...")
            continue

        amount = int(amount_param)

        comment = request.form.get(f"comment-{available_product}")

        if comment is None:
            app.logger.warning("POST in /service/<table> but missing comment-%s event", available_product)
            comment = ""

        if amount > 0:
            name, price, _ = app.config["minipos"].product.available[available_product]
            product = Product.create(new_order.id, name, price, amount, comment)
            db.session.add(product)
            db.session.flush()  # enforce creation of id, required for log
            product_added = True
            app.logger.info("Queued product %s for order %s", product.id, new_order.id)

    if not product_added:
        app.logger.warning("POST in /service/<table> but order does not contain any product. Skipping...")
    else:
        db.session.commit()
        app.logger.info("Added order %s", new_order.id)

    return redirect(url_for("service.service"))
