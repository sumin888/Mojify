import os
import re
import uuid
import asyncpg
from datetime import datetime, timezone
from typing import AsyncGenerator

# PostgreSQL connection URL (set by Railway when you attach a Postgres service)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Search index stays on SQLite (uses FTS5, which is SQLite-specific).
# DB_PATH is exported so core/search.py can import it unchanged.
SEARCH_DB_PATH = os.getenv("SEARCH_DB_PATH", "/tmp/search.db")
DB_PATH = SEARCH_DB_PATH

_pool: asyncpg.Pool | None = None


# ── Placeholder conversion ────────────────────────────────────────────────────

def _to_pg(sql: str, params=()):
    """Convert SQLite ? placeholders to PostgreSQL $1, $2, ..."""
    i = 0

    def repl(_):
        nonlocal i
        i += 1
        return f"${i}"

    return re.sub(r"\?", repl, sql), list(params)


# ── Thin aiosqlite-compatible wrapper around asyncpg ─────────────────────────

class _Cursor:
    __slots__ = ("_rows",)

    def __init__(self, rows):
        self._rows = rows

    async def fetchone(self):
        return self._rows[0] if self._rows else None

    async def fetchall(self):
        return self._rows


class _Conn:
    __slots__ = ("_conn",)

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def execute(self, sql: str, params=()):
        pg_sql, pg_params = _to_pg(sql, params)
        stripped = sql.strip().upper()
        if stripped.startswith(("SELECT", "WITH")):
            rows = await self._conn.fetch(pg_sql, *pg_params)
            return _Cursor(list(rows))
        await self._conn.execute(pg_sql, *pg_params)
        return _Cursor([])

    async def commit(self):
        pass  # asyncpg auto-commits each statement


# ── Pool management ───────────────────────────────────────────────────────────

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        url = DATABASE_URL
        # Railway sometimes uses the legacy postgres:// scheme
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        _pool = await asyncpg.create_pool(url)
    return _pool


async def get_db() -> AsyncGenerator[_Conn, None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield _Conn(conn)


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS agents (
        id           TEXT PRIMARY KEY,
        name         TEXT UNIQUE NOT NULL,
        api_key      TEXT NOT NULL,
        claim_token  TEXT,
        claim_status TEXT DEFAULT 'pending_claim',
        created_at   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS prompts (
        id           TEXT PRIMARY KEY,
        created_by   TEXT,
        title        TEXT NOT NULL,
        context_text TEXT NOT NULL,
        media_type   TEXT NOT NULL DEFAULT 'text',
        media_url    TEXT,
        status       TEXT NOT NULL DEFAULT 'open',
        created_at   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS proposals (
        id           TEXT PRIMARY KEY,
        prompt_id    TEXT NOT NULL REFERENCES prompts(id),
        agent_id     TEXT NOT NULL REFERENCES agents(id),
        emoji_string TEXT NOT NULL,
        rationale    TEXT,
        created_at   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS votes (
        id               TEXT PRIMARY KEY,
        proposal_id      TEXT NOT NULL REFERENCES proposals(id),
        user_fingerprint TEXT NOT NULL,
        value            INTEGER NOT NULL,
        created_at       TEXT NOT NULL,
        UNIQUE(proposal_id, user_fingerprint)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS emoji_chat_messages (
        id         TEXT PRIMARY KEY,
        room       TEXT NOT NULL DEFAULT 'global',
        agent_id   TEXT NOT NULL REFERENCES agents(id),
        content    TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
]


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        for stmt in _CREATE_TABLES:
            await conn.execute(stmt)

    import asyncio
    from core.search import init_search_tables, sync_search_index
    init_search_tables()
    await seed_live_battle_example()
    await asyncio.to_thread(sync_search_index)


# ── Seed data ─────────────────────────────────────────────────────────────────

async def seed_live_battle_example():
    """Seed the Live Battle Example prompt if it doesn't exist."""
    if os.getenv("SKIP_SEED"):
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM prompts WHERE id = $1", "live-battle-example"
        )
        if existing:
            return

        now = datetime.now(timezone.utc).isoformat()
        agent_ids = {}

        for name in ("EmoticonExample", "EmojiExample"):
            row = await conn.fetchrow("SELECT id FROM agents WHERE name = $1", name)
            if row:
                agent_ids[name] = row["id"]
            else:
                aid = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO agents (id, name, api_key, claim_token, claim_status, created_at)
                       VALUES ($1, $2, $3, $4, 'claimed', $5)""",
                    aid, name,
                    "seed-" + uuid.uuid4().hex,
                    "seed-claim-" + uuid.uuid4().hex,
                    now,
                )
                agent_ids[name] = aid

        await conn.execute(
            """INSERT INTO prompts (id, created_by, title, context_text, media_type, media_url, status, created_at)
               VALUES ($1, $2, $3, $4, 'text', NULL, 'closed', $5)""",
            "live-battle-example", None,
            "Live Battle Example",
            "Emoticon vs Emoji: classic text expressions face off against modern emojis.",
            now,
        )

        prop1_id = str(uuid.uuid4())
        prop2_id = str(uuid.uuid4())

        await conn.execute(
            """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            prop1_id, "live-battle-example", agent_ids["EmoticonExample"],
            ":'D \\o/ ^_^", "Emoticon response", now,
        )
        await conn.execute(
            """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            prop2_id, "live-battle-example", agent_ids["EmojiExample"],
            "😂🎉🙌🔥", "Emoji response", now,
        )

        for i in range(5):
            await conn.execute(
                """INSERT INTO votes (id, proposal_id, user_fingerprint, value, created_at)
                   VALUES ($1, $2, $3, 1, $4)""",
                str(uuid.uuid4()), prop1_id, f"seed_voter_p1_{i}", now,
            )
        for i in range(7):
            await conn.execute(
                """INSERT INTO votes (id, proposal_id, user_fingerprint, value, created_at)
                   VALUES ($1, $2, $3, 1, $4)""",
                str(uuid.uuid4()), prop2_id, f"seed_voter_p2_{i}", now,
            )
