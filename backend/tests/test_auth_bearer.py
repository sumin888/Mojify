"""
Tests for Bearer token authentication.
Auth supports both X-API-Key and Authorization: Bearer.
"""
import pytest


@pytest.fixture
def agent_and_prompt(client):
    """Create an agent and a prompt for auth tests."""
    reg = client.post("/api/agents/register", json={"name": "BearerTestAgent"})
    agent = reg.json()
    prompt = client.post(
        "/api/prompts/",
        json={"title": "Auth test", "context_text": "test", "media_type": "text"},
    ).json()
    return {"agent": agent, "prompt": prompt}


def test_proposal_with_x_api_key(client, agent_and_prompt):
    """Submit proposal with X-API-Key header (existing auth)."""
    agent = agent_and_prompt["agent"]
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "😀", "rationale": "Test"},
    )
    assert resp.status_code == 201


def test_proposal_with_bearer_token(client, agent_and_prompt):
    """Submit proposal with Authorization: Bearer header."""
    agent = agent_and_prompt["agent"]
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"Authorization": f"Bearer {agent['api_key']}"},
        json={"emoji_string": "🎉", "rationale": "Bearer test"},
    )
    assert resp.status_code == 201


def test_proposal_with_bearer_token_lowercase(client, agent_and_prompt):
    """Bearer header is case-insensitive (bearer vs Bearer)."""
    agent = agent_and_prompt["agent"]
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"Authorization": f"bearer {agent['api_key']}"},
        json={"emoji_string": "✨", "rationale": "Lowercase bearer"},
    )
    assert resp.status_code == 201


def test_emoji_chat_with_bearer_token(client, agent_and_prompt):
    """Emoji chat accepts Bearer token."""
    agent = agent_and_prompt["agent"]
    resp = client.post(
        "/api/emoji-chat/",
        headers={"Authorization": f"Bearer {agent['api_key']}"},
        json={"content": "😀", "room": "global"},
    )
    assert resp.status_code == 201


def test_missing_auth_returns_401(client, agent_and_prompt):
    """Request without API key returns 401."""
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code in (401, 422)  # 401 from our auth or 422 from FastAPI


def test_invalid_bearer_returns_401(client, agent_and_prompt):
    """Invalid Bearer token returns 401."""
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"Authorization": "Bearer invalid-fake-key"},
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code == 401
