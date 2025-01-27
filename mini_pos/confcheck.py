from enum import Enum, auto
from types import NoneType, UnionType  # https://github.com/python/cpython/issues/105499
from typing import Any, get_args, get_origin

CheckResultT = tuple[str, int]
CheckResultListT = list[CheckResultT | None]

# Key: name
# Value: Datatype (origin), mandatory (bool), sub-config (dict)
# If sub-config is tuple, this means any-of
# CONFIG_DICT: dict[str, tuple] = {}


class LogLevel:
    debug = 1
    info = 2
    warning = 3
    error = 4
    critical = 5


def path2str(path: list[str]) -> str:
    """Convert list of paths to string"""
    return "'" + " -> ".join(path) + "'"


def flatten(list_):
    """Flatten 2 dimensional list"""
    return [x for xs in list_ for x in xs]


def find_matching_subval(values, sub_config) -> dict | None:
    """If multiple values are specified in CONFIG_DICT, find the correct one"""
    if type(sub_config) is not tuple:
        msg = "sub_config must be of type tuple"
        raise TypeError(msg)

    matched_confs = []

    for sconf in sub_config:
        if any(x in sconf for x in values):
            # dict type is not hashable (can't be used in 'in' expression)
            matched_confs.append(sconf)

    if len(matched_confs) != 1:
        # Multiple or no configs found. We can't proceed here
        return None

    # Return the correct config
    return matched_confs[0]


# Typecheck functions used by QA checks
def check_primitive_type(data: Any, expected_type: type, path: list) -> CheckResultT | None:
    """Check if data matches a primitive expected type
    e.g. check if data has type str."""
    if isinstance(data, expected_type):
        return None

    return (
        f"Invalid type for config option {path2str(path)}. Is: {type(data)}. Expected: {expected_type}",
        LogLevel.error,
    )


def check_primitive_type_any(data: Any, expected_types: tuple[type], path: list) -> CheckResultT | None:
    """Check if data matches any primitive expected type
    e.g. check if data has either type str or int"""
    if any(isinstance(data, et) for et in expected_types):
        return None

    return (
        f"Invalid type for config option {path2str(path)}. Is: {type(data)}. Expected any of: {expected_types}",
        LogLevel.error,
    )


def check_union_type(data, type_params, path):
    # check if all type params are primitive
    if all(get_origin(tp) is None for tp in type_params):
        return [check_primitive_type_any(data, type_params, path)]

    # We have at least one not-primitive type
    primitive_types = []
    complex_types = []

    for tp in type_params:
        if get_origin(tp) is None:
            primitive_types.append(tp)
        else:
            complex_types.append(tp)

    primitive_result = check_primitive_type_any(data, primitive_types, path)
    if primitive_result is None:
        return []

    # Primitive checks did not pass
    if any(check_complex_type(data, t, path) is not None for t in complex_types):
        return []

    return [(f"Multi-type match did not pass at {path}", LogLevel.error)]


def check_dict_type(data, type_params, path):
    key_type, val_type = type_params

    check_result = []
    for k, v in data.items():
        check_result += check_complex_type(k, key_type, path)
        check_result += check_complex_type(v, val_type, path)

    return check_result


def check_complex_type(data: Any, expected_type: type, path: list) -> CheckResultListT:
    """Check if data matches a complex expected type
    e.g. check if data has type list[tuple[str,str]]."""

    origin = get_origin(expected_type)
    type_params = get_args(expected_type)

    # primitive data type, nothing to unpack
    if origin is None:
        return [check_primitive_type(data, expected_type, path)]

    # if parent type is union, check like a primitive
    if origin is UnionType:
        return check_union_type(data, type_params, path)

    # check parent type (YAML only has lists, python needs tuples)
    safe_origin = list if origin is tuple else origin

    if (primitive_check_result := check_primitive_type(data, safe_origin, path)) is not None:
        return [primitive_check_result]

    if origin is dict:
        return check_dict_type(data, type_params, path)

    # check child types (only if parent type is correct)
    if origin is list:
        return flatten(check_complex_type(d, type_params[0], path) for d in data)

    if origin is tuple:
        if len(type_params) != len(data):
            return [
                ((f"Config option has wrong length (must be {len(type_params)}): {path2str(path)}"), LogLevel.error)
            ]

        return flatten(
            check_complex_type(data[index], type_param, path) for index, type_param in enumerate(type_params)
        )

    msg = "Origin has unexpected type. This should not happen."
    raise TypeError(msg)


def check_mandatory(data: Any, base_config_dict: dict, base_path: list) -> CheckResultListT:
    """Check for any key in base_config_dict that is mandatory but not present in data"""
    check_result: CheckResultListT = []

    present_keys = set(data)
    required_keys = {x for x, y in base_config_dict.items() if y[1]}
    missing_keys = required_keys.difference(present_keys)

    for key in missing_keys:
        path = base_path.copy()
        path.append(key)
        check_result.append((f"Mandatory subkey not found in config: {path2str(path)}", LogLevel.error))

    return check_result


def check_config(data: Any, base_config_dict: dict, base_path: list) -> CheckResultListT:
    """Check if data conforms to the nested datastructure typing_dict.
    Mandatory keys must be present in mandatory_dict.
    e.g. check if data matches {"mykey": list[tuple[str,int]]}
    """
    check_result: CheckResultListT = []

    # First of all, check if any keys are missing
    # Type checking is done later so we only check existence here
    check_result += check_mandatory(data, base_config_dict, base_path)

    # Then iterate over all items in data
    # - Search the corresponding item in the config dict
    # - Check type and, if mandatory, check mandatory sub-keys
    # - For each subkey do the same recursively
    # - In case a mandatory key is missing, print a message

    for key, values in data.items():
        # Duplicate mutable variables to prevent manipulation of the original types
        path = base_path.copy()
        path.append(key)

        config_dict = base_config_dict.copy()

        # Do the actual checking
        if key not in config_dict:
            # Key is not in config_dict, unknown or invalid key
            check_result.append((f"Unrecognized additional key found: {path2str(path)}", LogLevel.info))
        else:
            # Key is in config_dict, good
            expected_type, mandatory, sub_config = config_dict[key]

            if type(sub_config) not in [NoneType, tuple, dict]:
                msg = (
                    f"Only tuple/dict/None are permitted as config values. Type of value is {type(sub_config)}. "
                    "This is a problem in the 'generate.py' script, not with any of the challenge.yml files."
                )
                raise TypeError(msg)

            ctc = [x for x in check_complex_type(values, expected_type, path) if x is not None]  # complex type check

            if ctc:
                # Type check failed
                check_result += ctc
            else:
                # Type matches, proceed with subkeys
                if type(values) is not list:
                    # We assume the given data can be in list format
                    # - If it is but is not allowed to, we should have gotten an error earlier on
                    # - If it is not, but allowed to, we unconditionally convert it to list to make the next step easier
                    # - If it is and is allowed to, we do noting
                    values = [values]

                if type(sub_config) is dict:
                    # Simple case with a dict of sub-values as sub-config
                    for vls in values:
                        check_result += check_config(vls, sub_config, path)

                elif type(sub_config) is tuple:
                    # More complex case with a tuple of sub-values as sub-config
                    # Any of the tuple values should be used in the config
                    # First determine, which of the tuple values is the correct one
                    for vls in values:
                        if (matched_conf := find_matching_subval(vls, sub_config)) is not None:
                            check_result += check_config(vls, matched_conf, path)
                        else:
                            check_result.append(
                                (
                                    f"Could not determine config to use. This usually indicates missing values. {path2str(path)}",
                                    LogLevel.info,
                                )
                            )

    return check_result


def check_config_base(data: Any, config_dict: dict):
    return check_config(data, config_dict, [])  # initialize with empty dict
