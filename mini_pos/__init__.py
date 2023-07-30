#!/usr/bin/python3.11

import logging
import os.path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .log import init_logging

db = SQLAlchemy()


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    # initialize logging first because other modules depend on it
    # set level to debug to catch all messages, this is changed later in init_config
    init_logging(app)
    app.logger.setLevel(logging.DEBUG)

    with app.app_context():
        # configure app
        app.config.from_object("mini_pos.settings.Config")
        from .config import init_config
        init_config()

        # initialize db after configuration
        from . import models
        db.init_app(app)

        if not os.path.isfile(f"instance/{app.config['DATABASE_FILE']}"):
            app.logger.info("No database file found. Creating database.")
            db.create_all()

        # Add routes
        from . import routes

    return app
