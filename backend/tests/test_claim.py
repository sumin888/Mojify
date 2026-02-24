"""
Tests for agent claiming: claim_url in registration, POST /api/agents/claim/{token}.
"""
import pytest


def test_register_returns_claim_url(client):
    """Registration response includes claim_url."""
    resp = client.post("/api/agents/register", json={"name": "ClaimTestAgent"})
    assert resp.status_code == 201
    data = resp.json()
    assert "claim_url" in data
    assert "claim" in data["claim_url"]
    assert data["claim_url"].endswith("/claim/") or "/claim/" in data["claim_url"]


def test_register_returns_skill_md(client):
    """Registration response includes skill_md for the agent."""
    resp = client.post("/api/agents/register", json={"name": "SkillTestAgent"})
    assert resp.status_code == 201
    data = resp.json()
    assert "skill_md" in data
    assert len(data["skill_md"]) > 0
    # Full skill has api/register; fallback has mojify/api
    assert "mojify" in data["skill_md"].lower() or "api" in data["skill_md"].lower()


def test_claim_agent_success(client):
    """POST /api/agents/claim/{token} marks agent as claimed."""
    reg = client.post("/api/agents/register", json={"name": "ToBeClaimed"})
    assert reg.status_code == 201
    claim_url = reg.json()["claim_url"]
    # Extract token from claim_url (e.g. http://localhost:5173/claim/TOKEN)
    token = claim_url.rstrip("/").split("/claim/")[-1]
    assert token

    resp = client.post(f"/api/agents/claim/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert data.get("agent_name") == "ToBeClaimed"


def test_claim_agent_invalid_token(client):
    """Claim with invalid token returns 404."""
    resp = client.post("/api/agents/claim/invalid-nonexistent-token")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_claim_agent_idempotent(client):
    """Claiming same agent twice: first succeeds, second returns 404 (token cleared)."""
    reg = client.post("/api/agents/register", json={"name": "DoubleClaim"})
    token = reg.json()["claim_url"].rstrip("/").split("/claim/")[-1]

    r1 = client.post(f"/api/agents/claim/{token}")
    assert r1.status_code == 200

    r2 = client.post(f"/api/agents/claim/{token}")
    assert r2.status_code == 404  # Token was cleared after first claim


def test_register_with_description(client):
    """Registration accepts optional description."""
    resp = client.post(
        "/api/agents/register",
        json={"name": "DescribedAgent", "description": "An agent that describes things"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "DescribedAgent"
