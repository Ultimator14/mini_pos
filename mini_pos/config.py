#!/usr/bin/python3.11

import json
import logging
import os
import sys
from typing import Any

from flask import current_app as app

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]


class ProductConfig:
    procuct_type: type= list[list[tuple[str,str]]]

    def __init__(self) -> None:
        self.available: AvailableProductsT = {}
        self.category_map: dict[int, str] = {}

    def set_options(self, product: dict[str,Any]) -> None:
        if (available_config := product.get("available")) is None:
            app.logger.critical("prouct->available missing in config file")
        elif len(available_config) == 0:
            app.logger.critical("config option product->available must be of length >0")
        elif not all(tuple(type(x) for x in y) == (str, float, int) for y in available_config):
            app.logger.critical("config option product->available must be of type list(str, float, int)")
        else:
            self.available = dict(enumerate([tuple(product) for product in available_config], start=1))  # type: ignore

        if (categories_config := product.get("categories")) is None:
            app.logger.critical("prouct->categories missing in config file")
        elif len(categories_config) == 0:
            app.logger.critical("config option product->categories must be of length >0")
        else:
            self.category_map = dict(categories_config)


class TableConfig:
    def __init__(self) -> None:
        self.size: tuple[int, int]
        self.grid: TablesGridT = []
        self.names: list[str]

    def populate_grid(self, names: list[tuple[int,int,int,int,str]]) -> None:
        grid: TablesGridT = [[None for x in range(self.size[0])] for y in range(self.size[1])]

        # parse tables
        for x, y, xlen, ylen, name in names:
            if xlen < 1 or ylen < 1:
                app.logger.critical("Invalid config option. Table can't have length < 1")
            if x + xlen > self.size[0] or y + ylen > self.size[1]:
                app.logger.critical("Table can't be placed outside the grid")

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        app.logger.warning("Duplicate table position %s/%s. Check your config", i, j)
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        self.grid = grid

    def set_options(self, table: dict[str,Any]) -> None:
        if (size_config := table.get("size")) is None:
            app.logger.critical("table->size missing in config file")
        elif len(size_config) != 2:
            app.logger.critical("config option table->size must be exactly of length 2")
        elif tuple(type(x) for x in size_config) != (int, int):
            app.logger.critical("config option table->size must be of type (int, int)")
        else:
            self.size = tuple(size_config)  # type: ignore

        if (names_config := table.get("names")) is None:
            app.logger.critical("table->names missing in config file")
        elif len(names_config) == 0:
            app.logger.critical("config option table->names must be of length >0")
        else:
            self.names = [name for _, _, _, _, name in names_config]
            if len(set(self.names)) != len(self.names):
                app.logger.critical("Duplicate table name found. Tables names must be unique")
            self.populate_grid(names_config)


class UIConfig:
    def __init__(self) -> None:
        self.auto_close: bool = True
        self.show_completed: int = 5
        self.timeout_warn: int = 120
        self.timeout_crit: int = 600
        self.split_categories: bool = False
        self.show_category_names: bool = False

    def set_options(self, ui: dict[str, Any]) -> None:
        self.auto_close = ui.get("auto_close", self.auto_close)
        self.show_completed = ui.get("show_completed", self.show_completed)  # zero = don't show
        self.timeout_warn, self.timeout_crit = ui.get("timeout", (self.timeout_warn, self.timeout_crit))
        self.split_categories = ui.get("split_categories", self.split_categories)
        self.show_category_names = ui.get("show_category_names", self.show_category_names)


class MiniPOSConfig:
    def __init__(self) -> None:
        self.product: ProductConfig = ProductConfig()
        self.ui: UIConfig = UIConfig()
        self.table: TableConfig = TableConfig()

    def load_file(self, config_file: str) -> None:
        if not os.path.isfile(config_file):
            app.logger.critical("No config file found. Abort execution")

        app.logger.info("Loading configuration...")

        with open(config_file, encoding="utf-8") as afile:
            try:
                config_data = json.load(afile)
                self.set_options(config_data)
            except json.decoder.JSONDecodeError as e:
                app.logger.critical("Broken configuration file: %s", repr(e))

    def set_options(self, config_data: dict) -> None:
        # debug setting also used for flask
        app.config["DEBUG"] = config_data.get("debug", app.config["DEBUG"])

        if (product := config_data.get("product")) is None:
            app.logger.critical("product section missing in config file.")
        else:
            self.product.set_options(product)

        if (table := config_data.get("table")) is None:
            app.logger.critical("table section missing in config file.")
        else:
            self.table.set_options(table)

        if (ui := config_data.get("ui")) is None:
            app.logger.warning("ui section is missing in config file. Using defaults.")
        else:
            self.ui.set_options(ui)


def init_config(app):
    # Get the crit log count handler to use
    crit_log_count_handler = next((x for x in app.logger.handlers if x.name == "CritLogCountHandler"), None)
    assert(crit_log_count_handler is not None)  # defined in log.py, should not be None

    _ = crit_log_count_handler.count  # reset counter

    mp = MiniPOSConfig()
    mp.load_file(app.config["CONFIG_FILE"])
    app.config["minipos"] = mp

    if crit_log_count_handler.count != 0:
        sys.exit(1)

    # adapt log setting
    if app.config["DEBUG"]:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
