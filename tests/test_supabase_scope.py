"""服务端即使用 service role，读写也必须带上已验证的 user id。"""

from __future__ import annotations

from companion.memory.supabase_store import SupabaseStore

USER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


class _Rec:
    def __init__(self) -> None:
        self.ops: list[tuple] = []

    def table(self, name: str) -> "_Q":
        return _Q(self, name)


class _Q:
    def __init__(self, rec: _Rec, name: str) -> None:
        self.rec = rec
        self.name = name
        self.op = ""
        self.filters: list[tuple[str, str]] = []
        self.payload = None

    def select(self, *args, **kwargs):
        self.op = "select"
        return self

    def eq(self, key: str, value: str):
        self.filters.append((key, value))
        return self

    def limit(self, n: int):
        return self

    def order(self, *args, **kwargs):
        return self

    def insert(self, row):
        self.op = "insert"
        self.payload = row
        return self

    def update(self, row):
        self.op = "update"
        self.payload = row
        return self

    def upsert(self, row):
        self.op = "upsert"
        self.payload = row
        return self

    def delete(self):
        self.op = "delete"
        return self

    def execute(self):
        self.rec.ops.append((self.name, self.op, list(self.filters), self.payload))
        if self.name == "companions" and self.op == "select":
            data = [{"id": "c1"}]
        elif self.name == "conversations" and self.op == "select":
            data = [{"id": "v1"}]
        elif self.name == "memories" and self.op == "select":
            data = [
                {
                    "id": "m1",
                    "kind": "event",
                    "summary": "甲的秘密",
                    "details": "",
                    "people": [],
                    "importance": 3,
                    "created_at": "2026-01-01T00:00:00",
                    "last_seen_at": "2026-01-01T00:00:00",
                    "source": "chat",
                }
            ]
        elif self.name == "profiles" and self.op == "select":
            data = [{"id": USER, "display_name": "甲", "preference_tags": {}}]
        else:
            data = [{"id": "m1"}]
        return type("R", (), {"data": data})()


def test_every_query_is_bound_to_verified_user(monkeypatch):
    rec = _Rec()
    monkeypatch.setattr("companion.memory.supabase_store._sb", lambda: rec)
    store = SupabaseStore(USER)
    store.append_chat_log("user", "只属于甲")
    store.update_memory("m1", summary="改过的甲")
    assert store.delete_memory("m1") is True

    assert rec.ops
    for name, op, filters, payload in rec.ops:
        if op in {"select", "update", "delete"}:
            assert any(key in {"user_id", "id"} for key, _ in filters), (name, op, filters)
            for key, value in filters:
                if key == "user_id":
                    assert value == USER
                if key == "id" and name == "profiles":
                    assert value == USER
        if op == "insert" and isinstance(payload, dict):
            owner = payload.get("user_id", payload.get("id"))
            assert owner == USER
        if op == "upsert" and isinstance(payload, dict):
            assert payload.get("id") == USER

    updates = [op for op in rec.ops if op[0] == "memories" and op[1] == "update"]
    assert updates
    assert ("user_id", USER) in updates[-1][2]
    assert ("id", "m1") in updates[-1][2]
