from mini_pos.config import CONFIG_DICT, MiniPOSConfig
from mini_pos.confcheck import check_config_base

def test_valid_config(app):
    config_data = {"products": {}, "tables": {"size": [1, 1], "names": []}}

    with app.app_context():
        assert not check_config_base(config_data, CONFIG_DICT)


def test_missing_mandatory_value(app):
    config_data = {"products": {}, "tables": {"size": [1, 1]}}

    with app.app_context():
        assert check_config_base(config_data, CONFIG_DICT)


def test_wrong_toplevel_type(app):
    config_data = {"products": {}, "tables": {"size": True, "names": [], "ui": True}}

    with app.app_context():
        assert check_config_base(config_data, CONFIG_DICT)


def test_wrong_type(app):
    config_data = {"products": {}, "tables": {"size": True, "names": []}}

    with app.app_context():
        assert check_config_base(config_data, CONFIG_DICT)


def get_crit_log_handler(app):
    crit_log_count_handler = next((x for x in app.logger.handlers if x.name == "CritLogCountHandler"), None)

    assert crit_log_count_handler is not None

    _ = crit_log_count_handler.count  # reset counter

    return crit_log_count_handler


def test_minipos_config(app):
    config_data = {"products": {}, "tables": {"size": [1, 1], "names": []}}
    clh = get_crit_log_handler(app)

    with app.app_context():
        _ = MiniPOSConfig(config_data)

    assert clh.count == 0


def test_duplicate_table_name(app):
    config_data = {
        "products": {},
        "tables": {"size": [2, 2], "names": [[0, 0, 1, 1, "A1"], [1, 1, 1, 1, "A1"]]},
    }
    clh = get_crit_log_handler(app)

    with app.app_context():
        _ = MiniPOSConfig(config_data)

    assert clh.count == 1


def test_invalid_table_length(app):
    config_data = {
        "products": {},
        "tables": {"size": [2, 2], "names": [[0, 0, 0, 1, "A1"]]},
    }
    clh = get_crit_log_handler(app)

    with app.app_context():
        _ = MiniPOSConfig(config_data)

    assert clh.count == 1

def test_table_outside_grid(app):
    config_data = {
        "products": {},
        "tables": {"size": [1, 1], "names": [[0, 0, 1, 2, "A1"]]},
    }
    clh = get_crit_log_handler(app)

    with app.app_context():
        _ = MiniPOSConfig(config_data)

    assert clh.count == 1
