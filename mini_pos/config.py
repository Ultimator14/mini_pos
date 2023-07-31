#!/usr/bin/python3.11

import json
import logging
import os
import sys

from flask import current_app as app

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]


def log_error_exit(msg):
    app.logger.critical(msg)
    sys.exit(1)


class ProductConfig:
    def __init__(self):
        self.available: AvailableProductsT = {}
        self.category_map: dict[int, str] = {}

    def set_options(self, product):
        if (available_config := product.get("available")) is None:
            log_error_exit("prouct->available missing in config file")
        elif len(available_config) == 0:
            log_error_exit("config option product->available must be of length >0")
        else:
            self.available = dict(enumerate([tuple(product) for product in available_config], start=1))
        if (categories_config := product.get("categories")) is None:
            log_error_exit("prouct->categories missing in config file")
        elif len(categories_config) == 0:
            log_error_exit("config option product->categories must be of length >0")
        else:
            self.category_map = dict(categories_config)


class TableConfig:
    def __init__(self):
        self.size: tuple[int, int]
        self.grid: TablesGridT = []
        self.names: list[str]

    def populate_grid(self, names) -> None:
        grid: TablesGridT = [[None for x in range(self.size[0])] for y in range(self.size[1])]

        # parse tables
        for x, y, xlen, ylen, name in names:
            if xlen < 1 or ylen < 1:
                log_error_exit("Invalid config option. Table can't have length < 1")
            if x + xlen > self.size[0] or y + ylen > self.size[1]:
                log_error_exit("Table can't be placed outside the grid")

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        app.logger.warning("Duplicate table position %s/%s. Check your config", i, j)
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        self.grid = grid

    def set_options(self, table) -> None:
        if (size_config := table.get("size")) is None:
            log_error_exit("table->size missing in config file")
        elif len(size_config) != 2:
            log_error_exit("config option table->size must be exactly of length 2")
        else:
            # size_config has len 2 at this
            self.size = tuple(size_config)  # type: ignore

        if (names_config := table.get("names")) is None:
            log_error_exit("table->names missing in config file")
        elif len(names_config) == 0:
            log_error_exit("config option table->names must be of length >0")
        else:
            self.names = [name for _, _, _, _, name in names_config]
            if len(set(self.names)) != len(self.names):
                log_error_exit("Duplicate table name found. Tables names must be unique")
            self.populate_grid(names_config)


class UIConfig:
    def __init__(self) -> None:
        self.auto_close: bool = True
        self.show_completed: int = 5
        self.timeout_warn: int = 120
        self.timeout_crit: int = 600
        self.split_categories: bool = False
        self.show_category_names: bool = False

    def set_options(self, ui) -> None:
        self.auto_close = ui.get("auto_close", self.auto_close)
        self.show_completed = ui.get("show_completed", self.show_completed)  # zero = don't show
        self.timeout_warn, self.timeout_crit = ui.get("timeout", (self.timeout_warn, self.timeout_crit))
        self.split_categories = ui.get("split_categories", self.split_categories)
        self.show_category_names = ui.get("show_category_names", self.show_category_names)


class MiniPOSConfig:
    def __init__(self, config_file: str) -> None:
        self.product: ProductConfig = ProductConfig()
        self.ui: UIConfig = UIConfig()
        self.table: TableConfig = TableConfig()

        self.load_config(config_file)

    def load_config(self, config_file) -> None:
        if not os.path.isfile(config_file):
            log_error_exit("No config file found. Abort execution")

        app.logger.info("Loading configuration...")

        with open(config_file, encoding="utf-8") as afile:
            try:
                config_data = json.load(afile)
                self.set_options(config_data)
            except json.decoder.JSONDecodeError as e:
                log_error_exit(f"Broken configuration file: {repr(e)!s}")

    def set_options(self, config_data) -> None:
        # debug setting also used for flask
        app.config["DEBUG"] = config_data.get("debug", app.config["DEBUG"])

        if (product := config_data.get("product")) is None:
            log_error_exit("product section missing in config file.")
        else:
            self.product.set_options(product)

        if (table := config_data.get("table")) is None:
            log_error_exit("table section missing in config file.")
        else:
            self.table.set_options(table)

        if (ui := config_data.get("ui")) is None:
            app.logger.warning("ui section is missing in config file. Using defaults.")
        else:
            self.ui.set_options(ui)


def init_config():
    app.config["minipos"] = MiniPOSConfig(app.config["CONFIG_FILE"])

    # adapt log setting
    if app.config["DEBUG"]:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
