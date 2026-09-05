"""情绪标签解析 — LLM 句首 `[情绪]` → 火山引擎 emotion 参数。

链路说明
--------
1. LLM 被要求句首输出 `[平和|开心|心疼|温柔]`（见 PersonaManager 指导）
2. 本模块解析标签 → 火山 emotion（calm/happy/sad 等）
3. 若 LLM 漏标 / 标错，可用用户原话做启发式兜底（suggest_from_user）
4. 「检测」不是独立 NLU，而是：LLM 自标 + 规则兜底

注意：火山部分音色不支持 `comfort` 等值，会静默失败并回退 calm，
因此映射必须落在常见可用集合上。
"""

from __future__ import annotations

import re

# 句首情绪标签，例如：[温柔]、【开心】、(心疼)
_EMOTION_TAG_RE = re.compile(
    r"^\s*[\[【(（]\s*(?P<label>[^\]】)）]+?)\s*[\]】)）]\s*",
    re.UNICODE,
)

# 中文标签 / 别名 → 火山引擎 emotion 参数
# 仅使用实测/文档常见值：calm / happy / sad / angry / surprised
# （旧版曾把「温柔」映到 comfort，多数音色不支持 → 一律回退 calm，听感像没语气）
EMOTION_MAP: dict[str, str] = {
    "平和": "calm",
    "平静": "calm",
    "冷静": "calm",
    "calm": "calm",
    "neutral": "calm",
    "开心": "happy",
    "高兴": "happy",
    "愉快": "happy",
    "happy": "happy",
    "心疼": "sad",
    "难过": "sad",
    "失落": "sad",
    "疲惫": "sad",
    "sad": "sad",
    # 温柔/安慰：优先 soft 系（gentle/warm），失败再 sad
    "温柔": "gentle",
    "柔和": "gentle",
    "安慰": "warm",
    "关切": "warm",
    "关心": "warm",
    "温柔安慰": "gentle",
    "comfort": "gentle",
    "认真": "calm",
    "生气": "angry",
    "愤怒": "angry",
    "害羞": "happy",
    "脸红": "happy",
    "直白": "happy",
    "热烈": "happy",
    "明亮": "happy",
    "撒娇": "happy",
    "得意": "happy",
    "吃醋": "sad",
    "小情绪": "sad",
    "委屈": "sad",
    "受伤": "sad",
}

# 火山失败时的降级链（synthesize 会依次尝试）
EMOTION_FALLBACKS: dict[str, list[str]] = {
    "happy": ["happy", "calm"],
    "sad": ["sad", "tear", "calm"],
    "angry": ["angry", "sad", "calm"],
    "surprised": ["surprised", "happy", "calm"],
    "gentle": ["gentle", "warm", "sad", "calm"],
    "warm": ["warm", "gentle", "sad", "calm"],
    "sorry": ["sorry", "sad", "calm"],
    "tear": ["tear", "sad", "calm"],
    "calm": ["calm"],
    "comfort": ["gentle", "warm", "sad", "calm"],
}

DEFAULT_EMOTION = "calm"

# 用户原话 → 建议语气（启发式，不依赖 LLM）
_USER_DISTRESS = re.compile(
    r"(难受|难过|想哭|哭了|崩溃|绝望|好累|疲惫|失眠|睡不着|被骂|没用|"
    r"焦虑|害怕|恐慌|孤独|心痛|委屈|撑不住|空了|烦死|不想活)",
    re.I,
)
_USER_JOY = re.compile(
    r"(开心|高兴|好开心|太棒了|真好|幸福|松了口气|终于|小确幸|可爱|哈哈)",
    re.I,
)
_USER_ANGER = re.compile(r"(生气|愤怒|气死|烦死了|受够了|凭什么)", re.I)


def parse_emotion_tag(text: str) -> tuple[str, str]:
    """从句首解析情绪标签。

    Returns
    -------
    (emotion, clean_text)
        emotion: 火山引擎 emotion 参数（如 calm / happy / sad）
        clean_text: 去掉句首标签后的朗读文本
    """
    raw = (text or "").strip()
    if not raw:
        return DEFAULT_EMOTION, ""

    m = _EMOTION_TAG_RE.match(raw)
    if not m:
        return DEFAULT_EMOTION, raw

    label_raw = (m.group("label") or "").strip()
    label = label_raw.lower()
    emotion = (
        EMOTION_MAP.get(label_raw)
        or EMOTION_MAP.get(label)
        or DEFAULT_EMOTION
    )
    clean = raw[m.end() :].strip()
    return emotion, clean or raw


def strip_emotion_tag(text: str) -> str:
    """仅去掉句首情绪标签（用于聊天持久化 / UI 展示）。"""
    _, clean = parse_emotion_tag(text)
    return clean


def has_emotion_tag(text: str) -> bool:
    return bool(_EMOTION_TAG_RE.match((text or "").strip()))


def suggest_from_user(user_text: str) -> str | None:
    """根据用户原话启发式建议火山 emotion；无明显信号时返回 None。"""
    t = (user_text or "").strip()
    if not t:
        return None
    if _USER_DISTRESS.search(t):
        return "sad"
    if _USER_JOY.search(t):
        return "happy"
    if _USER_ANGER.search(t):
        return "sad"  # 陪伴场景用软声接住，不用 angry
    return None


def resolve_emotion(reply_text: str, user_text: str = "") -> tuple[str, str]:
    """综合 LLM 句首标签 + 用户语境，得到最终 (emotion, clean_text)。

    优先级：
    1. 有有效句首标签 → 用标签
    2. 标签缺失或为 calm，但用户明显负面/开心 → 用启发式覆盖
    3. 否则 calm
    """
    tagged_emotion, clean = parse_emotion_tag(reply_text)
    hinted = suggest_from_user(user_text)

    if has_emotion_tag(reply_text) and tagged_emotion != DEFAULT_EMOTION:
        return tagged_emotion, clean

    if hinted and tagged_emotion == DEFAULT_EMOTION:
        return hinted, clean

    if has_emotion_tag(reply_text):
        return tagged_emotion, clean

    return (hinted or DEFAULT_EMOTION), clean


def label_for_emotion(emotion: str) -> str:
    """火山 emotion → 中文展示/回填标签。"""
    rev = {
        "happy": "开心",
        "sad": "心疼",
        "calm": "平和",
        "angry": "心疼",
        "surprised": "开心",
        "comfort": "温柔",
        "gentle": "温柔",
        "warm": "温柔",
        "sorry": "心疼",
        "tear": "心疼",
    }
    return rev.get(emotion or DEFAULT_EMOTION, "平和")


def ensure_emotion_prefix(reply_text: str, user_text: str = "") -> str:
    """若回复缺句首标签，按 resolve 结果补上（供非流式 / 落库前使用）。"""
    raw = (reply_text or "").strip()
    if not raw:
        return raw
    if has_emotion_tag(raw):
        return raw
    emotion, clean = resolve_emotion(raw, user_text)
    return f"[{label_for_emotion(emotion)}]{clean}"
