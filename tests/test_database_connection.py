import os
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

@pytest.fixture(scope='module')
def db_engine():
    """Fixture to create a database engine for testing."""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    yield engine
    engine.dispose()

def test_database_connection_should_fail():
    """
    Test deliberately using invalid credentials to simulate failure.
    This test passes if the connection fails as expected.
    """
    invalid_url = "postgresql://dump:dump1234@localhost:5432/DumpMyCash"
    engine = create_engine(invalid_url)
    
    with pytest.raises(OperationalError):
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

def test_database_connection_should_succeed(db_engine):
    """
    Test using correct credentials from config.py.
    This test passes if the connection is successful.
    """
    with db_engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
