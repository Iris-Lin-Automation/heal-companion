"""Chat loop: recall → respond → extract memories.

架构说明
--------
- System Prompt 由 PersonaManager.build_system_prompt() 统一生成，
  包含角色人设 + 三层记忆上下文（档案 / 召回 / 偏好标签）+ 实时环境。
- loop.py 只负责：取数据 → 组装 messages → 调 LLM → 持久化。
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any, Optional

from companion.memory.extract import extract_and_save
from companion.memory.store import MemoryStore
from companion.persona.loader import PersonaManager
from companion.tts.emotion import ensure_emotion_prefix, resolve_emotion, strip_emotion_tag

# ── 人设默认值（可通过 .env 覆盖） ──
DEFAULT_PERSONA_ID: str = os.getenv("PERSONA_ID", "older_friend")

_manager = PersonaManager()


# ════════════════════════════════════════════════════════
#  消息组装
# ════════════════════════════════════════════════════════

def build_messages(
    store: MemoryStore,
    user_text: str,
    companion_name: Optional[str] = None,
    persona_id: str = DEFAULT_PERSONA_ID,
    history_override: Optional[list[dict[str, str]]] = None,
    env_context: Optional[dict[str, Any]] = None,
) -> tuple[list[dict[str, str]], str]:
    """返回 ``(messages, resolved_name)``。"""
    profile = store.load_profile()
    recalled = store.recall(user_text, limit=8)

    system_prompt, name = _manager.build_system_prompt(
        persona_id=persona_id,
        name_override=companion_name or None,
        user_profile=profile,
        recalled_memories=recalled,
        preference_tags=store.top_preference_tags(5),
        env_context=env_context,
        relationship_stage=store.relationship_stage(),
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    history = history_override
    if history is None:
        history = [
            {"role": t["role"], "content": t["content"]}
            for t in store.recent_chat(10)
            if t["role"] in {"user", "assistant"}
        ]
    for turn in history[-10:]:
        role = turn.get("role")
        if role not in {"user", "assistant"}:
            continue
        messages.append({"role": role, "content": turn.get("content") or ""})

    messages.append({"role": "user", "content": user_text})
    return messages, name


# ════════════════════════════════════════════════════════
#  对话接口
# ════════════════════════════════════════════════════════

def chat_once(
    client: Any,
    model: str,
    store: MemoryStore,
    user_text: str,
    companion_name: Optional[str] = None,
    persona_id: str = DEFAULT_PERSONA_ID,
    extract: bool = True,
    env_context: Optional[dict[str, Any]] = None,
) -> str:
    messages, _name = build_messages(
        store, user_text, companion_name, persona_id, env_context=env_context
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=messages,
    )
    reply = ensure_emotion_prefix(
        (resp.choices[0].message.content or "").strip(), user_text
    )
    reply_clean = strip_emotion_tag(reply)
    store.append_chat_log("user", user_text)
    store.append_chat_log("assistant", reply_clean)
    if extract:
        extract_and_save(client, model, store, user_text, reply_clean)
    return reply


def chat_stream(
    client: Any,
    model: str,
    store: MemoryStore,
    user_text: str,
    companion_name: Optional[str] = None,
    persona_id: str = DEFAULT_PERSONA_ID,
    extract: bool = True,
    history_override: Optional[list[dict[str, str]]] = None,
    env_context: Optional[dict[str, Any]] = None,
) -> Iterator[str]:
    """流式输出 token；流结束后持久化对话并异步提取记忆。"""
    messages, _name = build_messages(
        store,
        user_text,
        companion_name,
        persona_id,
        history_override,
        env_context=env_context,
    )
    stream = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=messages,
        stream=True,
    )
    chunks: list[str] = []
    for event in stream:
        delta = event.choices[0].delta.content or ""
        if delta:
            chunks.append(delta)
            yield delta
    reply = "".join(chunks).strip()
    reply_clean = strip_emotion_tag(reply)
    store.append_chat_log("user", user_text)
    store.append_chat_log("assistant", reply_clean)
    if extract and reply_clean:
        extract_and_save(client, model, store, user_text, reply_clean)


def resolve_reply_emotion(reply_text: str, user_text: str = "") -> str:
    """供 API 在 SSE done 事件里带回，前端 TTS 显式传 emotion。"""
    emotion, _ = resolve_emotion(reply_text, user_text)
    return emotion
