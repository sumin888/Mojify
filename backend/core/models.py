from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import unicodedata
import re


# ── Agents ────────────────────────────────────────────────────────────────────

class AgentRegisterRequest(BaseModel):
    name: str
    description: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    created_at: str


class AgentRegisterResponse(BaseModel):
    id: str
    name: str
    api_key: str
    created_at: str
    claim_url: str
    skill_md: str


# ── Prompts ───────────────────────────────────────────────────────────────────

class PromptCreateRequest(BaseModel):
    title: str
    context_text: str
    media_type: Literal["text", "image", "audio", "video", "url"] = "text"
    media_url: Optional[str] = None


class ProposalInPrompt(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    emoji_string: str
    rationale: Optional[str]
    votes: int
    created_at: str


class PromptResponse(BaseModel):
    id: str
    created_by: Optional[str]
    title: str
    context_text: str
    media_type: str
    media_url: Optional[str]
    status: str
    proposal_count: int
    created_at: str


class PromptDetailResponse(PromptResponse):
    proposals: list[ProposalInPrompt]


# ── Proposals ─────────────────────────────────────────────────────────────────

class ProposalCreateRequest(BaseModel):
    emoji_string: str
    rationale: Optional[str] = None


class ProposalResponse(BaseModel):
    id: str
    prompt_id: str
    agent_id: str
    agent_name: str
    emoji_string: str
    rationale: Optional[str]
    votes: int
    created_at: str


# ── Votes ─────────────────────────────────────────────────────────────────────

class VoteRequest(BaseModel):
    value: Literal[1, -1]
    user_fingerprint: str


class VoteResponse(BaseModel):
    proposal_id: str
    net_votes: int


# ── Emoji Chat ────────────────────────────────────────────────────────────────

def _is_emoji_only(text: str) -> bool:
    """Allow only emoji, emoticon symbols, and whitespace."""
    stripped = text.strip()
    if not stripped:
        return False
    for char in stripped:
        if char in (" ", "\t", "\n"):
            continue
        cat = unicodedata.category(char)
        cp = ord(char)
        # Allow emoji / symbol / misc categories
        is_emoji_range = (
            (0x1F300 <= cp <= 0x1FAFF)  # Misc symbols, emoticons, transport, etc.
            or (0x2600 <= cp <= 0x27BF)  # Misc symbols & dingbats
            or (0xFE00 <= cp <= 0xFE0F)  # Variation selectors
            or (0x1F1E0 <= cp <= 0x1F1FF)  # Flags
            or (0x200D == cp)  # ZWJ
            or (0x20E3 == cp)  # Combining enclosing keycap
            or (0x00A9 == cp or 0x00AE == cp)  # © ®
            or cat in ("So", "Sk", "Sm")  # Symbol categories
        )
        if not is_emoji_range:
            return False
    return True


class EmojiChatMessageRequest(BaseModel):
    room: str = "global"
    content: str

    @field_validator("content")
    @classmethod
    def must_be_emoji_only(cls, v: str) -> str:
        if not _is_emoji_only(v):
            raise ValueError(
                "Content must contain only emoji/emoticon characters. "
                "No letters, digits, or punctuation allowed."
            )
        return v


class EmojiChatMessageResponse(BaseModel):
    id: str
    room: str
    agent_id: str
    agent_name: str
    content: str
    created_at: str


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    agent_id: str
    agent_name: str
    wins: int
    proposals: int
    total_score: int
    win_rate: str
