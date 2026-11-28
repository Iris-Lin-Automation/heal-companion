"""Supabase 存储。即使用 service role，每条读写都带上已验证的 user_id。"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from companion.memory.schema import MemoryItem, MemoryKind, UserProfile
from companion.memory.store import MemoryStore

_client: Any = None


def _sb():
    global _client
    if _client is None:
        from supabase import create_client

        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class SupabaseStore:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.sb = _sb()
        self.companion_id, self.conversation_id = self._ensure_scope()

    def _ensure_scope(self) -> tuple[str, str]:
        comp = (
            self.sb.table("companions")
            .select("id")
            .eq("user_id", self.user_id)
            .limit(1)
            .execute()
        )
        rows = comp.data or []
        if not rows:
            created = (
                self.sb.table("companions")
                .insert({"user_id": self.user_id, "name": "heal", "persona_id": "older_friend"})
                .execute()
            )
            rows = created.data or []
        companion_id = rows[0]["id"]

        conv = (
            self.sb.table("conversations")
            .select("id")
            .eq("user_id", self.user_id)
            .limit(1)
            .execute()
        )
        conv_rows = conv.data or []
        if not conv_rows:
            created = (
                self.sb.table("conversations")
                .insert({"user_id": self.user_id, "companion_id": companion_id})
                .execute()
            )
            conv_rows = created.data or []
        return companion_id, conv_rows[0]["id"]

    def load_profile(self) -> UserProfile:
        res = self.sb.table("profiles").select("*").eq("id", self.user_id).limit(1).execute()
        rows = res.data or []
        if not rows:
            self.sb.table("profiles").insert({"id": self.user_id}).execute()
            res = self.sb.table("profiles").select("*").eq("id", self.user_id).limit(1).execute()
            rows = res.data or [{}]
        row = rows[0]
        tags = row.get("preference_tags") or {}
        if not isinstance(tags, dict):
            tags = {}
        return UserProfile(
            user_id=self.user_id,
            display_name=row.get("display_name") or "",
            preferred_address=row.get("preferred_address") or "你",
            timezone=row.get("timezone") or "Asia/Shanghai",
            comfort_notes=row.get("comfort_notes") or "",
            relationship_stage=row.get("relationship_stage") or "first_meet",
            preference_tags={str(k): int(v) for k, v in tags.items()},
            emotional_state=row.get("emotional_state") or "",
            created_at=str(row.get("created_at") or _now()),
        )

    def save_profile(self, profile: UserProfile) -> None:
        self.sb.table("profiles").upsert(
            {
                "id": self.user_id,
                "display_name": profile.display_name,
                "preferred_address": profile.preferred_address,
                "comfort_notes": profile.comfort_notes,
                "timezone": profile.timezone,
                "relationship_stage": self.relationship_stage(),
                "preference_tags": profile.preference_tags or {},
                "emotional_state": profile.emotional_state,
            }
        ).execute()

    def merge_preference_tags(self, new_tags: list[str], emotional_state: str = "") -> list[str]:
        profile = self.load_profile()
        tags = dict(profile.preference_tags or {})
        for raw in new_tags or []:
            tag = (raw or "").strip()
            if not tag or len(tag) > 24:
                continue
            tags[tag] = int(tags.get(tag, 0)) + 1
        ranked = sorted(tags.items(), key=lambda x: (-x[1], x[0]))[:20]
        profile.preference_tags = dict(ranked)
        if (emotional_state or "").strip():
            profile.emotional_state = emotional_state.strip()[:32]
        self.save_profile(profile)
        return [t for t, _ in ranked[:5]]

    def top_preference_tags(self, n: int = 5) -> list[str]:
        tags = self.load_profile().preference_tags or {}
        ranked = sorted(tags.items(), key=lambda x: (-x[1], x[0]))
        return [t for t, _ in ranked[:n]]

    def list_memories(self) -> list[MemoryItem]:
        res = self.sb.table("memories").select("*").eq("user_id", self.user_id).execute()
        items = []
        for row in res.data or []:
            people = row.get("people") or []
            if not isinstance(people, list):
                people = []
            items.append(
                MemoryItem(
                    id=str(row["id"]),
                    kind=MemoryKind(row["kind"]),
                    summary=row.get("summary") or "",
                    details=row.get("details") or "",
                    people=[str(p) for p in people],
                    importance=int(row.get("importance") or 3),
                    created_at=str(row.get("created_at") or _now()),
                    last_seen_at=str(row.get("last_seen_at") or _now()),
                    source=row.get("source") or "chat",
                )
            )
        return items

    def save_memories(self, items: list[MemoryItem]) -> None:
        self.sb.table("memories").delete().eq("user_id", self.user_id).execute()
        if not items:
            return
        self.sb.table("memories").insert([self._memory_row(m) for m in items]).execute()

    def _memory_row(self, item: MemoryItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "user_id": self.user_id,
            "kind": item.kind.value,
            "summary": item.summary,
            "details": item.details or "",
            "people": item.people or [],
            "importance": item.importance,
            "created_at": item.created_at,
            "last_seen_at": item.last_seen_at,
            "source": item.source or "chat",
        }

    def upsert(self, item: MemoryItem) -> MemoryItem:
        items = self.list_memories()
        for old in items:
            if old.kind == item.kind and (
                old.summary == item.summary
                or old.summary in item.summary
                or item.summary in old.summary
            ):
                merged = old.model_copy(
                    update={
                        "summary": item.summary if len(item.summary) >= len(old.summary) else old.summary,
                        "details": item.details or old.details,
                        "people": sorted(set(old.people + item.people)),
                        "importance": max(old.importance, item.importance),
                        "last_seen_at": _now(),
                    }
                )
                self.sb.table("memories").update(self._memory_row(merged)).eq("id", old.id).eq(
                    "user_id", self.user_id
                ).execute()
                return merged
        if not item.id:
            item = item.model_copy(update={"id": uuid.uuid4().hex[:12]})
        self.sb.table("memories").insert(self._memory_row(item)).execute()
        return item

    def get_memory(self, memory_id: str) -> MemoryItem | None:
        res = (
            self.sb.table("memories")
            .select("*")
            .eq("id", memory_id)
            .eq("user_id", self.user_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return next((m for m in self.list_memories() if m.id == memory_id), None)

    def update_memory(
        self,
        memory_id: str,
        *,
        summary: str | None = None,
        details: str | None = None,
        importance: int | None = None,
    ) -> MemoryItem | None:
        current = self.get_memory(memory_id)
        if current is None:
            return None
        updates: dict[str, Any] = {"last_seen_at": _now()}
        if summary is not None:
            text = summary.strip()
            if not text:
                return None
            updates["summary"] = text[:200]
        if details is not None:
            updates["details"] = details.strip()[:500]
        if importance is not None:
            updates["importance"] = max(1, min(5, int(importance)))
        merged = current.model_copy(update=updates)
        self.sb.table("memories").update(
            {
                "summary": merged.summary,
                "details": merged.details,
                "importance": merged.importance,
                "last_seen_at": merged.last_seen_at,
            }
        ).eq("id", memory_id).eq("user_id", self.user_id).execute()
        return merged

    def delete_memory(self, memory_id: str) -> bool:
        if self.get_memory(memory_id) is None:
            return False
        self.sb.table("memories").delete().eq("id", memory_id).eq("user_id", self.user_id).execute()
        return True

    def today_journal(self) -> str:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        res = (
            self.sb.table("messages")
            .select("content")
            .eq("user_id", self.user_id)
            .eq("role", "journal")
            .gte("created_at", start)
            .execute()
        )
        return "\n".join(
            str(row.get("content") or "").strip()
            for row in (res.data or [])
            if str(row.get("content") or "").strip()
        )

    def load_bridge_date(self):
        from datetime import date

        res = (
            self.sb.table("profiles")
            .select("bridge_sent_on")
            .eq("id", self.user_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        raw = rows[0].get("bridge_sent_on") if rows else None
        if not raw:
            return None
        try:
            return date.fromisoformat(str(raw)[:10])
        except ValueError:
            return None

    def save_bridge_date(self) -> None:
        from datetime import date

        self.sb.table("profiles").update(
            {"bridge_sent_on": date.today().isoformat()}
        ).eq("id", self.user_id).execute()

    def append_journal(self, line: str) -> None:
        text = (line or "").strip()
        if text:
            self.append_chat_log("journal", text)

    def append_chat_log(self, role: str, content: str) -> None:
        self.sb.table("messages").insert(
            {
                "conversation_id": self.conversation_id,
                "user_id": self.user_id,
                "role": role,
                "content": content,
            }
        ).execute()

    def recent_chat(self, n: int = 12) -> list[dict]:
        res = (
            self.sb.table("messages")
            .select("role,content,created_at")
            .eq("user_id", self.user_id)
            .order("created_at", desc=True)
            .limit(n)
            .execute()
        )
        rows = list(reversed(res.data or []))
        return [
            {"role": row["role"], "content": row["content"]}
            for row in rows
            if row.get("role") in {"user", "assistant"}
        ]

    def chat_turn_count(self) -> int:
        res = (
            self.sb.table("messages")
            .select("role")
            .eq("user_id", self.user_id)
            .eq("role", "user")
            .execute()
        )
        return len(res.data or [])

    def relationship_stage(self) -> str:
        turns = self.chat_turn_count()
        if turns >= 20:
            return "close"
        if turns >= 6:
            return "familiar"
        return "first_meet"

    def recall(self, query: str, limit: int = 8) -> list[MemoryItem]:
        # 复用文件库的关键词打分，数据源只限当前用户。
        scratch = MemoryStore.__new__(MemoryStore)
        scratch.user_id = self.user_id
        scratch.list_memories = self.list_memories  # type: ignore[method-assign]
        return MemoryStore.recall(scratch, query, limit)

    def format_recall_block(self, items: list[MemoryItem]) -> str:
        return MemoryStore.format_recall_block(self, items)  # type: ignore[arg-type]
