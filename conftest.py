import os
import secrets
import string

import pytest

import iatidq.setup
from iatidataquality import app as flask_app
from iatidataquality import db


@pytest.fixture
def app():
    flask_app.config.from_pyfile(os.path.join("..", "config_test.py"))
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def as_admin(client):
    """Log in as admin, use this fixture to test protected views."""

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for i in range(20))
    iatidq.setup.setup_admin_user("admin", password)
    return client.post(
        "/login/",
        data={
            "username": "admin",
            "password": password,
        },
    )
