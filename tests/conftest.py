"""Shared pytest fixtures."""
import pytest

from techwatch.models import db


@pytest.fixture
def conn():
    """An initialised in-memory database, fresh for each test."""
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()
