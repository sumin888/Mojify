"""
Tests for the admin API endpoints.
Login/logout, prompt listing, open/close with auth guard checks.
"""
import pytest

_CREDS = {"username": "mojify", "password": "yfijom888"}


def _login(client) -> str:
    """Return a valid admin token."""
    resp = client.post("/api/admin/login", json=_CREDS)
    assert resp.status_code == 200
    return resp.json()["token"]


def _auth(token: str) -> dict:
    return {"x-admin-token": token}


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_admin_login_success(client):
    resp = client.post("/api/admin/login", json=_CREDS)
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert len(data["token"]) == 64  # 32 bytes hex


def test_admin_login_wrong_password(client):
    resp = client.post("/api/admin/login", json={"username": "mojify", "password": "wrong"})
    assert resp.status_code == 401


def test_admin_login_wrong_username(client):
    resp = client.post("/api/admin/login", json={"username": "hacker", "password": "yfijom888"})
    assert resp.status_code == 401


def test_admin_no_token_returns_401(client):
    resp = client.get("/api/admin/prompts")
    assert resp.status_code == 401


def test_admin_invalid_token_returns_401(client):
    resp = client.get("/api/admin/prompts", headers={"x-admin-token": "notavalidtoken"})
    assert resp.status_code == 401


def test_admin_logout_invalidates_token(client):
    token = _login(client)
    # Works before logout
    assert client.get("/api/admin/prompts", headers=_auth(token)).status_code == 200
    # Logout
    resp = client.post("/api/admin/logout", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    # Token rejected after logout
    assert client.get("/api/admin/prompts", headers=_auth(token)).status_code == 401


# ── Prompt listing ─────────────────────────────────────────────────────────────

def test_admin_list_prompts_empty(client):
    token = _login(client)
    resp = client.get("/api/admin/prompts", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_admin_list_prompts_with_data(client):
    token = _login(client)
    client.post("/api/prompts/", json={"title": "Round A", "context_text": "ctx", "media_type": "text"})
    client.post("/api/prompts/", json={"title": "Round B", "context_text": "ctx", "media_type": "text"})
    resp = client.get("/api/admin/prompts", headers=_auth(token))
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert "Round A" in titles
    assert "Round B" in titles


def test_admin_list_prompts_includes_proposal_count(client):
    token = _login(client)
    reg = client.post("/api/agents/register", json={"name": "AdminTestAgent"})
    agent_id = reg.json()["id"]
    api_key = reg.json()["api_key"]

    prompt = client.post("/api/prompts/", json={"title": "Counted", "context_text": "x", "media_type": "text"})
    prompt_id = prompt.json()["id"]

    client.post(
        f"/api/prompts/{prompt_id}/proposals",
        json={"agent_id": agent_id, "emoji_string": "😊", "rationale": "test"},
        headers={"x-api-key": api_key},
    )

    resp = client.get("/api/admin/prompts", headers=_auth(token))
    found = next(p for p in resp.json() if p["id"] == prompt_id)
    assert found["proposal_count"] == 1


# ── Open / Close ───────────────────────────────────────────────────────────────

def test_admin_close_prompt(client):
    token = _login(client)
    create = client.post("/api/prompts/", json={"title": "Close me", "context_text": "x", "media_type": "text"})
    prompt_id = create.json()["id"]
    assert create.json()["status"] == "open"

    resp = client.patch(f"/api/admin/prompts/{prompt_id}/close", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_admin_open_prompt(client):
    token = _login(client)
    create = client.post("/api/prompts/", json={"title": "Open me", "context_text": "x", "media_type": "text"})
    prompt_id = create.json()["id"]

    client.patch(f"/api/admin/prompts/{prompt_id}/close", headers=_auth(token))
    resp = client.patch(f"/api/admin/prompts/{prompt_id}/open", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_admin_close_not_found(client):
    token = _login(client)
    resp = client.patch("/api/admin/prompts/nonexistent-uuid/close", headers=_auth(token))
    assert resp.status_code == 404


def test_admin_open_not_found(client):
    token = _login(client)
    resp = client.patch("/api/admin/prompts/nonexistent-uuid/open", headers=_auth(token))
    assert resp.status_code == 404


def test_admin_close_requires_auth(client):
    create = client.post("/api/prompts/", json={"title": "No auth", "context_text": "x", "media_type": "text"})
    prompt_id = create.json()["id"]
    resp = client.patch(f"/api/admin/prompts/{prompt_id}/close")
    assert resp.status_code == 401
