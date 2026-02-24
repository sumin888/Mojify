"""
Pytest configuration and fixtures for backend tests.
Uses a temporary database file; clears tables after tests that insert data.
"""
import asyncio

import pytest

from tests.test_utils import TEST_DB_PATH, clear_db, run_async
from database import get_db, init_db
from main import app


async def get_test_db():
    """Test DB dependency - uses temp file."""
    import aiosqlite
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def init_test_db():
    """Initialize test database (run once per session)."""
    run_async(init_db())


@pytest.fixture(autouse=True)
def reset_db(init_test_db):
    """Clear DB before each test so tests start with a clean slate."""
    run_async(clear_db())
    yield
    run_async(clear_db())


@pytest.fixture
def client():
    """TestClient with overridden DB dependency."""
    app.dependency_overrides[get_db] = get_test_db
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
