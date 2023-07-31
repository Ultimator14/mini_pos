from .bar import bar_bp
from .fetch import fetch_bp
from .home import home_bp
from .service import service_bp


def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(bar_bp, url_prefix="/bar")
    app.register_blueprint(service_bp, url_prefix="/service")
    app.register_blueprint(fetch_bp, url_prefix="/fetch")
