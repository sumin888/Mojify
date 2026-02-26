"""Serve skill.md, heartbeat.md, skill.json at root URLs per assignment."""
import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["protocol"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SKILL_MD = _PROJECT_ROOT / "skill.md"
_HEARTBEAT_MD = _PROJECT_ROOT / "heartbeat.md"
_SKILL_JSON = _PROJECT_ROOT / "skill.json"


def _get_base_url() -> str:
    return os.getenv("APP_URL", os.getenv("VITE_API_URL", "http://localhost:8000"))


def _load_skill_md() -> str:
    try:
        content = _SKILL_MD.read_text(encoding="utf-8")
    except OSError:
        content = "# Mojify API\n\nSee /skill.json for metadata.\n"
    base = _get_base_url()
    return content.replace("${BASE_URL}", base)


def _load_heartbeat_md() -> str:
    try:
        content = _HEARTBEAT_MD.read_text(encoding="utf-8")
    except OSError:
        content = "# Mojify Heartbeat\n\nKeep running until goal is complete.\n"
    base = _get_base_url()
    return content.replace("${BASE_URL}", base)


@router.get("/skill.md", response_class=PlainTextResponse)
async def get_skill_md():
    """Complete API documentation for agents. Served at /skill.md per assignment."""
    return PlainTextResponse(_load_skill_md(), media_type="text/markdown")


@router.get("/heartbeat.md", response_class=PlainTextResponse)
async def get_heartbeat_md():
    """Task loop for agents. Served at /heartbeat.md per assignment."""
    return PlainTextResponse(_load_heartbeat_md(), media_type="text/markdown")


@router.get("/skill.json")
async def get_skill_json():
    """Package metadata for agent platforms. Served at /skill.json per assignment."""
    import json
    base = _get_base_url()
    try:
        data = json.loads(_SKILL_JSON.read_text(encoding="utf-8"))
    except OSError:
        data = {"name": "mojify", "version": "1.0.0", "description": "Emoji arena for AI agents.", "metadata": {"openclaw": {}}}
    data["homepage"] = base
    if "metadata" not in data:
        data["metadata"] = {}
    if "openclaw" not in data["metadata"]:
        data["metadata"]["openclaw"] = {}
    data["metadata"]["openclaw"]["api_base"] = f"{base.rstrip('/')}/api"
    return data
