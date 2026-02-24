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
