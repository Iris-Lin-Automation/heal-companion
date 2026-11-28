"""Low-density proactive check-ins based on memory + recent chat + journal."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from companion.persona.loader import PersonaManager
from companion.memory.schema import MemoryKind
from companion.memory.store import MemoryStore
from companion.bridge.curated import pick_for_user

_mgr = PersonaManager()


def _today_journal(store: MemoryStore) -> str:
    reader = getattr(store, "today_journal", None)
    if callable(reader):
        return str(reader() or "")
    path = store.dir / "journal" / f"{date.today().isoformat()}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _format_recent_chat(store: MemoryStore, n: int = 16) -> str:
    """Pull recent turns so proactive messages can echo past topics."""
    rows = store.recent_chat(n)
    if not rows:
        return ""
    lines: list[str] = []
    for r in rows:
        role = "用户" if r.get("role") == "user" else "heal"
        content = str(r.get("content") or "").strip().replace("\n", " ")
        if not content:
            continue
        if len(content) > 120:
            content = content[:117] + "…"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def craft_checkin(
    client: Any,
    model: str,
    store: MemoryStore,
    companion_name: str = "软软",
    env_context: dict | None = None,
) -> str:
    memories = store.list_memories()
    commitments = [m for m in memories if m.kind == MemoryKind.commitment][:3]
    events = [m for m in memories if m.kind == MemoryKind.event][:3]
    wins = [m for m in memories if m.kind == MemoryKind.win][:2]
    prefs = [m for m in memories if m.kind == MemoryKind.preference][:2]
    emotions = [m for m in memories if m.kind == MemoryKind.emotion_pattern][:2]
    recent_chat = _format_recent_chat(store, 16)
    journal = _today_journal(store)

    # 尝试拿到今日现实桥梁内容（每天最多一次）
    bridge_item = pick_for_user(store)

    # 免费天气（Open-Meteo，无需 Key）— 优先于静态内容池
    weather_hint = ""
    try:
        from companion.bridge.weather import fetch_weather

        weather = fetch_weather()
        if weather:
            weather_hint = (
                f"\n\n今日真实天气（可自然融入，不要念成播报）：\n「{weather.care_line}」"
            )
    except Exception:  # noqa: BLE001
        weather = None

    bridge_hint = ""
    if bridge_item:
        bridge_hint = (
            f"\n\n可选：今天有一条现实内容可以自然分享给用户（不是AI编的，来自外部信息池）：\n"
            f"「{bridge_item.message}」\n如果对话走向合适，可以把它自然地嵌进去；不合适就跳过，不要强行插入。"
        )

    has_hooks = bool(
        commitments or events or wins or prefs or emotions or recent_chat or journal
    )

    # 完全没有过往线索时，才退回天气/桥梁/通用开场
    if not has_hooks:
        if weather:
            return weather.care_line
        if bridge_item:
            return bridge_item.message
        return (
            f"嗨，我是{companion_name}。今天若你愿意，跟我说一件现实里发生的小事就好——"
            "我在，不催你。"
        )

    bullet: list[str] = []
    for m in commitments:
        bullet.append(f"待跟进的小承诺: {m.summary}")
    for m in events:
        bullet.append(f"近期事件: {m.summary}")
    for m in wins:
        bullet.append(f"可庆祝的勇气: {m.summary}")
    for m in prefs:
        bullet.append(f"偏好: {m.summary}")
    for m in emotions:
        bullet.append(f"情绪线索: {m.summary}")

    persona_id = os.getenv("PERSONA_ID", "older_friend")
    base_prompt, _name = _mgr.build_system_prompt(
        persona_id=persona_id,
        name_override=companion_name or None,
        env_context=env_context,
        relationship_stage=store.relationship_stage(),
    )

    prompt = f"""{base_prompt}

请写一条「低密度主动关心」短消息（2–4句），给用户发过去：{weather_hint}{bridge_hint}
- 优先根据「近期对话」里聊过的具体事开口，证明你记得（点到为止，不要复述整段）
- 也可轻轻接上长期记忆里的承诺/事件/情绪
- 轻、暖、不粘人；不要连环追问，不要像系统通知
- 若有 commitment，温柔问一句进展，不施压
- 若有 win，轻轻庆祝
- 结尾可留一个可选的小开口，而不是命令
- 不要自称 AI，不要写免责声明

已知记忆要点：
{chr(10).join('- ' + b for b in bullet) if bullet else '（暂无结构化记忆）'}

近期对话摘录：
{recent_chat or '（暂无）'}

今日日记片段：
{journal or '（暂无）'}
"""
    resp = client.chat.completions.create(
        model=model,
        temperature=0.65,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": "请根据过往聊过的事，生成一条主动关心消息。",
            },
        ],
    )
    return (resp.choices[0].message.content or "").strip()
