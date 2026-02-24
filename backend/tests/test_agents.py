"""
Unit tests for agents API endpoints.
"""
import pytest


def test_register_agent(client):
    """Register a new agent and verify response."""
    resp = client.post(
        "/api/agents/register",
        json={"name": "TestAgent"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestAgent"
    assert "id" in data
    assert "api_key" in data
    assert len(data["api_key"]) == 64  # 32 bytes hex
    assert "created_at" in data
    assert "claim_url" in data
    assert "skill_md" in data


def test_register_agent_duplicate_name(client):
    """Registering with duplicate name returns 409."""
    client.post("/api/agents/register", json={"name": "DupAgent"})
    resp = client.post("/api/agents/register", json={"name": "DupAgent"})
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


def test_list_agents_empty(client):
    """List agents when none exist."""
    resp = client.get("/api/agents/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_agents_after_register(client):
    """List agents returns registered agents."""
    r1 = client.post("/api/agents/register", json={"name": "AgentA"})
    r2 = client.post("/api/agents/register", json={"name": "AgentB"})
    resp = client.get("/api/agents/")
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert "AgentA" in names
    assert "AgentB" in names


def test_get_agent(client):
    """Get agent by ID."""
    reg = client.post("/api/agents/register", json={"name": "GetMe"})
    agent_id = reg.json()["id"]
    resp = client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "GetMe"
    assert resp.json()["id"] == agent_id


def test_get_agent_not_found(client):
    """Get non-existent agent returns 404."""
    resp = client.get("/api/agents/nonexistent-uuid")
    assert resp.status_code == 404
