"""登录后的 JWT 决定身份。伪造 user_id 不能读写别人的记忆。"""

from __future__ import annotations

import uuid

import jwt
from fastapi.testclient import TestClient

from api.server import app
from companion.memory.schema import MemoryKind
from companion.memory.store import MemoryStore, new_memory

SECRET = "test-jwt-secret-not-production-32b"


def _token(uid: str) -> str:
    return jwt.encode(
        {"sub": uid, "aud": "authenticated", "role": "authenticated"},
        SECRET,
        algorithm="HS256",
    )


def _bind(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("companion.memory.store.ROOT", tmp_path)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setattr("api.server.get_store", lambda user_id: MemoryStore(user_id))


def _authed(uid: str) -> TestClient:
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {_token(uid)}"
    return client


def test_private_routes_require_login(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    client = TestClient(app)
    assert client.get("/api/history").status_code == 401
    assert client.get("/api/memories").status_code == 401
    assert client.get("/api/profile").status_code == 401
    assert client.post("/api/chat", json={"message": "hi", "user_id": "u_other"}).status_code == 401
    assert client.patch("/api/memories/abc", json={"summary": "x", "user_id": "u_other"}).status_code == 401
    assert client.delete("/api/memories/abc", params={"user_id": "u_other"}).status_code == 401
    assert (
        client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}], "user": "u_other"},
        ).status_code
        == 401
    )
    forged = client.get("/api/memories", headers={"Authorization": "Bearer not-a-jwt"})
    assert forged.status_code == 401


def test_anonymous_session_endpoint_is_closed(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    res = TestClient(app).post("/api/session", json={"rotate": True, "user_id": "u_spoof"})
    assert res.status_code == 410
    assert "u_spoof" not in res.text


def test_spoofed_user_id_cannot_cross_read_or_write(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())
    c1 = _authed(id1)
    c2 = _authed(id2)

    MemoryStore(id1).upsert(new_memory(MemoryKind.event, "甲的秘密", importance=5))
    MemoryStore(id1).append_chat_log("user", "甲说过的话")
    other = MemoryStore(id2).upsert(new_memory(MemoryKind.event, "乙的秘密", importance=5))

    memories = c1.get("/api/memories", params={"user_id": id2}).json()
    summaries = [m["summary"] for m in memories["memories"]]
    assert "甲的秘密" in summaries
    assert "乙的秘密" not in summaries
    assert memories["user_id"] == id1

    history = c1.get("/api/history", params={"user_id": id2}).json()["messages"]
    assert any("甲说过的话" in m["content"] for m in history)

    denied = c1.delete(f"/api/memories/{other.id}", params={"user_id": id2})
    assert denied.status_code == 404
    assert MemoryStore(id2).get_memory(other.id) is not None

    own_id = MemoryStore(id1).list_memories()[0].id
    forged = c2.patch(
        f"/api/memories/{own_id}",
        json={"user_id": id1, "summary": "被改掉"},
    )
    assert forged.status_code == 404
    assert MemoryStore(id1).get_memory(own_id).summary == "甲的秘密"


def test_chat_stream_uses_token_not_body(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    uid = str(uuid.uuid4())
    client = _authed(uid)
    seen: list[str] = []

    def fake_stream(client, model, store, text, **kwargs):
        seen.append(store.user_id)
        yield "hi"

    monkeypatch.setattr("api.server.chat_stream", fake_stream)
    monkeypatch.setattr("api.server._settings", lambda *a, **k: (None, "m", "heal"))
    monkeypatch.setattr("api.server._gen_quick_replies", lambda *a, **k: [])

    res = client.post(
        "/api/chat",
        json={"message": "你好", "user_id": "u_attacker", "stream": True},
    )
    assert res.status_code == 200
    assert '"token": "hi"' in res.text or '"token":"hi"' in res.text
    assert seen == [uid]


def test_service_key_cannot_impersonate_on_product_routes(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    monkeypatch.setenv("HEAL_V1_KEY", "heal-v1-test-key")
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer heal-v1-test-key"
    assert client.get("/api/memories").status_code == 401
