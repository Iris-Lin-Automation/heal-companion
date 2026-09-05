"""Extract durable memories from a chat turn via LLM JSON."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from companion.memory.schema import ExtractedMemories, MemoryItem, REMEMBER_GUIDE
from companion.memory.store import MemoryStore


EXTRACT_SYSTEM = f"""你是记忆整理器，不是聊天角色。
根据最近对话，只提取值得长期保存的事实，并做 Auto-Tagging。
{REMEMBER_GUIDE}

输出严格 JSON，匹配 schema：
{{
  "items": [
    {{
      "id": "可空",
      "kind": "identity|preference|person|event|commitment|emotion_pattern|win|boundary",
      "summary": "一句话事实",
      "details": "可选补充",
      "people": ["人名"],
      "importance": 1到5,
      "source": "chat"
    }}
  ],
  "journal_line": "今天对话的一句日记，可 null",
  "preference_tags": ["喜欢简短回复", "最近焦虑", "讨厌被催促"],
  "emotional_state": "焦虑|平静|开心|疲惫|难过|null"
}}

preference_tags 规则：短中文短语，反映沟通偏好或近期状态；本轮无明显信号则空数组。
emotional_state：本轮用户主导情绪，不确定则 null。
没有新信息时 items 为空数组。不要编造。
"""


def extract_and_save(client: Any, model: str, store: MemoryStore, user_text: str, assistant_text: str) -> ExtractedMemories:
    recent = store.recent_chat(8)
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    transcript += f"\nuser: {user_text}\nassistant: {assistant_text}"

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": transcript},
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    # normalize ids
    items = []
    for it in data.get("items") or []:
        it["id"] = it.get("id") or uuid.uuid4().hex[:12]
        it.setdefault("source", "chat")
        it.setdefault("people", [])
        it.setdefault("details", "")
        it.setdefault("importance", 3)
        now = datetime.now().isoformat(timespec="seconds")
        if not it.get("created_at"):
            it["created_at"] = now
        if not it.get("last_seen_at"):
            it["last_seen_at"] = now
        items.append(MemoryItem.model_validate(it))
    extracted = ExtractedMemories(items=items, journal_line=data.get("journal_line"))

    for item in extracted.items:
        store.upsert(item)
    if extracted.journal_line:
        store.append_journal(extracted.journal_line)

    # Auto-Tagging：权重累积 + 近期情绪
    tags = [str(t).strip() for t in (data.get("preference_tags") or []) if str(t).strip()]
    emo = data.get("emotional_state")
    emo_str = str(emo).strip() if emo and str(emo).lower() not in {"null", "none", ""} else ""
    if tags or emo_str:
        store.merge_preference_tags(tags, emo_str)

    # Soft-update profile name if identity mentions 称呼
    profile = store.load_profile()
    for item in extracted.items:
        if item.kind.value == "identity" and "叫" in item.summary and not profile.display_name:
            profile.display_name = item.summary[:40]
            store.save_profile(profile)
            break
    return extracted
