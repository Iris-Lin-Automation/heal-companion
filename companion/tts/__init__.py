"""TTS package — 火山引擎多情感语音合成。"""

from companion.tts.emotion import parse_emotion_tag, strip_emotion_tag
from companion.tts.volcengine import VolcTTSError, synthesize

__all__ = [
    "parse_emotion_tag",
    "strip_emotion_tag",
    "synthesize",
    "VolcTTSError",
]
