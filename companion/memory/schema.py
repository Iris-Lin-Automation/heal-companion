"""Memory types: what we keep for a long-term healing companion."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MemoryKind(str, Enum):
    identity = "identity"  # name, how to address, timezone
    preference = "preference"  # what comfort works, topics to avoid
    person = "person"  # friends / family / someone they're analyzing
    event = "event"  # episodic: went out with friends, interview...
    commitment = "commitment"  # real-life courage steps they said they'd try
    emotion_pattern = "emotion_pattern"  # triggers, recurring feelings
    win = "win"  # real-world courage moments to celebrate later
    boundary = "boundary"  # hard limits, sensitive topics


class MemoryItem(BaseModel):
    id: str
    kind: MemoryKind
    summary: str = Field(..., description="One-line durable fact, Chinese OK")
    details: str = ""
    people: list[str] = Field(default_factory=list)
    importance: int = Field(3, ge=1, le=5)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    last_seen_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    source: str = "chat"


class ExtractedMemories(BaseModel):
    items: list[MemoryItem] = Field(default_factory=list)
    journal_line: Optional[str] = Field(
        None, description="One diary sentence about today's chat, or null"
    )


class UserProfile(BaseModel):
    user_id: str
    display_name: str = ""
    preferred_address: str = "你"
    timezone: str = "Asia/Shanghai"
    comfort_notes: str = ""
    # first_meet / familiar / close；当前由聊天轮数推断，后续可开放给用户调节
    relationship_stage: str = "first_meet"
    # Auto-Tagging：tag → 累积权重，注入时取 Top-5
    preference_tags: dict[str, int] = Field(default_factory=dict)
    # 最近一轮粗情绪（供 Heartbeat / Bridge 使用）
    emotional_state: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


# What to remember (product rule of thumb)
REMEMBER_GUIDE = """
只持久化「以后还用得上」的信息：

1. identity —— 怎么称呼、作息、重要自我描述
2. preference —— 怎样安慰有效、讨厌被怎样对待
3. person —— 反复出现的人：关系、关键行为、用户对他们的感受
4. event —— 具体生活事件（和谁、做了什么、大概什么时候）
5. commitment —— 用户说要在现实里尝试的一小步
6. emotion_pattern —— 反复触发点（不是一次性情绪宣泄全文）
7. win —— 现实里已经做到的勇气瞬间
8. boundary —— 敏感话题与硬边界

不要存：一次性闲聊废话、完整聊天原文、模型自己的猜测当事实。
"""
