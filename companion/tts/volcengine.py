"""火山引擎多情感 TTS (OpenSpeech HTTP)。

文档：https://openspeech.bytedance.com/api/v1/tts
认证：Header Authorization = Bearer;{token}  （注意是分号，不是空格）
"""

from __future__ import annotations

import base64
import os
import uuid
from typing import Any

import httpx

from companion.tts.emotion import DEFAULT_EMOTION, EMOTION_FALLBACKS, parse_emotion_tag

VOLC_TTS_URL = "https://openspeech.bytedance.com/api/v1/tts"


class VolcTTSError(RuntimeError):
    """火山引擎 TTS 调用失败。"""


def _settings() -> dict[str, str]:
    appid = (os.getenv("VOLC_APPID") or "").strip()
    token = (os.getenv("VOLC_TOKEN") or "").strip()
    voice = (os.getenv("VOLC_VOICE_TYPE") or "BV001_streaming").strip()
    cluster = (os.getenv("VOLC_CLUSTER") or "volcano_tts").strip()
    if not appid or not token:
        raise VolcTTSError("请在 .env 配置 VOLC_APPID 与 VOLC_TOKEN")
    return {
        "appid": appid,
        "token": token,
        "voice_type": voice,
        "cluster": cluster,
    }


def build_payload(
    text: str,
    *,
    emotion: str = DEFAULT_EMOTION,
    voice_type: str | None = None,
    speed_ratio: float = 1.04,
) -> dict[str, Any]:
    cfg = _settings()
    try:
        pitch_ratio = float(os.getenv("VOLC_PITCH_RATIO", "1.03"))
    except ValueError:
        pitch_ratio = 1.03
    return {
        "app": {
            "appid": cfg["appid"],
            "token": cfg["token"],
            "cluster": cfg["cluster"],
        },
        "user": {"uid": os.getenv("VOLC_UID", "heal-companion")},
        "audio": {
            "voice_type": voice_type or cfg["voice_type"],
            "encoding": "mp3",
            "speed_ratio": speed_ratio,
            "volume_ratio": 1.0,
            "pitch_ratio": pitch_ratio,
            "emotion": emotion or DEFAULT_EMOTION,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
        },
    }


def _emotion_candidates(emotion: str) -> list[str]:
    key = (emotion or DEFAULT_EMOTION).strip() or DEFAULT_EMOTION
    chain = EMOTION_FALLBACKS.get(key) or [key, DEFAULT_EMOTION]
    # 去重保序
    seen: set[str] = set()
    out: list[str] = []
    for e in chain:
        if e not in seen:
            seen.add(e)
            out.append(e)
    if DEFAULT_EMOTION not in seen:
        out.append(DEFAULT_EMOTION)
    return out


async def synthesize(
    text: str,
    *,
    emotion: str | None = None,
    voice_type: str | None = None,
    speed_ratio: float = 1.04,
) -> bytes:
    """合成 MP3 字节流。

    若 text 句首带 `[温柔]` 等标签且未显式传 emotion，则自动解析。
    音色不支持某 emotion 时按降级链重试，并打印实际生效值便于排查。
    """
    parsed_emotion, clean = parse_emotion_tag(text)
    final_emotion = emotion or parsed_emotion
    spoken = clean.strip()
    if not spoken:
        raise VolcTTSError("TTS 文本为空")

    # 过长截断，避免超时
    if len(spoken) > 300:
        spoken = spoken[:300].rsplit("，", 1)[0].rsplit("。", 1)[0] + "…"

    # 关切类稍微放慢即可，避免听起来拖沓
    if final_emotion in {"sad", "comfort", "gentle", "warm", "sorry", "tear"} and speed_ratio > 1.0:
        speed_ratio = 1.0

    cfg = _settings()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{cfg['token']}",
    }
    candidates = _emotion_candidates(final_emotion)
    last_err = ""

    async with httpx.AsyncClient(timeout=30.0) as client:
        for emo in candidates:
            payload = build_payload(
                spoken,
                emotion=emo,
                voice_type=voice_type,
                speed_ratio=speed_ratio,
            )
            resp = await client.post(VOLC_TTS_URL, json=payload, headers=headers)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue
            data = resp.json()
            code = data.get("code")
            if code not in (None, 0, 3000, "3000", "0"):
                last_err = f"code={code}: {data.get('message') or data}"
                print(f"[TTS] emotion={emo!r} 失败，尝试下一个: {last_err}")
                continue
            b64 = data.get("data")
            if not b64:
                last_err = f"响应无音频 data: {str(data)[:200]}"
                continue
            if emo != final_emotion:
                print(f"[TTS] 请求 emotion={final_emotion!r} → 实际使用 {emo!r}")
            else:
                print(f"[TTS] emotion={emo!r} ok, chars={len(spoken)}")
            try:
                return base64.b64decode(b64)
            except Exception as exc:  # noqa: BLE001
                raise VolcTTSError(f"base64 解码失败: {exc}") from exc

    raise VolcTTSError(f"全部 emotion 候选失败 ({candidates}): {last_err}")
