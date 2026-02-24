"""
Unit tests for database initialization and operations.
"""
import asyncio

import aiosqlite
import pytest

from database import CREATE_TABLES, init_db
from tests.test_utils import TEST_DB_PATH, clear_db, run_async


def test_init_db_creates_tables():
    """init_db should create all required tables."""
    run_async(init_db())

    async def check_tables():
        async with aiosqlite.connect(TEST_DB_PATH) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            rows = await cursor.fetchall()
            tables = [r[0] for r in rows]
        return tables

    tables = run_async(check_tables())
    expected = {"agents", "prompts", "proposals", "votes", "emoji_chat_messages"}
    assert expected.issubset(set(tables))


def test_init_db_idempotent():
    """init_db can be called multiple times without error (IF NOT EXISTS)."""
    run_async(init_db())
    run_async(init_db())
    run_async(init_db())
    # No exception raised


def test_agents_table_schema():
    """Agents table has correct columns."""
    run_async(init_db())

    async def check():
        async with aiosqlite.connect(TEST_DB_PATH) as db:
            cursor = await db.execute("PRAGMA table_info(agents)")
            cols = [r[1] for r in await cursor.fetchall()]
        return cols

    cols = run_async(check())
    assert "id" in cols
    assert "name" in cols
    assert "api_key" in cols
    assert "created_at" in cols


def test_insert_and_clear_agents():
    """Insert agent, verify it exists, then clear DB."""
    run_async(init_db())

    async def insert_and_verify():
        async with aiosqlite.connect(TEST_DB_PATH) as db:
            await db.execute(
                "INSERT INTO agents (id, name, api_key, created_at) VALUES (?, ?, ?, ?)",
                ("test-id", "TestAgent", "key123", "2026-01-01T00:00:00Z"),
            )
            await db.commit()
            cursor = await db.execute("SELECT name FROM agents WHERE id = ?", ("test-id",))
            row = await cursor.fetchone()
        return row[0] if row else None

    name = run_async(insert_and_verify())
    assert name == "TestAgent"

    run_async(clear_db())

    async def verify_cleared():
        async with aiosqlite.connect(TEST_DB_PATH) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            count = (await cursor.fetchone())[0]
        return count

    count = run_async(verify_cleared())
    assert count == 0
