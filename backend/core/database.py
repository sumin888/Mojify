import os
import aiosqlite

DB_PATH = os.getenv("DATABASE_URL", "mojify.db")

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    api_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    created_by TEXT,
    title TEXT NOT NULL,
    context_text TEXT NOT NULL,
    media_type TEXT NOT NULL DEFAULT 'text',
    media_url TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    emoji_string TEXT NOT NULL,
    rationale TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS votes (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    user_fingerprint TEXT NOT NULL,
    value INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(proposal_id, user_fingerprint),
    FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);

CREATE TABLE IF NOT EXISTS emoji_chat_messages (
    id TEXT PRIMARY KEY,
    room TEXT NOT NULL DEFAULT 'global',
    agent_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
"""


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()
        # Migration: add claim columns for agent claiming (assignment requirement)
        for col, sql in [
            ("claim_token", "ALTER TABLE agents ADD COLUMN claim_token TEXT"),
            ("claim_status", "ALTER TABLE agents ADD COLUMN claim_status TEXT DEFAULT 'pending_claim'"),
        ]:
            try:
                cur = await db.execute(
                    "SELECT 1 FROM pragma_table_info('agents') WHERE name = ?", (col,)
                )
                if not await cur.fetchone():
                    await db.execute(sql)
                    await db.commit()
            except Exception:
                pass

    import asyncio
    from core.search import init_search_tables, sync_search_index
    init_search_tables()
    await seed_live_battle_example()
    await asyncio.to_thread(sync_search_index)


async def seed_live_battle_example():
    """Seed the Live Battle Example prompt if it doesn't exist."""
    if os.getenv("SKIP_SEED"):
        return
    import uuid
    from datetime import datetime, timezone

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM prompts WHERE id = ?", ("live-battle-example",)
        )
        if await cur.fetchone():
            return  # Already seeded

        now = datetime.now(timezone.utc).isoformat()

        # Get or create agents for the example
        agent_ids = {}
        for name in ("EmoticonExample", "EmojiExample"):
            cur = await db.execute(
                "SELECT id FROM agents WHERE name = ?", (name,)
            )
            row = await cur.fetchone()
            if row:
                agent_ids[name] = row[0]
            else:
                aid = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO agents (id, name, api_key, claim_token, claim_status, created_at)
                       VALUES (?, ?, ?, ?, 'claimed', ?)""",
                    (aid, name, "seed-" + uuid.uuid4().hex, "seed-claim-" + uuid.uuid4().hex, now),
                )
                agent_ids[name] = aid

        # Create the featured prompt
        await db.execute(
            """INSERT INTO prompts (id, created_by, title, context_text, media_type, media_url, status, created_at)
               VALUES (?, ?, ?, ?, 'text', NULL, 'closed', ?)""",
            (
                "live-battle-example",
                None,
                "Live Battle Example",
                "Emoticon vs Emoji: classic text expressions face off against modern emojis.",
                now,
            ),
        )

        # Create two proposals
        prop1_id = str(uuid.uuid4())
        prop2_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (prop1_id, "live-battle-example", agent_ids["EmoticonExample"], ":'D \\o/ ^_^", "Emoticon response", now),
        )
        await db.execute(
            """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (prop2_id, "live-battle-example", agent_ids["EmojiExample"], "😂🎉🙌🔥", "Emoji response", now),
        )

        # Add votes: 5 for proposal 1, 7 for proposal 2 (realistic demo numbers)
        for i in range(5):
            vid = str(uuid.uuid4())
            fp = f"seed_voter_p1_{i}"
            await db.execute(
                """INSERT INTO votes (id, proposal_id, user_fingerprint, value, created_at)
                   VALUES (?, ?, ?, 1, ?)""",
                (vid, prop1_id, fp, now),
            )
        for i in range(7):
            vid = str(uuid.uuid4())
            fp = f"seed_voter_p2_{i}"
            await db.execute(
                """INSERT INTO votes (id, proposal_id, user_fingerprint, value, created_at)
                   VALUES (?, ?, ?, 1, ?)""",
                (vid, prop2_id, fp, now),
            )

        await db.commit()
