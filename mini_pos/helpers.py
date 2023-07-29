#!/usr/bin/python3.11

import sys
from typing import NoReturn

from . import Config


def _cyan(prompt: str) -> str:
    return f"\033[36;1m{prompt}\033[0m"  # ]]


def _green(prompt: str) -> str:
    return f"\033[32;1m{prompt}\033[0m"  # ]]


def _yellow(prompt: str) -> str:
    return f"\033[33;1m{prompt}\033[0m"  # ]]


def _red(prompt: str) -> str:
    return f"\033[31;1m{prompt}\033[0m"  # ]]


def log_debug(msg: str) -> None:
    if Config.debug:
        print(_cyan(f"*** Debug ***: {msg}"))  # ]]


def log_info(msg: str) -> None:
    print(_green(f"*** Info ***: {msg}"))  # ]]


def log_warn(msg: str) -> None:
    print(_yellow(f"*** Warning! ***: {msg}"))  # ]]


def log_error(msg: str) -> None:
    print(_red(f"*** Error! ***: {msg}"))  # ]]


def log_error_exit(msg: str) -> NoReturn:
    log_error(msg)
    sys.exit(1)
