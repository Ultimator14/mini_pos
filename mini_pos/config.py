import json
import logging
import os
import sys
from typing import Any

from flask import current_app as app

from .confcheck import LogLevel, check_config_base

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]

# Key: name
# Value: Datatype (origin), mandatory (bool), sub-config (dict)
# If sub-config is tuple, this means any-of
CONFIG_DICT: dict[str, tuple] = {
    "product": (
        dict,
        True,
        {
            "available": (list[tuple[str, float, int]], True, None),
            "categories": (list[tuple[int, str]], True, None),
        },
    ),
    "table": (
        dict,
        True,
        {
            "size": (tuple[int, int], True, None),
            "names": (list[tuple[int, int, int, int, str]], True, None),
        },
    ),
    "ui": (
        dict,
        False,
        {
            "auto_close": (bool, False, None),
            "show_completed": (int, False, None),
            "show_category_names": (bool, False, None),
            "fold_categories": (bool, False, None),
            "timeout": (tuple[int, int], False, None),
        },
    ),
    "debug": (bool, False, None),
}


class ProductConfig:
    def __init__(self, product: dict[str, Any]) -> None:
        self.available: AvailableProductsT = dict(
            enumerate([tuple(product) for product in product["available"]], start=1)
        )  # type: ignore
        self.category_map: dict[int, str] = dict(product["categories"])


class TableConfig:
    def __init__(self, table: dict[str, Any]) -> None:
        self.size: tuple[int, int] = tuple(table["size"])  # type: ignore

        names_config = table["names"]
        self.names: list[str] = [name for _, _, _, _, name in names_config]

        if len(set(self.names)) != len(self.names):
            app.logger.critical("Duplicate table name found. Tables names must be unique")

        self.grid: TablesGridT = []
        self.populate_grid(names_config)

    def populate_grid(self, names: list[tuple[int, int, int, int, str]]) -> None:
        grid: TablesGridT = [[None for x in range(self.size[0])] for y in range(self.size[1])]

        # parse tables
        for x, y, xlen, ylen, name in names:
            if xlen < 1 or ylen < 1:
                app.logger.critical("Invalid config option. Table can't have length < 1")
            if x + xlen > self.size[0] or y + ylen > self.size[1]:
                app.logger.critical("Table can't be placed outside the grid")
                return  # tables outside the grid will cause a crash in the next block

            for i in range(y, y + ylen):
                for j in range(x, x + xlen):
                    if grid[i][j] is not None:
                        app.logger.warning("Duplicate table position %s/%s. Check your config", i, j)
                    grid[i][j] = (False, None, None, None)

            grid[y][x] = (True, xlen, ylen, name)

        self.grid = grid


class UIConfig:
    def __init__(self, ui: dict[str, Any]) -> None:
        self.auto_close = ui.get("auto_close", True)
        self.show_completed = ui.get("show_completed", 5)  # zero = don't show
        self.timeout_warn, self.timeout_crit = ui.get("timeout", (120, 600))
        self.show_category_names = ui.get("show_category_names", False)
        self.fold_categories = ui.get("fold_categories", True)


class MiniPOSConfig:
    def __init__(self, config_data: dict) -> None:
        self.product: ProductConfig = ProductConfig(config_data["product"])
        self.table: TableConfig = TableConfig(config_data["table"])
        self.ui: UIConfig = UIConfig(config_data.get("ui", {}))


def load_file(config_file: str) -> dict | None:
    if not os.path.isfile(config_file):
        app.logger.critical("No config file found.")
        return None

    app.logger.info("Loading configuration...")

    with open(config_file, encoding="utf-8") as afile:
        try:
            return json.load(afile)
        except json.decoder.JSONDecodeError as e:
            app.logger.critical("Broken configuration file: %s", repr(e))
            return None


def init_config(app):
    # Check if config file exists and has no json errors
    if (config_data := load_file(app.config["CONFIG_FILE"])) is None:
        sys.exit(1)

    # Check if config conforms to correct structure
    log_lookup = {
        LogLevel.debug: app.logger.debug,
        LogLevel.info: app.logger.info,
        LogLevel.warning: app.logger.warning,
        LogLevel.error: app.logger.error,
        LogLevel.critical: app.logger.critical,
    }

    check_result = check_config_base(config_data, CONFIG_DICT)

    if check_result:
        for msg, fun in check_result:
            log_lookup[fun](msg)

        sys.exit(2)

    # debug setting also used for flask
    app.config["DEBUG"] = config_data.get("debug", app.config["DEBUG"])

    # Make sure that no table is named "login" as this breaks login functionality in service
    if any(x[4] == "login" for x in config_data["table"]["names"]):
        app.logger.critical("Table name 'login' is prohibited.")
        sys.exit(3)

    # Get the crit log count handler to use
    crit_log_count_handler = next((x for x in app.logger.handlers if x.name == "CritLogCountHandler"), None)
    assert crit_log_count_handler is not None  # defined in log.py, should not be None

    # Initialize config object from json
    _ = crit_log_count_handler.count  # reset counter

    app.config["minipos"] = MiniPOSConfig(config_data)

    if crit_log_count_handler.count != 0:
        sys.exit(4)

    # adapt log setting
    if app.config["DEBUG"]:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
