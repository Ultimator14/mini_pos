import logging

from flask import Flask

from .config import init_config
from .log import init_logging
from .models import init_db
from .routes import register_blueprints


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    # initialize logging first because other modules depend on it
    # set level to debug to catch all messages, this is changed later in init_config
    init_logging(app)
    app.logger.setLevel(logging.DEBUG)

    with app.app_context():
        # configure app
        app.config.from_object("mini_pos.settings.Config")

        init_config(app)

        # initialize db after configuration
        init_db(app)

        # Add routes
        register_blueprints(app)

    return app
