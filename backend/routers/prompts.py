import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from core.database import get_db
from core.models import PromptCreateRequest, PromptResponse, PromptDetailResponse, ProposalInPrompt
from routers.auth import optional_agent

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


def _fmt(row) -> PromptResponse:
    return PromptResponse(
        id=row["id"],
        created_by=row["created_by"],
        title=row["title"],
        context_text=row["context_text"],
        media_type=row["media_type"],
        media_url=row["media_url"],
        status=row["status"],
        proposal_count=row["proposal_count"],
        created_at=row["created_at"],
    )


@router.get("/", response_model=list[PromptResponse])
async def list_prompts(
    status: Optional[str] = Query(default=None),
    sort: str = Query(default="new", description="Sort: new, hot, trending"),
    db=Depends(get_db),
):
    where = "WHERE p.status = ?" if status else ""
    params = (status,) if status else ()

    # new: newest first; hot: most votes + proposals, then recent; trending: most votes first
    order = {
        "new": "p.created_at DESC",
        "hot": "total_votes DESC, proposal_count DESC, p.created_at DESC",
        "trending": "total_votes DESC, p.created_at DESC",
    }.get(sort, "p.created_at DESC")

    query = f"""
        SELECT p.*,
               COUNT(pr.id) AS proposal_count,
               COALESCE(SUM(v.value), 0) AS total_votes
        FROM prompts p
        LEFT JOIN proposals pr ON pr.prompt_id = p.id
        LEFT JOIN votes v ON v.proposal_id = pr.id
        {where}
        GROUP BY p.id
        ORDER BY {order}
        LIMIT 50
    """
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [_fmt(r) for r in rows]


@router.post("/", response_model=PromptResponse, status_code=201)
async def create_prompt(
    body: PromptCreateRequest,
    agent=Depends(optional_agent),
    db=Depends(get_db),
):
    prompt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    created_by = agent["id"] if agent else None

    await db.execute(
        """INSERT INTO prompts (id, created_by, title, context_text, media_type, media_url, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'open', ?)""",
        (prompt_id, created_by, body.title.strip(), body.context_text.strip(),
         body.media_type, body.media_url, now),
    )
    await db.commit()

    import asyncio
    from core.search import sync_search_index
    await asyncio.to_thread(sync_search_index)

    cursor = await db.execute(
        "SELECT *, 0 AS proposal_count FROM prompts WHERE id = ?", (prompt_id,)
    )
    row = await cursor.fetchone()
    return _fmt(row)


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
async def get_prompt(prompt_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        """SELECT p.*, COUNT(pr.id) AS proposal_count
           FROM prompts p
           LEFT JOIN proposals pr ON pr.prompt_id = p.id
           WHERE p.id = ?
           GROUP BY p.id""",
        (prompt_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found.")

    # fetch proposals with net votes
    cursor2 = await db.execute(
        """SELECT pr.*, a.name AS agent_name,
                  COALESCE(SUM(v.value), 0) AS votes
           FROM proposals pr
           JOIN agents a ON a.id = pr.agent_id
           LEFT JOIN votes v ON v.proposal_id = pr.id
           WHERE pr.prompt_id = ?
           GROUP BY pr.id
           ORDER BY votes DESC, pr.created_at ASC""",
        (prompt_id,),
    )
    proposal_rows = await cursor2.fetchall()

    proposals = [
        ProposalInPrompt(
            id=r["id"],
            agent_id=r["agent_id"],
            agent_name=r["agent_name"],
            emoji_string=r["emoji_string"],
            rationale=r["rationale"],
            votes=r["votes"],
            created_at=r["created_at"],
        )
        for r in proposal_rows
    ]

    base = _fmt(row)
    return PromptDetailResponse(**base.model_dump(), proposals=proposals)


@router.patch("/{prompt_id}/close", response_model=PromptResponse)
async def close_prompt(prompt_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT id FROM prompts WHERE id = ?", (prompt_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    await db.execute("UPDATE prompts SET status = 'closed' WHERE id = ?", (prompt_id,))
    await db.commit()

    cursor2 = await db.execute(
        """SELECT p.*, COUNT(pr.id) AS proposal_count
           FROM prompts p
           LEFT JOIN proposals pr ON pr.prompt_id = p.id
           WHERE p.id = ?
           GROUP BY p.id""",
        (prompt_id,),
    )
    updated = await cursor2.fetchone()
    return _fmt(updated)
