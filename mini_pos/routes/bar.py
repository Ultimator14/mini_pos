from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app as app

from mini_pos.models import Order, Product

bar_bp = Blueprint("bar", __name__, template_folder="templates")


@bar_bp.route("/", strict_slashes=False)
def bar_selection():
    app.logger.debug("GET /bar")

    # If there is only one bar including the default one (if present) we can directly show it
    bars = app.config["minipos"].bars.copy()

    if len(bars) == 1:
        # display the only bar
        return redirect(url_for("bar.bar_name", bar=bars.keys()[0]))

    return render_template("bar_selection.html", bars=bars)


@bar_bp.route("/<bar>", strict_slashes=False)
def bar_name(bar: str):
    app.logger.debug("GET /bar/<bar>")

    if app.config["minipos"].bars.get(bar) is None:
        app.logger.error("GET in /bar/%s with invalid bar. Using default bar. Skipping...", bar)
        return "Error! Bar not found"

    return render_template(
        "bar.html",
        orders=Order.get_open_orders_for_bar(bar),
        partially_completed_orders=Order.get_partially_completed_order_for_bar(bar),
        completed_orders=Order.get_last_completed_orders_for_bar(bar),
        show_completed=bool(app.config["minipos"].ui.bar.show_completed),
        bar=bar,
    )

@bar_bp.route("/<bar>/history", strict_slashes=False)
def bar_history(bar: str):
    app.logger.debug("GET /bar/<bar>/history")

    if app.config["minipos"].bars.get(bar) is None:
        app.logger.error("GET in /bar/%s with invalid bar. Using default bar. Skipping...", bar)
        return "Error! Bar not found"

    return render_template(
        "bar_history.html",
        completed_orders=Order.get_all_completed_orders_for_bar(bar),
        bar=bar
    )

@bar_bp.route("/<bar>", methods=["POST"], strict_slashes=False)
def bar_submit(bar: str):
    app.logger.debug("POST /bar/<bar>")

    order_id = request.form.get("order-completed")
    product_id = request.form.get("product-completed")

    if order_id is not None and product_id is not None:
        app.logger.info("POST in /bar with order and product completion data. Using order...")

    if order_id is not None:
        if not order_id.isdigit():
            app.logger.error("POST in /bar but filetype not convertible to integer")
        else:
            handle_order_completed_event(int(order_id), bar)

    elif product_id is not None:
        if not product_id.isdigit():
            app.logger.error("POST in /bar but filetype not convertible to integer")
        else:
            handle_product_completed_event(int(product_id))

    else:
        app.logger.error("POST in /bar but neither order nor product specified")

    return redirect(url_for("bar.bar_name", bar=bar))


def handle_order_completed_event(order_id: int, bar: str) -> None:
    order = Order.get_order_by_id(order_id)

    if order is None:
        app.logger.error("POST in /bar but no matching order to complete")
        return

    order.complete_for_bar(bar)


def handle_product_completed_event(product_id: int) -> None:
    product = Product.get_product_by_id(product_id)

    if product is None:
        app.logger.error("POST in /bar but no matching product found")
        return

    product.complete()
    order_id = product.order_id

    if app.config["minipos"].ui.bar.auto_close and len(Product.get_open_products_by_order_id(order_id)) == 0:
        # Since orders are filtered for different bars, we only have to check the case that an order is really
        # closed, not that it is partially closed by one bar only
        app.logger.info("Last Product completed. Attempting auto_close")

        if (order := Order.get_order_by_id(order_id)) is None:
            app.logger.error("POST in /bar but no matching order for product found")
            return

        order.complete()
