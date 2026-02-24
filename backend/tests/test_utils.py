"""
Shared test utilities: DB path, clear_db, run_async.
"""
import asyncio
import os
import tempfile

import aiosqlite

# Set test DB path before any database imports
_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB_PATH = _test_db_file.name
_test_db_file.close()
os.environ["DATABASE_URL"] = TEST_DB_PATH
os.environ["SKIP_SEED"] = "1"  # Skip seed so tests start with empty DB


async def clear_db():
    """Delete all data from test DB (respects FK order)."""
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("DELETE FROM votes")
        await db.execute("DELETE FROM proposals")
        await db.execute("DELETE FROM emoji_chat_messages")
        await db.execute("DELETE FROM prompts")
        await db.execute("DELETE FROM agents")
        await db.commit()


def run_async(coro):
    """Run async coroutine from sync context."""
    return asyncio.run(coro)
