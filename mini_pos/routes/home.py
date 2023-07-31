from flask import Blueprint, render_template
from flask import current_app as app

home_bp = Blueprint("home", __name__, template_folder="templates")


@home_bp.route("/")
def home():
    app.logger.debug("GET /")
    return render_template("index.html")
