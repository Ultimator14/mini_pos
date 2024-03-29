from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app as app

from mini_pos.models import Order, Product

bar_bp = Blueprint("bar", __name__, template_folder="templates")


@bar_bp.route("/", strict_slashes=False)
def bar():
    app.logger.debug("GET /bar")
    return render_template(
        "bar.html",
        orders=Order.get_open_orders(),
        completed_orders=Order.get_last_completed_orders(),
        show_completed=bool(app.config["minipos"].ui.show_completed),
    )


@bar_bp.route("/", methods=["POST"], strict_slashes=False)
def bar_submit():
    app.logger.debug("POST /bar")

    order_id = request.form.get("order-completed")
    product_id = request.form.get("product-completed")

    if order_id is not None and product_id is not None:
        app.logger.info("POST in /bar with order and product completion data. Using order...")

    if order_id is not None:
        if not order_id.isdigit():
            app.logger.error("POST in /bar but filetype not convertible to integer")
        else:
            handle_order_completed_event(int(order_id))

    elif product_id is not None:
        if not product_id.isdigit():
            app.logger.error("POST in /bar but filetype not convertible to integer")
        else:
            handle_product_completed_event(int(product_id))

    else:
        app.logger.error("POST in /bar but neither order nor product specified")

    return redirect(url_for("bar.bar"))


def handle_order_completed_event(order_id: int) -> None:
    order = Order.get_order_by_id(order_id)

    if order is None:
        app.logger.error("POST in /bar but no matching order to complete")
        return

    order.complete()


def handle_product_completed_event(product_id: int) -> None:
    product = Product.get_product_by_id(product_id)

    if product is None:
        app.logger.error("POST in /bar but no matching product found")
        return

    product.complete()
    order_id = product.order_id

    if app.config["minipos"].ui.auto_close and len(Product.get_open_products_by_order_id(order_id)) == 0:
        app.logger.info("Last Product completed. Attempting auto_close")

        if (order := Order.get_order_by_id(order_id)) is None:
            app.logger.error("POST in /bar but no matching order for product found")
            return

        order.complete()
