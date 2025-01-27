from flask import Blueprint, jsonify, render_template
from flask import current_app as app

from mini_pos.models import Order

fetch_bp = Blueprint("fetch", __name__, template_folder="templates")


@fetch_bp.route("/bar", strict_slashes=False)
def fetch_bar():
    app.logger.debug("GET /fetch/bar")
    return render_template(
        "bar_body.html",
        orders=Order.get_open_orders(),
        completed_orders=Order.get_last_completed_orders(),
        show_completed=bool(app.config["minipos"].ui.bar.show_completed),
    )


@fetch_bp.route("/service", strict_slashes=False)
def fetch_service():
    app.logger.debug("GET /fetch/service")
    return jsonify(Order.get_active_tables())
