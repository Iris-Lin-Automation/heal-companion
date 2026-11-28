"""T1: /api/users 与 /api/recover 不得再列出或交还任何用户。"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.server import app
from companion.memory.schema import MemoryKind
from companion.memory.store import MemoryStore, new_memory


def test_users_and_recover_are_closed(tmp_path, monkeypatch):
    monkeypatch.setattr("companion.memory.store.ROOT", tmp_path)
    busy = MemoryStore("u_busy_user")
    busy.save_profile(busy.load_profile().model_copy(update={"display_name": "最活跃的人"}))
    busy.append_chat_log("user", "只有这个人聊过")
    busy.upsert(new_memory(MemoryKind.event, "不该被枚举出来的事", importance=5))

    quiet = MemoryStore("u_quiet_user")
    quiet.save_profile(quiet.load_profile().model_copy(update={"display_name": "另一个人"}))

    client = TestClient(app)
    for path in (
        "/api/users",
        "/api/recover",
        "/api/recover?nickname=最活跃的人",
        "/api/recover?user_id=u_busy_user",
    ):
        res = client.get(path)
        assert res.status_code == 404, path
        body = res.text
        assert "u_busy_user" not in body
        assert "u_quiet_user" not in body
        assert "最活跃的人" not in body
        assert "不该被枚举出来的事" not in body
        assert '"found": true' not in body.lower() and '"found":true' not in body.lower()


def test_health_still_public():
    res = TestClient(app).get("/api/health")
    assert res.status_code == 200
    assert res.json().get("ok") is True


def test_frontend_does_not_call_recover():
    app_tsx = Path(__file__).resolve().parents[1] / "web" / "src" / "App.tsx"
    text = app_tsx.read_text(encoding="utf-8")
    assert "/api/recover" not in text
    assert "/api/users" not in text
