from flask import Blueprint, jsonify, render_template
from flask import current_app as app

from mini_pos.models import Order

fetch_bp = Blueprint("fetch", __name__, template_folder="templates")


@fetch_bp.route("/bar/<bar>", strict_slashes=False)
def fetch_bar(bar: str):
    app.logger.debug("GET /fetch/bar/<bar>")

    if app.config["minipos"].bars.get(bar) is None:
        app.logger.error("GET in /bar/%s with invalid bar. Using default bar. Skipping...", bar)
        return "Error! Bar not found"

    return render_template(
        "bar_body.html",
        orders=Order.get_open_orders_for_bar(bar),
        partially_completed_orders=Order.get_partially_completed_order_for_bar(bar),
        completed_orders=Order.get_last_completed_orders_for_bar(bar),
        show_completed=bool(app.config["minipos"].ui.bar.show_completed),
        bar=bar,
    )


@fetch_bp.route("/service", strict_slashes=False)
def fetch_service():
    app.logger.debug("GET /fetch/service")
    return jsonify(Order.get_active_tables())
