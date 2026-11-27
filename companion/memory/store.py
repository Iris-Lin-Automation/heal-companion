"""File-based memory store (OpenClaw-style: human-readable markdown + JSON index)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path

from companion.memory.schema import MemoryItem, MemoryKind, UserProfile

ROOT = Path(__file__).resolve().parents[2] / "data" / "users"


def _safe_id(user_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id)[:64] or "default"


class MemoryStore:
    def __init__(self, user_id: str = "default") -> None:
        self.user_id = _safe_id(user_id)
        self.dir = ROOT / self.user_id
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "journal").mkdir(exist_ok=True)
        self.memories_path = self.dir / "memories.json"
        self.profile_path = self.dir / "profile.json"
        self.user_md = self.dir / "USER.md"
        self.memory_md = self.dir / "MEMORY.md"
        if not self.memories_path.exists():
            self._write_json(self.memories_path, [])
        if not self.profile_path.exists():
            self.save_profile(UserProfile(user_id=self.user_id))
        self._sync_markdown()

    @staticmethod
    def _write_json(path: Path, data) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_profile(self) -> UserProfile:
        return UserProfile.model_validate_json(self.profile_path.read_text(encoding="utf-8"))

    def save_profile(self, profile: UserProfile) -> None:
        self.profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        self._sync_markdown()

    def merge_preference_tags(self, new_tags: list[str], emotional_state: str = "") -> list[str]:
        """PRD Auto-Tagging：重复出现权重 +1，保留 Top-20，返回注入用 Top-5。"""
        profile = self.load_profile()
        tags = dict(profile.preference_tags or {})
        for raw in new_tags or []:
            tag = (raw or "").strip()
            if not tag or len(tag) > 24:
                continue
            tags[tag] = int(tags.get(tag, 0)) + 1
        # 截断 Top-20
        ranked = sorted(tags.items(), key=lambda x: (-x[1], x[0]))[:20]
        profile.preference_tags = dict(ranked)
        if (emotional_state or "").strip():
            profile.emotional_state = emotional_state.strip()[:32]
        self.save_profile(profile)
        return [t for t, _ in ranked[:5]]

    def top_preference_tags(self, n: int = 5) -> list[str]:
        tags = (self.load_profile().preference_tags or {})
        ranked = sorted(tags.items(), key=lambda x: (-x[1], x[0]))
        return [t for t, _ in ranked[:n]]

    def list_memories(self) -> list[MemoryItem]:
        raw = json.loads(self.memories_path.read_text(encoding="utf-8"))
        return [MemoryItem.model_validate(x) for x in raw]

    def save_memories(self, items: list[MemoryItem]) -> None:
        self._write_json(self.memories_path, [i.model_dump() for i in items])
        self._sync_markdown()

    def upsert(self, item: MemoryItem) -> MemoryItem:
        items = self.list_memories()
        # Dedup by same kind + similar summary prefix
        for i, old in enumerate(items):
            if old.kind == item.kind and (
                old.summary == item.summary or old.summary in item.summary or item.summary in old.summary
            ):
                merged = old.model_copy(
                    update={
                        "summary": item.summary if len(item.summary) >= len(old.summary) else old.summary,
                        "details": item.details or old.details,
                        "people": sorted(set(old.people + item.people)),
                        "importance": max(old.importance, item.importance),
                        "last_seen_at": datetime.now().isoformat(timespec="seconds"),
                    }
                )
                items[i] = merged
                self.save_memories(items)
                return merged
        if not item.id:
            item = item.model_copy(update={"id": uuid.uuid4().hex[:12]})
        items.append(item)
        self.save_memories(items)
        return item

    def get_memory(self, memory_id: str) -> MemoryItem | None:
        mid = (memory_id or "").strip()
        if not mid:
            return None
        for m in self.list_memories():
            if m.id == mid:
                return m
        return None

    def update_memory(
        self,
        memory_id: str,
        *,
        summary: str | None = None,
        details: str | None = None,
        importance: int | None = None,
    ) -> MemoryItem | None:
        items = self.list_memories()
        for i, old in enumerate(items):
            if old.id != memory_id:
                continue
            updates: dict = {"last_seen_at": datetime.now().isoformat(timespec="seconds")}
            if summary is not None:
                text = summary.strip()
                if not text:
                    return None
                updates["summary"] = text[:200]
            if details is not None:
                updates["details"] = details.strip()[:500]
            if importance is not None:
                updates["importance"] = max(1, min(5, int(importance)))
            merged = old.model_copy(update=updates)
            items[i] = merged
            self.save_memories(items)
            return merged
        return None

    def delete_memory(self, memory_id: str) -> bool:
        items = self.list_memories()
        next_items = [m for m in items if m.id != memory_id]
        if len(next_items) == len(items):
            return False
        self.save_memories(next_items)
        return True

    def append_journal(self, line: str) -> None:
        line = (line or "").strip()
        if not line:
            return
        path = self.dir / "journal" / f"{date.today().isoformat()}.md"
        stamp = datetime.now().strftime("%H:%M")
        with path.open("a", encoding="utf-8") as f:
            f.write(f"- {stamp} {line}\n")

    def append_chat_log(self, role: str, content: str) -> None:
        path = self.dir / "chat.jsonl"
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "role": role,
            "content": content,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def recent_chat(self, n: int = 12) -> list[dict]:
        path = self.dir / "chat.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def chat_turn_count(self) -> int:
        """Count user turns for lightweight relationship progression."""
        path = self.dir / "chat.jsonl"
        if not path.exists():
            return 0
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                if json.loads(line).get("role") == "user":
                    count += 1
            except json.JSONDecodeError:
                continue
        return count

    def relationship_stage(self) -> str:
        """MVP relationship pacing: first_meet -> familiar -> close."""
        turns = self.chat_turn_count()
        if turns >= 20:
            return "close"
        if turns >= 6:
            return "familiar"
        return "first_meet"

    def recall(self, query: str, limit: int = 8) -> list[MemoryItem]:
        """Lightweight keyword recall; good enough for MVP before vectors."""
        q = (query or "").lower()
        tokens = [t for t in re.split(r"\W+", q) if len(t) >= 2]
        scored: list[tuple[int, MemoryItem]] = []
        for m in self.list_memories():
            blob = f"{m.summary} {m.details} {' '.join(m.people)}".lower()
            score = m.importance
            for t in tokens:
                if t in blob:
                    score += 3
            for p in m.people:
                if p and p in (query or ""):
                    score += 4
            # Always keep high-importance identity/preference lightly boosted
            if m.kind in {MemoryKind.identity, MemoryKind.preference, MemoryKind.boundary}:
                score += 1
            scored.append((score, m))
        scored.sort(key=lambda x: (x[0], x[1].last_seen_at), reverse=True)
        # Always include top identity facts
        picked: list[MemoryItem] = []
        for m in self.list_memories():
            if m.kind == MemoryKind.identity and m not in picked:
                picked.append(m)
            if len(picked) >= 2:
                break
        for _, m in scored:
            if m not in picked:
                picked.append(m)
            if len(picked) >= limit:
                break
        return picked

    def format_recall_block(self, items: list[MemoryItem]) -> str:
        if not items:
            return "（暂无长期记忆）"
        lines = []
        for m in items:
            people = f" · 相关人: {', '.join(m.people)}" if m.people else ""
            lines.append(f"- [{m.kind.value}|重要{m.importance}] {m.summary}{people}")
            if m.details:
                lines.append(f"  细节: {m.details}")
        return "\n".join(lines)

    def _sync_markdown(self) -> None:
        profile = self.load_profile()
        self.user_md.write_text(
            f"""# USER

- user_id: {profile.user_id}
- 称呼: {profile.preferred_address or profile.display_name or '你'}
- 显示名: {profile.display_name or '（未设置）'}
- 时区: {profile.timezone}
- 安慰偏好: {profile.comfort_notes or '（待观察）'}
- 关系阶段: {self.relationship_stage()}
- 近期情绪: {profile.emotional_state or '（待观察）'}
- 偏好标签: {', '.join(f'{k}×{v}' for k, v in sorted((profile.preference_tags or {}).items(), key=lambda x: -x[1])[:8]) or '（暂无）'}
""",
            encoding="utf-8",
        )
        by_kind: dict[str, list[MemoryItem]] = {}
        for m in self.list_memories():
            by_kind.setdefault(m.kind.value, []).append(m)
        parts = ["# MEMORY\n", "可人工编辑。聊天时模型会读写结构化索引 `memories.json`。\n"]
        for kind in MemoryKind:
            bucket = by_kind.get(kind.value, [])
            if not bucket:
                continue
            parts.append(f"\n## {kind.value}\n")
            for m in sorted(bucket, key=lambda x: -x.importance):
                parts.append(f"- ({m.importance}) {m.summary}")
                if m.details:
                    parts.append(f"  - {m.details}")
        self.memory_md.write_text("\n".join(parts) + "\n", encoding="utf-8")


def new_memory(
    kind: MemoryKind,
    summary: str,
    details: str = "",
    people: list[str] | None = None,
    importance: int = 3,
) -> MemoryItem:
    return MemoryItem(
        id=uuid.uuid4().hex[:12],
        kind=kind,
        summary=summary,
        details=details,
        people=people or [],
        importance=importance,
    )
