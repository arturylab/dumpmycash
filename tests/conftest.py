import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.models import db as _db
from app.models import User
from app.config import TestConfig

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    with flask_app.app_context():
        _db.drop_all()


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db(app):
    """Provides the database instance and handles cleanup for each test function."""
    with app.app_context():
        pass

    yield _db

    with app.app_context():
        meta = _db.metadata
        for table in reversed(meta.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def auth_client(client, db):
    """A test client that provides helper methods for authentication."""
    class AuthActions:
        def __init__(self, client, db_session):
            self._client = client
            self._db = db_session

        def login(self, email="test@example.com", password="Password123!"):
            return self._client.post('/login', data=dict(
                email=email,
                password=password
            ), follow_redirects=True)

        def logout(self):
            return self._client.post('/logout', follow_redirects=True)

        def register(self, username="testuser", email="test@example.com", password="Password123!"):
            return self._client.post('/register', data=dict(
                username=username,
                email=email,
                password=password
            ), follow_redirects=True)
        
        def create_user(self, username="testuser", email="test@example.com", password="Password123!"):
            user = User(username=username, email=email)
            user.set_password(password)
            self._db.session.add(user)
            self._db.session.commit()
            return user

    return AuthActions(client, _db)