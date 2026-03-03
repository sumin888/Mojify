"""
Unit tests for prompts API endpoints.
"""
import pytest


def test_create_prompt(client):
    """Create a prompt anonymously."""
    resp = client.post(
        "/api/prompts/",
        json={
            "title": "Test prompt",
            "context_text": "Some context",
            "media_type": "text",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test prompt"
    assert data["context_text"] == "Some context"
    assert data["status"] == "open"
    assert data["proposal_count"] == 0
    assert "id" in data


def test_list_prompts_empty(client):
    """List prompts when none exist."""
    resp = client.get("/api/prompts/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_prompts_with_status(client):
    """List prompts filtered by status."""
    client.post(
        "/api/prompts/",
        json={"title": "Open", "context_text": "x", "media_type": "text"},
    )
    resp = client.get("/api/prompts/?status=open")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_prompt(client):
    """Get prompt by ID with proposals."""
    create = client.post(
        "/api/prompts/",
        json={"title": "Get me", "context_text": "ctx", "media_type": "text"},
    )
    prompt_id = create.json()["id"]
    resp = client.get(f"/api/prompts/{prompt_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get me"
    assert "proposals" in resp.json()
    assert resp.json()["proposals"] == []


def test_get_prompt_not_found(client):
    """Get non-existent prompt returns 404."""
    resp = client.get("/api/prompts/nonexistent-uuid")
    assert resp.status_code == 404


def test_get_prompt_unauthenticated_includes_proposals(client):
    """GET /api/prompts/{id} works with no auth and returns proposals."""
    reg = client.post("/api/agents/register", json={"name": "ReadTestAgent"})
    api_key = reg.json()["api_key"]
    prompt = client.post("/api/prompts/", json={"title": "Read me", "context_text": "x", "media_type": "text"})
    prompt_id = prompt.json()["id"]
    client.post(
        f"/api/prompts/{prompt_id}/proposals",
        json={"emoji_string": "😊", "rationale": "happy"},
        headers={"x-api-key": api_key},
    )

    # No auth header at all
    resp = client.get(f"/api/prompts/{prompt_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == prompt_id
    assert len(data["proposals"]) == 1
    assert data["proposals"][0]["emoji_string"] == "😊"


def test_close_prompt(client):
    """Close a prompt."""
    create = client.post(
        "/api/prompts/",
        json={"title": "To close", "context_text": "x", "media_type": "text"},
    )
    prompt_id = create.json()["id"]
    resp = client.patch(f"/api/prompts/{prompt_id}/close")
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_close_prompt_not_found(client):
    """Close non-existent prompt returns 404."""
    resp = client.patch("/api/prompts/nonexistent-uuid/close")
    assert resp.status_code == 404


def test_list_prompts_sort_all(client):
    """sort=all returns open rounds first, then closed, ordered by date."""
    r1 = client.post("/api/prompts/", json={"title": "Open round", "context_text": "x", "media_type": "text"})
    r2 = client.post("/api/prompts/", json={"title": "Closed round", "context_text": "y", "media_type": "text"})
    client.patch(f"/api/prompts/{r2.json()['id']}/close")

    resp = client.get("/api/prompts/", params={"sort": "all"})
    assert resp.status_code == 200
    results = resp.json()
    titles = [p["title"] for p in results]
    assert "Open round" in titles
    assert "Closed round" in titles
    # Open round should appear before closed round
    assert titles.index("Open round") < titles.index("Closed round")


def test_list_prompts_sort_all_empty(client):
    """sort=all with no prompts returns empty list."""
    resp = client.get("/api/prompts/", params={"sort": "all"})
    assert resp.status_code == 200
    assert resp.json() == []
