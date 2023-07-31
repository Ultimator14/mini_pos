#!/usr/bin/python3.11

import logging
import os.path

from flask import Flask

from .config import init_config
from .log import init_logging
from .models import db
from .routes.bar import bar_bp
from .routes.fetch import fetch_bp
from .routes.home import home_bp
from .routes.service import service_bp


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    # initialize logging first because other modules depend on it
    # set level to debug to catch all messages, this is changed later in init_config
    init_logging(app)
    app.logger.setLevel(logging.DEBUG)

    with app.app_context():
        # configure app
        app.config.from_object("mini_pos.settings.Config")

        init_config()

        # initialize db after configuration
        db.init_app(app)

        if not os.path.isfile(f"instance/{app.config['DATABASE_FILE']}"):
            app.logger.info("No database file found. Creating database.")
            db.create_all()

        # Add routes
        app.register_blueprint(home_bp)
        app.register_blueprint(bar_bp)
        app.register_blueprint(service_bp)
        app.register_blueprint(fetch_bp)

    return app
