import pytest

from mini_pos import create_app
from mini_pos.settings import TestConfig


@pytest.fixture()
def app():
    return create_app(config=TestConfig)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
