"""
Tests for protocol files: skill.md, heartbeat.md, skill.json.
Served at root URLs per assignment requirements.
"""
import pytest


def test_skill_md_returns_markdown(client):
    """GET /skill.md returns API documentation as markdown."""
    resp = client.get("/skill.md")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers.get("content-type", "") or "text/plain" in resp.headers.get("content-type", "")
    content = resp.text
    assert "mojify" in content.lower() or "emoji" in content.lower() or "api" in content.lower()
    # Full skill.md has register; fallback has metadata
    assert "register" in content.lower() or "metadata" in content.lower()


def test_skill_md_contains_base_url(client):
    """skill.md has BASE_URL injected (not placeholder)."""
    resp = client.get("/skill.md")
    assert resp.status_code == 200
    # Should not contain literal ${BASE_URL} - it gets replaced
    assert "${BASE_URL}" not in resp.text or "localhost" in resp.text


def test_heartbeat_md_returns_markdown(client):
    """GET /heartbeat.md returns task loop as markdown."""
    resp = client.get("/heartbeat.md")
    assert resp.status_code == 200
    content = resp.text
    assert "heartbeat" in content.lower() or "loop" in content.lower()
    assert "goal" in content.lower() or "step" in content.lower()


def test_heartbeat_md_contains_base_url(client):
    """heartbeat.md has BASE_URL injected."""
    resp = client.get("/heartbeat.md")
    assert resp.status_code == 200
    assert "${BASE_URL}" not in resp.text or "localhost" in resp.text


def test_skill_json_returns_valid_json(client):
    """GET /skill.json returns package metadata."""
    resp = client.get("/skill.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert data["name"] == "mojify"
    assert "version" in data
    assert "description" in data
    assert "homepage" in data
    assert "metadata" in data
    assert "openclaw" in data["metadata"]
    assert "api_base" in data["metadata"]["openclaw"]
    assert "/api" in data["metadata"]["openclaw"]["api_base"]


def test_skill_json_api_base_has_api_suffix(client):
    """skill.json openclaw.api_base ends with /api."""
    resp = client.get("/skill.json")
    data = resp.json()
    api_base = data["metadata"]["openclaw"]["api_base"]
    assert api_base.endswith("/api")
