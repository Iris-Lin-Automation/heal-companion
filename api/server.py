"""Web API + OpenAI-compatible endpoint for Open WebUI / LobeChat."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

from api.auth import require_user_id, require_v1_user
from companion.chat.loop import chat_once, chat_stream
from companion.heartbeat.checkin import craft_checkin
from companion.memory.factory import get_store
from companion.memory.schema import MemoryKind
from companion.memory.store import new_memory

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

app = FastAPI(title="Heal Companion", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Heal-Emotion"],
)


def _settings(
    api_key_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
) -> tuple[OpenAI, str, str]:
    """优先用访客自带的 DeepSeek Key（BYOK），否则回退到服务器 .env。"""
    api_key = (api_key_override or "").strip() or (os.getenv("OPENAI_API_KEY") or "")
    if not api_key or api_key.startswith("sk-xxx"):
        raise HTTPException(
            status_code=401,
            detail="请填写自己的 DeepSeek API Key（设置里粘贴后即可免费体验）",
        )
    base_url = (
        (base_url_override or "").strip()
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.deepseek.com"
    )
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")
    name = os.getenv("COMPANION_NAME", "软软")
    return OpenAI(api_key=api_key, base_url=base_url), model, name


class ChatRequest(BaseModel):
    message: str
    user_id: str = ""  # 已忽略：身份只来自已验证的 JWT
    stream: bool = True
    # 前端悄悄上传：城市 / 本地时间 / 天气（Open-Meteo 等免费源）
    env_context: Optional[dict[str, Any]] = None
    # 访客自带 DeepSeek Key（只走本次请求，不落盘）
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class PingRequest(BaseModel):
    user_id: str = ""  # 已忽略：身份只来自已验证的 JWT
    env_context: Optional[dict[str, Any]] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    # 可选：显式指定情绪（calm/happy/sad）；不传则从句首 [标签] + 用户语境解析
    emotion: Optional[str] = None
    # 可选：用户原话，用于缺标签时的语气兜底
    user_text: Optional[str] = None
    voice_type: Optional[str] = None
    speed_ratio: Optional[float] = None


class ProfileUpdate(BaseModel):
    user_id: str = ""  # 已忽略：身份只来自已验证的 JWT
    display_name: str = ""
    preferred_address: str = "你"
    comfort_notes: str = ""


class MemoryUpdate(BaseModel):
    user_id: str = ""  # 已忽略：身份只来自已验证的 JWT
    summary: Optional[str] = None
    details: Optional[str] = None
    importance: Optional[int] = None


class OpenAIMessage(BaseModel):
    role: str
    content: Any = ""


class OpenAIChatRequest(BaseModel):
    model: str = "heal-companion"
    messages: list[OpenAIMessage]
    stream: bool = False
    temperature: Optional[float] = None
    user: Optional[str] = None


@app.get("/api/health")
def health():
    return {"ok": True, "companion": os.getenv("COMPANION_NAME", "软软")}


@app.post("/api/session", include_in_schema=False)
def open_session():
    """匿名 cookie 会话已关闭。身份只来自 Supabase 登录。"""
    raise HTTPException(status_code=410, detail="请使用账号登录")


@app.get("/api/users", include_in_schema=False)
def list_users():
    """已关闭：公开枚举 data/users 会泄露所有人的 id 与昵称。"""
    raise HTTPException(status_code=404, detail="not found")


@app.get("/api/recover", include_in_schema=False)
def recover_user():
    """已关闭：无凭证按昵称或「最活跃用户」换号会把访客接到别人的记忆。"""
    raise HTTPException(status_code=404, detail="not found")


@app.post("/api/tts")
async def tts(body: TTSRequest, _user_id: str = Depends(require_user_id)):
    """
    TTS 合成：优先火山引擎多情感；失败时回退 edge-tts，保证可播放。
    """
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text 为空")

    from companion.tts.emotion import resolve_emotion
    from starlette.responses import Response

    emotion, clean = resolve_emotion(text, body.user_text or "")
    if body.emotion:
        emotion = body.emotion

    speed_ratio = body.speed_ratio
    if speed_ratio is None:
        try:
            speed_ratio = float(os.getenv("VOLC_SPEED_RATIO", "1.04"))
        except ValueError:
            speed_ratio = 1.04

    # ── 1) 火山引擎 ──
    try:
        from companion.tts.volcengine import VolcTTSError, synthesize

        audio = await synthesize(
            text,
            emotion=emotion,
            voice_type=body.voice_type,
            speed_ratio=speed_ratio,
        )
        if audio:
            return Response(
                content=audio,
                media_type="audio/mpeg",
                headers={"X-Heal-Emotion": emotion},
            )
    except Exception as volc_exc:  # noqa: BLE001
        # 凭证未开通 / 网络失败时回退，不中断体验
        print(f"[TTS] 火山失败，回退 edge-tts: {volc_exc}")

    # ── 2) edge-tts 回退 ──
    try:
        import edge_tts
        from io import BytesIO

        spoken = clean or text
        if len(spoken) > 300:
            spoken = spoken[:300].rsplit("，", 1)[0].rsplit("。", 1)[0] + "…"

        # edge-tts 无多情感，用语速轻微区分；少年感陪伴不要过慢
        rate = "-4%" if emotion == "sad" else ("+8%" if emotion == "happy" else "+2%")
        communicate = edge_tts.Communicate(spoken, "zh-CN-YunxiNeural", rate=rate)
        buf = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        if buf.tell() == 0:
            raise RuntimeError("edge-tts 空音频")
        return Response(
            content=buf.getvalue(),
            media_type="audio/mpeg",
            headers={"X-Heal-Emotion": f"{emotion}|edge"},
        )
    except Exception as edge_exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"TTS 全部失败（火山 + edge）。edge: {edge_exc}",
        ) from edge_exc


@app.get("/api/memories")
def memories(user_id: str = Depends(require_user_id)):
    store = get_store(user_id)
    mem_items = store.list_memories()
    return {
        "user_id": user_id,
        "profile": store.load_profile().model_dump(),
        "memories": [m.model_dump() for m in mem_items],
        "markdown": store.format_recall_block(mem_items),
    }


@app.patch("/api/memories/{memory_id}")
def patch_memory(memory_id: str, body: MemoryUpdate, user_id: str = Depends(require_user_id)):
    store = get_store(user_id)
    updated = store.update_memory(
        memory_id,
        summary=body.summary,
        details=body.details,
        importance=body.importance,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="memory not found")
    return {"ok": True, "memory": updated.model_dump()}


@app.delete("/api/memories/{memory_id}")
def remove_memory(memory_id: str, user_id: str = Depends(require_user_id)):
    store = get_store(user_id)
    if not store.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="memory not found")
    return {"ok": True, "id": memory_id}


@app.get("/api/history")
def history(user_id: str = Depends(require_user_id), limit: int = 40):
    store = get_store(user_id)
    return {"messages": store.recent_chat(limit)}


@app.get("/api/profile")
def get_profile(user_id: str = Depends(require_user_id)):
    store = get_store(user_id)
    return store.load_profile().model_dump()


@app.post("/api/profile")
def update_profile(body: ProfileUpdate, user_id: str = Depends(require_user_id)):
    store = get_store(user_id)
    profile = store.load_profile()
    profile.display_name = (body.display_name or "").strip() or profile.display_name
    profile.preferred_address = (body.preferred_address or "").strip() or profile.preferred_address
    profile.comfort_notes = (body.comfort_notes or "").strip() or profile.comfort_notes
    store.save_profile(profile)
    # Seed identity memory so recall knows the name
    if profile.display_name:
        store.upsert(
            new_memory(
                MemoryKind.identity,
                f"希望被叫做{profile.display_name}",
                importance=5,
            )
        )
    if profile.comfort_notes:
        store.upsert(
            new_memory(
                MemoryKind.preference,
                profile.comfort_notes,
                importance=4,
            )
        )
    return profile.model_dump()


@app.post("/api/ping")
def ping(body: PingRequest, user_id: str = Depends(require_user_id)):
    client, model, name = _settings(body.api_key, body.base_url)
    store = get_store(user_id)
    msg = craft_checkin(
        client, model, store, name, env_context=body.env_context
    )
    from companion.tts.emotion import strip_emotion_tag

    store.append_chat_log("assistant", strip_emotion_tag(msg))
    return {"message": msg, "companion": name}


@app.post("/api/chat")
def chat(body: ChatRequest, user_id: str = Depends(require_user_id)):
    client, model, name = _settings(body.api_key, body.base_url)
    store = get_store(user_id)
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "message empty")

    if not body.stream:
        reply = chat_once(
            client,
            model,
            store,
            text,
            companion_name=name,
            env_context=body.env_context,
        )
        return {"reply": reply, "companion": name}

    def event_gen():
        from companion.chat.loop import resolve_reply_emotion

        full_reply: list[str] = []
        try:
            for token in chat_stream(
                client,
                model,
                store,
                text,
                companion_name=name,
                env_context=body.env_context,
            ):
                full_reply.append(token)
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

            # 正文一结束就 done，别等快捷回复 —— 否则前端一直「正在想」但语音已在播
            reply_text = "".join(full_reply)
            emotion = resolve_reply_emotion(reply_text, text)
            yield f"data: {json.dumps({'done': True, 'companion': name, 'emotion': emotion}, ensure_ascii=False)}\n\n"

            # chips 失败绝不能再抛 error：否则前端会把已成功的回复盖成「连不上」
            try:
                yield ": keepalive\n\n"
                chips = _gen_quick_replies(client, model, text, reply_text)
                if chips:
                    yield f"data: {json.dumps({'quick_replies': chips}, ensure_ascii=False)}\n\n"
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            # 若已开始吐字，尽量别用 error 冲掉前端已渲染内容（前端也会兜底）
            if full_reply:
                emotion = resolve_reply_emotion("".join(full_reply), text)
                yield f"data: {json.dumps({'done': True, 'companion': name, 'emotion': emotion}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


def _gen_quick_replies(client: "OpenAI", model: str, user_msg: str, ai_reply: str) -> list[str]:
    """生成 2–3 条懒人话题胶囊，基于上下文推断用户可能想回复的内容。"""
    _CHIPS_PROMPT = """\
你是一个对话交互设计师。根据 AI 刚才说的话和用户的上下文，生成 2-3 条简短的气泡选项，代表用户"可能想回复的情绪/意愿"。

要求：
- 中文；每条不超过 12 个字；带一个贴切 emoji 前缀
- 风格亲切口语化，不要太正式
- 分别覆盖不同情绪倾向（如：倾诉延伸 / 想摆烂放空 / 转移话题）
- 严格只返回 JSON 数组，不要其他文字，例如：
  ["🥺 真的好累，抱抱我", "☕ 先喝口水缓缓", "🎵 不想说话，放首歌"]
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.8,
            max_tokens=120,
            timeout=8.0,
            messages=[
                {"role": "system", "content": _CHIPS_PROMPT},
                {"role": "user", "content": f"用户说：{user_msg}\nAI 回复：{ai_reply}\n\n请生成气泡选项："},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        # 找到 JSON 数组部分
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            chips = json.loads(raw[start:end])
            if isinstance(chips, list):
                return [str(c) for c in chips[:3]]
    except Exception:  # noqa: BLE001
        pass
    # fallback
    return ["🥺 再说说", "☕ 先休息一下", "🎵 放首歌放空"]


# -------- OpenAI-compatible (plug into Open WebUI / LobeChat) --------


@app.get("/v1/models")
def list_models():
    name = os.getenv("COMPANION_NAME", "软软")
    return {
        "object": "list",
        "data": [
            {
                "id": "heal-companion",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "heal-companion",
                "name": f"{name} · 治愈陪伴",
            }
        ],
    }


def _last_user_and_history(messages: list[OpenAIMessage]) -> tuple[str, list[dict[str, str]]]:
    history: list[dict[str, str]] = []
    last_user = ""
    for m in messages:
        role = m.role
        content = m.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        content = str(content or "")
        if role == "system":
            continue
        if role == "user":
            last_user = content
        if role in {"user", "assistant"} and content:
            history.append({"role": role, "content": content})
    if history and history[-1]["role"] == "user":
        history = history[:-1]
    return last_user, history


@app.post("/v1/chat/completions")
def openai_chat(
    body: OpenAIChatRequest,
    authorization: Optional[str] = Header(default=None),
):
    user_id = require_v1_user(authorization)
    client, model, name = _settings()
    store = get_store(user_id)
    user_text, history = _last_user_and_history(body.messages)
    if not user_text:
        raise HTTPException(400, "no user message")

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    if not body.stream:
        # Use history from client so Open WebUI multi-turn works
        reply = "".join(
            chat_stream(
                client,
                model,
                store,
                user_text,
                companion_name=name,
                history_override=history,
            )
        )
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": "heal-companion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
        }

    def sse():
        try:
            for token in chat_stream(
                client,
                model,
                store,
                user_text,
                companion_name=name,
                history_override=history,
            ):
                payload = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": "heal-companion",
                    "choices": [
                        {"index": 0, "delta": {"content": token}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            end = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": "heal-companion",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(end)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001
            err = {"error": {"message": str(exc), "type": "server_error"}}
            yield f"data: {json.dumps(err)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


web_dist = ROOT / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web")
