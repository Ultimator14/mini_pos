from flask import Blueprint, jsonify, render_template
from flask import current_app as app

from mini_pos.models import Order

fetch_bp = Blueprint("fetch", __name__, template_folder="templates")


@fetch_bp.route("/bar/<name>", strict_slashes=False)
def fetch_bar(name: str):
    app.logger.debug("GET /fetch/bar/<name>")

    if name == "default" and app.config["minipos"].ui.bar.default:
        # display default bar
        return render_template(
            "bar_body.html",
            orders=Order.get_open_orders(),
            completed_orders=Order.get_last_completed_orders(),
            show_completed=bool(app.config["minipos"].ui.bar.show_completed),
            bar=name,
        )

    # Try to display another bar
    bar_categories = app.config["minipos"].bars.get(name)

    if bar_categories is None:
        app.logger.error("GET in /bar/%s with invalid bar. Using default bar. Skipping...", name)
        return "Error! Bar not found"

    return render_template(
        "bar_body.html",
        orders=Order.get_open_orders_by_categories(bar_categories),
        completed_orders=Order.get_last_completed_orders_by_categories(bar_categories),
        show_completed=bool(app.config["minipos"].ui.bar.show_completed),
        bar=name,
    )


@fetch_bp.route("/service", strict_slashes=False)
def fetch_service():
    app.logger.debug("GET /fetch/service")
    return jsonify(Order.get_active_tables())
