import os
import tempfile

import pytest

from mini_pos import create_app
from mini_pos.settings import TestConfig


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp()

    flask_app = create_app(config=TestConfig)

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
