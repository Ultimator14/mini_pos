#!/usr/bin/python3.11

import logging
import os.path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .log import init_logging

db = SQLAlchemy()


def create_app() -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object("mini_pos.settings.Config")

    db.init_app(app)

    init_logging(app)
    app.logger.setLevel(logging.DEBUG)  # set to debug to catch all messages, this is changed later in init_config

    with app.app_context():
        if not os.path.isfile(f"instance/{app.config['DATABASE_FILE']}"):
            app.logger.info("No database file found. Creating database.")
            db.create_all()

        # must be withing app context to make app work
        from . import routes
        from .config import init_config
        init_config()

    return app
