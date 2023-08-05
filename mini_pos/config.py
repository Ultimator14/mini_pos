import json
import logging
import os
import sys
from typing import Any, get_args, get_origin

from flask import current_app as app

AvailableProductsT = dict[int, tuple[str, float, int]]
TablesGridTupleT = tuple[bool, int | None, int | None, str | None]
TablesGridT = list[list[TablesGridTupleT | None]]


TYPING_DICT = {
    "product": {
        "available": list[tuple[str, float, int]],
        "categories": list[tuple[int, str]],
    },
    "table": {
        "size": tuple[int, int],
        "names": list[tuple[int, int, int, int, str]],
    },
    "ui": {
        "auto_close": bool,
        "show_completed": int,
        "show_category_names": bool,
        "split_categories": bool,
        "timeout": tuple[int, int],
    },
    "debug": bool,
}

MANDATORY_DICT = {
    "product": {
        "available": True,
        "categories": True,
    },
    "table": {
        "size": True,
        "names": True,
    },
}


def check_type(data: Any, expected_type: type, path: str) -> bool:
    """Check if data matches a primitive expected type.
    e.g. check if data has type str
    """
    if isinstance(data, expected_type):
        return True

    app.logger.critical("Invalid type for config option: %s", path)
    return False


def unpack_type(data: Any, expected_type: type, path: str) -> bool:
    """Check if data matches a nested expected type.
    e.g. check if data has type list[tuple[str,int]]
    """
    origin = get_origin(expected_type)

    # ban dicts
    if origin is dict:
        err_msg = "Nested dictionary types are not supported for type checking config"
        raise TypeError(err_msg)

    # primitive data type, nothing to unpack
    if origin is None:
        return check_type(data, expected_type, path)

    path = f"{path} -> {origin.__name__!s}"

    # check parent type (JSON only has lists, python needs tuples)
    safe_origin = list if origin is tuple else origin
    if not check_type(data, safe_origin, path):
        return False

    # check child types (only if parent type is correct)
    type_params = get_args(expected_type)

    if origin is list:
        return all(unpack_type(d, type_params[0], path) for d in data)

    if origin is tuple:
        if len(type_params) != len(data):
            app.logger.critical("Config option has wrong length (must be %s): %s", len(type_params), data)
            return False

        return all(unpack_type(data[index], type_param, path) for index, type_param in enumerate(type_params))

    return all(check_type(data[tp], type_params[tp], path) for tp in type_params)


def check_config(data: Any, typing_dict: dict, mandatory_dict: dict | None, path="."):
    """Check if data conforms to the nested datastructure typing_dict.
    Mandatory keys must be present in mandatory_dict.
    e.g. check if data matches {"mykey": list[tuple[str,int]]}
    """
    check_result = True

    # Iterate over all supported config options
    for key, expected_type in typing_dict.items():
        subpath = f"{path} -> {key}"

        if key in data:
            # Key is present in config
            if type(expected_type) is dict:
                if check_type(data[key], dict, subpath):
                    md = mandatory_dict.get(key) if type(mandatory_dict) is dict else None
                    check_result = check_config(data[key], typing_dict[key], md, subpath) and check_result
                else:
                    check_result = False
            else:
                check_result = unpack_type(data[key], expected_type, subpath) and check_result
        else:
            # Key is missing from config
            if mandatory_dict is not None and mandatory_dict.get(key):
                app.logger.critical("Mandatory key missing from config: %s", subpath)
                check_result = False
            else:
                app.logger.warning("Optional key missing from config: %s", subpath)

    return check_result


class ProductConfig:
    def __init__(self, product: dict[str, Any]) -> None:
        self.available: AvailableProductsT = dict(enumerate([tuple(product) for product in product["available"]], start=1))  # type: ignore
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
        self.split_categories = ui.get("split_categories", False)
        self.show_category_names = ui.get("show_category_names", False)


class MiniPOSConfig:
    def __init__(self, config_data: dict) -> None:
        # debug setting also used for flask
        app.config["DEBUG"] = config_data.get("debug", app.config["DEBUG"])  # optional

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
    if not check_config(config_data, TYPING_DICT, MANDATORY_DICT):
        sys.exit(1)

    # Get the crit log count handler to use
    crit_log_count_handler = next((x for x in app.logger.handlers if x.name == "CritLogCountHandler"), None)
    assert crit_log_count_handler is not None  # defined in log.py, should not be None

    # Initialize config object from json
    _ = crit_log_count_handler.count  # reset counter

    app.config["minipos"] = MiniPOSConfig(config_data)

    if crit_log_count_handler.count != 0:
        sys.exit(1)

    # adapt log setting
    if app.config["DEBUG"]:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
