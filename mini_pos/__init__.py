#!/usr/bin/python3.11

import json
import os.path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]

CONFIG_FILE: str = "config.json"
DATABASE_FILE: str = "data.db"


class Config:
    debug: bool = False

    class Product:
        available: AvailableProductsT = {}
        category_map: dict[int, str] = {}

        @classmethod
        def set_options(cls, product):
            if (available_config := product.get("available")) is None:
                log_error_exit("prouct->available missing in config file")
            elif len(available_config) == 0:
                log_error_exit("config option product->available must be of length >0")
            else:
                cls.available = dict(enumerate([tuple(product) for product in available_config], start=1))

            if (categories_config := product.get("categories")) is None:
                log_error_exit("prouct->categories missing in config file")
            elif len(categories_config) == 0:
                log_error_exit("config option product->categories must be of length >0")
            else:
                cls.category_map = dict(categories_config)

    class Table:
        size: tuple[int, int]
        grid: TablesGridT = []
        names: list[str]

        @classmethod
        def populate_grid(cls, names) -> None:
            grid: TablesGridT = [[None for x in range(cls.size[0])] for y in range(cls.size[1])]

            # parse tables
            for x, y, xlen, ylen, name in names:
                if xlen < 1 or ylen < 1:
                    log_error_exit("Invalid config option. Table can't have length < 1")
                if x + xlen > cls.size[0] or y + ylen > cls.size[1]:
                    log_error_exit("Table can't be placed outside the grid")

                for i in range(y, y + ylen):
                    for j in range(x, x + xlen):
                        if grid[i][j] is not None:
                            log_warn(f"Duplicate table position {i!s}/{j!s}. Check your config")
                        grid[i][j] = (False, None, None, None)

                grid[y][x] = (True, xlen, ylen, name)

            cls.grid = grid

        @classmethod
        def set_options(cls, table) -> None:
            if (size_config := table.get("size")) is None:
                log_error_exit("table->size missing in config file")
            elif len(size_config) != 2:
                log_error_exit("config option table->size must be exactly of length 2")
            else:
                cls.size = tuple(size_config)  # type: ignore (size_config has len 2 at this point)

            if (names_config := table.get("names")) is None:
                log_error_exit("table->names missing in config file")
            elif len(names_config) == 0:
                log_error_exit("config option table->names must be of length >0")
            else:
                cls.names = [name for _, _, _, _, name in names_config]
                if len(set(cls.names)) != len(cls.names):
                    log_error_exit("Duplicate table name found. Tables names must be unique")
                cls.populate_grid(names_config)

    class UI:
        auto_close: bool = True
        show_completed: int = 5
        timeout_warn: int = 120
        timeout_crit: int = 600
        split_categories: bool = False
        show_category_names: bool = False

        @classmethod
        def set_options(cls, ui) -> None:
            cls.auto_close = ui.get("auto_close", cls.auto_close)
            cls.show_completed = ui.get("show_completed", cls.show_completed)  # zero = don't show
            cls.timeout_warn, cls.timeout_crit = ui.get("timeout", (cls.timeout_warn, cls.timeout_crit))
            cls.split_categories = ui.get("split_categories", cls.split_categories)
            cls.show_category_names = ui.get("show_category_names", cls.show_category_names)

    @classmethod
    def set_options(cls, config_data) -> None:
        cls.debug = config_data.get("debug", cls.debug)

        if (product := config_data.get("product")) is None:
            log_error_exit("product section missing in config file.")
        else:
            cls.Product.set_options(product)

        if (table := config_data.get("table")) is None:
            log_error_exit("table section missing in config file.")
        else:
            cls.Table.set_options(table)

        if (ui := config_data.get("ui")) is None:
            log_warn("ui section is missing in config file. Using defaults.")
        else:
            cls.UI.set_options(ui)


 # must be after Config class to avoid circular import
from .helpers import (
    log_debug,
    log_error,
    log_error_exit,
    log_info,
    log_warn,
)

app: Flask = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE}"
db = SQLAlchemy(app)
#app.register_blueprint(people, url_prefix='')


def load_config() -> None:
    log_info("Loading configuration...")
    with open("config.json", encoding="utf-8") as afile:
        try:
            config_data = json.load(afile)
            Config.set_options(config_data)
        except json.decoder.JSONDecodeError as e:
            log_error_exit(f"Broken configuration file: {repr(e)!s}")


if not os.path.isfile(CONFIG_FILE):
    log_error_exit("No config file found. Abort execution")
load_config()  # must be after class and function definitions to prevent type error

if not os.path.isfile(f"instance/{DATABASE_FILE}"):
    log_info("No database file found. Creating database.")
    with app.app_context():
        db.create_all()

from .routes import *

if __name__ == "__main__":
    app.run()
