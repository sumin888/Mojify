from fastapi import Header, HTTPException, Depends
from core.database import get_db


def _extract_api_key(x_api_key: str = Header(default=None), authorization: str = Header(default=None)) -> str | None:
    """Extract API key from X-API-Key or Authorization: Bearer header."""
    if x_api_key:
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


async def require_agent(
    x_api_key: str = Header(default=None),
    authorization: str = Header(default=None),
    db=Depends(get_db),
) -> dict:
    """Dependency: validates API key (X-API-Key or Bearer) and returns the agent row."""
    api_key = _extract_api_key(x_api_key, authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Use X-API-Key or Authorization: Bearer.")
    cursor = await db.execute(
        "SELECT id, name FROM agents WHERE api_key = ?", (api_key,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return {"id": row["id"], "name": row["name"]}


async def optional_agent(
    x_api_key: str = Header(default=None),
    authorization: str = Header(default=None),
    db=Depends(get_db),
):
    """Dependency: returns agent dict if API key present, else None."""
    api_key = _extract_api_key(x_api_key, authorization)
    if not api_key:
        return None
    cursor = await db.execute(
        "SELECT id, name FROM agents WHERE api_key = ?", (api_key,)
    )
    row = await cursor.fetchone()
    return {"id": row["id"], "name": row["name"]} if row else None
