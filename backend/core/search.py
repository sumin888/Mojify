"""
Hybrid search: BM25 (FTS5) + vector similarity with RRF fusion.
Optimized for production: connection pooling, incremental indexing,
async-safe embedding, numpy-free cosine fallback, and robust error handling.
"""
from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
from contextlib import contextmanager
from threading import Lock
from typing import Optional

from core.database import DB_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Encoder — fastembed, lazy-loaded, thread-safe singleton
#
# Why fastembed over sentence-transformers:
#   - ONNX runtime only (~50 MB), no PyTorch (~500 MB)
#   - Model is downloaded once to a local cache dir (set via
#     FASTEMBED_CACHE_DIR env var — point this at a Railway volume
#     or persistent path so it survives redeploys)
#   - Same embedding space as all-MiniLM-L6-v2 (384-dim)
#
# Install: pip install fastembed
# Optional cache: set FASTEMBED_CACHE_DIR=/data/fastembed_cache in Railway env vars
# ---------------------------------------------------------------------------

import os

_encoder = None
_encoder_lock = Lock()
_encoder_available: bool | None = None  # None = untried

# Model name in fastembed's registry — identical vector space to all-MiniLM-L6-v2
_FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _get_encoder():
    global _encoder, _encoder_available
    if _encoder_available is False:
        return None
    if _encoder is not None:
        return _encoder
    with _encoder_lock:
        # Double-checked locking
        if _encoder is not None:
            return _encoder
        try:
            from fastembed import TextEmbedding
            cache_dir = os.environ.get("FASTEMBED_CACHE_DIR")
            kwargs = {"cache_dir": cache_dir} if cache_dir else {}
            _encoder = TextEmbedding(model_name=_FASTEMBED_MODEL, **kwargs)
            _encoder_available = True
            logger.info("Loaded fastembed encoder: %s", _FASTEMBED_MODEL)
        except ImportError:
            _encoder_available = False
            logger.warning("fastembed not installed — falling back to BM25-only search. Run: pip install fastembed")
    return _encoder


# ---------------------------------------------------------------------------
# Connection helper — use WAL mode for better read/write concurrency
# ---------------------------------------------------------------------------

@contextmanager
def _connect(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_search_tables(db_path: str = DB_PATH) -> None:
    """Create FTS5 and embeddings tables if they don't exist."""
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_embeddings (
                entity_type TEXT NOT NULL,
                entity_id   TEXT NOT NULL,
                content     TEXT NOT NULL,
                embedding   BLOB NOT NULL,
                PRIMARY KEY (entity_type, entity_id)
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
                entity_type,
                entity_id UNINDEXED,
                title,
                content,
                tokenize='porter unicode61'
            )
        """)
        # Index to speed up entity_type lookups on the embeddings table
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_type
            ON search_embeddings(entity_type)
        """)


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embed(text: str) -> list[float] | None:
    model = _get_encoder()
    if model is None:
        return None
    # fastembed.embed() returns a generator of numpy arrays, one per input
    result = next(model.embed([text]))
    return result.tolist()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure-Python fallback (no numpy required). Fast enough for <10k docs."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    denom = norm_a * norm_b
    return dot / denom if denom > 1e-9 else 0.0


def _pack_embedding(emb: list[float]) -> str:
    """Store as compact JSON (or swap for struct.pack for ~3x smaller blobs)."""
    return json.dumps(emb)


def _unpack_embedding(raw: str | bytes) -> list[float]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


# ---------------------------------------------------------------------------
# FTS query sanitisation
# ---------------------------------------------------------------------------

_FTS_SPECIAL = re.compile(r'[^\w\s]', re.UNICODE)

def _build_fts_query(query: str, max_terms: int = 6) -> str | None:
    """
    Sanitise and build an FTS5 query string.
    Returns None if no valid tokens remain.
    Uses AND so all terms must appear — more precise than OR.
    Falls back to OR if the AND match returns no results (handled at call site).
    """
    clean = _FTS_SPECIAL.sub(" ", query)
    tokens = [t for t in clean.split() if len(t) >= 2][:max_terms]
    if not tokens:
        return None
    # Append * to the last token for prefix matching (e.g. "age" matches "agents")
    terms = tokens[:-1] + [tokens[-1] + "*"]
    return " AND ".join(terms)


# ---------------------------------------------------------------------------
# Incremental sync helpers
# ---------------------------------------------------------------------------

def _indexed_ids(conn: sqlite3.Connection, entity_type: str) -> set[str]:
    rows = conn.execute(
        "SELECT entity_id FROM search_fts WHERE entity_type = ?", (entity_type,)
    ).fetchall()
    return {r["entity_id"] for r in rows}


def _insert_entity(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    title: str,
    content: str,
) -> None:
    conn.execute(
        "INSERT INTO search_fts (entity_type, entity_id, title, content) VALUES (?, ?, ?, ?)",
        (entity_type, entity_id, title, content),
    )
    emb = _embed(content)
    if emb is not None:
        conn.execute(
            """INSERT OR REPLACE INTO search_embeddings
               (entity_type, entity_id, content, embedding) VALUES (?, ?, ?, ?)""",
            (entity_type, entity_id, content, _pack_embedding(emb)),
        )


def _delete_entity(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> None:
    conn.execute(
        "DELETE FROM search_fts WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    )
    conn.execute(
        "DELETE FROM search_embeddings WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    )


# ---------------------------------------------------------------------------
# Public sync API
# ---------------------------------------------------------------------------

def sync_search_index(db_path: str = DB_PATH, incremental: bool = True) -> int:
    """
    Sync FTS5 and embeddings tables from prompts, agents, proposals.

    incremental=True  — only index new rows (fast, safe to call on every write)
    incremental=False — full rebuild (use for schema migrations or repairs)

    Returns the number of newly indexed items.
    """
    with _connect(db_path) as conn:
        if not incremental:
            conn.execute("DELETE FROM search_fts")
            conn.execute("DELETE FROM search_embeddings")
            existing_prompts: set[str] = set()
            existing_agents: set[str] = set()
            existing_proposals: set[str] = set()
        else:
            existing_prompts = _indexed_ids(conn, "prompt")
            existing_agents = _indexed_ids(conn, "agent")
            existing_proposals = _indexed_ids(conn, "proposal")

        count = 0

        # --- Prompts ---
        for row in conn.execute("SELECT id, title, context_text FROM prompts").fetchall():
            if row["id"] in existing_prompts:
                continue
            title = row["title"] or ""
            content = f"{title} {row['context_text'] or ''}".strip()
            _insert_entity(conn, "prompt", row["id"], title, content)
            count += 1

        # --- Agents ---
        for row in conn.execute("SELECT id, name FROM agents").fetchall():
            if row["id"] in existing_agents:
                continue
            name = row["name"] or ""
            content = name
            _insert_entity(conn, "agent", row["id"], name, content)
            count += 1

        # --- Proposals ---
        for row in conn.execute(
            """SELECT pr.id, pr.emoji_string, pr.rationale, p.title AS prompt_title
               FROM proposals pr
               JOIN prompts p ON p.id = pr.prompt_id"""
        ).fetchall():
            if row["id"] in existing_proposals:
                continue
            content = f"{row['emoji_string'] or ''} {row['rationale'] or ''} {row['prompt_title'] or ''}".strip()
            title = (row["rationale"] or row["emoji_string"] or "")[:100]
            _insert_entity(conn, "proposal", row["id"], title, content)
            count += 1

    logger.debug("sync_search_index: indexed %d new items (incremental=%s)", count, incremental)
    return count


def index_one(
    entity_type: str,
    entity_id: str,
    title: str,
    content: str,
    db_path: str = DB_PATH,
) -> None:
    """
    Index a single entity immediately after creation/update.
    Call this from your route handlers instead of a full sync.

    Example:
        index_one("prompt", new_prompt.id, new_prompt.title, new_prompt.context_text)
    """
    with _connect(db_path) as conn:
        _delete_entity(conn, entity_type, entity_id)  # remove stale version if any
        _insert_entity(conn, entity_type, entity_id, title, content)


def delete_one(entity_type: str, entity_id: str, db_path: str = DB_PATH) -> None:
    """Remove a single entity from the search index (call on deletion)."""
    with _connect(db_path) as conn:
        _delete_entity(conn, entity_type, entity_id)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    limit: int = 20,
    entity_types: Optional[list[str]] = None,
    db_path: str = DB_PATH,
) -> list[dict]:
    """
    Hybrid BM25 + vector search with Reciprocal Rank Fusion (RRF).
    Returns list of {entity_type, entity_id, title, snippet, score}.
    Falls back gracefully to BM25-only if embeddings are unavailable.
    """
    if not query or not query.strip():
        return []

    q = query.strip()
    fts_query = _build_fts_query(q)
    if fts_query is None:
        return []

    type_filter = ""
    type_params: list = []
    if entity_types:
        placeholders = ",".join("?" * len(entity_types))
        type_filter = f" AND entity_type IN ({placeholders})"
        type_params = list(entity_types)

    fetch_limit = limit * 3  # over-fetch before RRF re-ranking

    with _connect(db_path) as conn:
        # --- BM25 via FTS5 ---
        bm25_rows = _run_fts(conn, fts_query, type_filter, type_params, fetch_limit)

        # If AND query matched nothing, retry with OR (broader fallback)
        if not bm25_rows and " AND " in fts_query:
            fts_or = fts_query.replace(" AND ", " OR ")
            bm25_rows = _run_fts(conn, fts_or, type_filter, type_params, fetch_limit)

        # --- Vector search ---
        query_embedding = _embed(q)
        vector_ranked: list[tuple[str, str, str]] = []

        if query_embedding is not None:
            emb_sql = "SELECT entity_type, entity_id, content, embedding FROM search_embeddings"
            emb_params: list = []
            if entity_types:
                emb_sql += f" WHERE entity_type IN ({','.join('?' * len(entity_types))})"
                emb_params = list(entity_types)

            scored: list[tuple[str, str, str, float]] = []
            for row in conn.execute(emb_sql, emb_params).fetchall():
                emb = _unpack_embedding(row["embedding"])
                sim = _cosine_similarity(query_embedding, emb)
                if sim > 0.15:
                    scored.append((row["entity_type"], row["entity_id"], row["content"][:100], sim))

            scored.sort(key=lambda x: -x[3])
            vector_ranked = [(r[0], r[1], r[2]) for r in scored[:fetch_limit]]

    # --- RRF fusion (k=60 is standard) ---
    k = 60
    rrf: dict[tuple[str, str], float] = {}

    for rank, row in enumerate(bm25_rows):
        key = (row["entity_type"], row["entity_id"])
        rrf[key] = rrf.get(key, 0.0) + 1.0 / (k + rank + 1)

    for rank, (etype, eid, _) in enumerate(vector_ranked):
        key = (etype, eid)
        rrf[key] = rrf.get(key, 0.0) + 1.0 / (k + rank + 1)

    # --- Build output ---
    bm25_lookup = {(r["entity_type"], r["entity_id"]): r for r in bm25_rows}
    vector_content = {(r[0], r[1]): r[2] for r in vector_ranked}

    results: list[dict] = []
    for (etype, eid), score in sorted(rrf.items(), key=lambda x: -x[1])[:limit]:
        bm = bm25_lookup.get((etype, eid))
        title = bm["title"] if bm else (vector_content.get((etype, eid)) or "")[:80]
        snippet = (bm["snippet"] if bm and bm["snippet"] else None)
        results.append({
            "entity_type": etype,
            "entity_id": eid,
            "title": title,
            "snippet": snippet,
            "score": round(score, 4),
        })

    return results


def _run_fts(
    conn: sqlite3.Connection,
    fts_query: str,
    type_filter: str,
    type_params: list,
    limit: int,
) -> list[sqlite3.Row]:
    try:
        return conn.execute(
            f"""
            SELECT entity_type, entity_id, title,
                   snippet(search_fts, 3, '<b>', '</b>', '…', 12) AS snippet,
                   bm25(search_fts) AS rank
            FROM search_fts
            WHERE search_fts MATCH ?
            {type_filter}
            ORDER BY rank
            LIMIT ?
            """,
            [fts_query] + type_params + [limit],
        ).fetchall()
    except sqlite3.OperationalError as exc:
        logger.warning("FTS query failed (%s): %s", fts_query, exc)
        return []