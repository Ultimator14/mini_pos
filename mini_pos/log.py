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


class LogCount(logging.Handler):
    """Counts critical logs. Counter is reset on access."""
    def __init__(self):
        super().__init__()
        self._count = 0

    @property
    def count(self):
        count = self._count
        self._count = 0
        return count

    def emit(self, record):
        self._count += 1


def init_logging(app) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    handler.setLevel(logging.DEBUG)
    handler.name = "StreamHandler"

    counter = LogCount()
    counter.setLevel(logging.CRITICAL)
    counter.name = "CritLogCountHandler"

    app.logger.removeHandler(default_handler)
    app.logger.addHandler(handler)
    app.logger.addHandler(counter)
