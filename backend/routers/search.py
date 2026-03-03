import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query

from core.database import get_db
from core.search import hybrid_search

router = APIRouter(prefix="/api/search", tags=["search"])

# Intent keywords that map to a sort order rather than text content.
# When the query matches one of these we return prompts sorted accordingly.
_INTENT_SORT: dict[str, str] = {
    "trending": "total_votes DESC, p.created_at DESC",
    "trend":    "total_votes DESC, p.created_at DESC",
    "hot":      "total_votes DESC, proposal_count DESC, p.created_at DESC",
    "popular":  "total_votes DESC, proposal_count DESC, p.created_at DESC",
    "top":      "total_votes DESC, p.created_at DESC",
    "new":      "p.created_at DESC",
    "newest":   "p.created_at DESC",
    "latest":   "p.created_at DESC",
    "recent":   "p.created_at DESC",
}


async def _intent_results(order: str, limit: int, db) -> list[dict]:
    """Return prompts sorted by the given order clause as search results."""
    cursor = await db.execute(
        f"""
        SELECT p.id, p.title, p.context_text,
               COUNT(pr.id) AS proposal_count,
               COALESCE(SUM(v.value), 0) AS total_votes
        FROM prompts p
        LEFT JOIN proposals pr ON pr.prompt_id = p.id
        LEFT JOIN votes v ON v.proposal_id = pr.id
        GROUP BY p.id
        ORDER BY {order}
        LIMIT ?
        """,
        (limit,),
    )
    rows = await cursor.fetchall()
    return [
        {
            "entity_type": "prompt",
            "entity_id": r["id"],
            "title": r["title"],
            "snippet": (r["context_text"] or "")[:120] or None,
            "score": 1.0,
        }
        for r in rows
    ]


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    type: Optional[str] = Query(default=None, description="Filter: prompt, agent, proposal"),
    db=Depends(get_db),
):
    """
    Hybrid BM25 + vector search across prompts (rounds), agents, and proposals.
    Recognises intent keywords (trending, hot, new, …) and returns sorted rounds.
    """
    entity_types = None
    if type:
        entity_types = [t.strip() for t in type.split(",") if t.strip()]
        valid = {"prompt", "agent", "proposal"}
        entity_types = [t for t in entity_types if t in valid]
        if not entity_types:
            entity_types = None

    # Check for intent keywords before hitting FTS
    q_lower = q.strip().lower()
    intent_order = _INTENT_SORT.get(q_lower)
    if intent_order and (entity_types is None or "prompt" in entity_types):
        results = await _intent_results(intent_order, limit, db)
        return {"query": q, "results": results}

    results = await asyncio.to_thread(hybrid_search, q, limit, entity_types)

    # Enrich proposals with prompt_id for linking
    proposal_ids = [r["entity_id"] for r in results if r["entity_type"] == "proposal"]
    if proposal_ids:
        placeholders = ",".join("?" * len(proposal_ids))
        cursor = await db.execute(
            f"SELECT id, prompt_id FROM proposals WHERE id IN ({placeholders})",
            proposal_ids,
        )
        rows = await cursor.fetchall()
        prompt_map = {r["id"]: r["prompt_id"] for r in rows}
        for r in results:
            if r["entity_type"] == "proposal":
                r["prompt_id"] = prompt_map.get(r["entity_id"])

    return {"query": q, "results": results}
