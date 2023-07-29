#!/usr/bin/python3.11

import logging

from flask.logging import default_handler


class CustomFormatter(logging.Formatter):
    cyan = "\033[36;1m"  # ]]
    green = "\033[32;1m"  # ]]
    yellow = "\033[33;1m"  # ]]
    red = "\033[31;1m"  # ]]
    reset = "\033[0m"  # ]]

    format_str = "*** %(levelname)s *** %(message)s"

    FORMATS: dict = {
        logging.DEBUG: cyan + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: red + format_str + reset,
    }

    def format(self, record) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def init_logging(app) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    handler.setLevel(logging.DEBUG)

    app.logger.addHandler(handler)
    app.logger.removeHandler(default_handler)
