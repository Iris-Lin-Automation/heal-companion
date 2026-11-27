"""PersonaManager — 人设加载 + 三层记忆 System Prompt 组装器。

职责
----
1. 从 YAML（或遗留 .md）读取角色配置，渲染角色基础 prompt。
2. 动态注入三层记忆上下文：
   - Layer 1：用户档案  (UserProfile)
   - Layer 2：召回的情节记忆  (list[MemoryItem])
   - Layer 3：偏好标签  (list[str])  ← 当 extract.py 支持后填入
3. 对外暴露唯一入口：
       PersonaManager().build_system_prompt(persona_id, ...)

用法
----
    from companion.persona.loader import PersonaManager

    mgr = PersonaManager()
    system_prompt, name = mgr.build_system_prompt(
        persona_id="older_friend",
        name_override="heal",
        user_profile=store.load_profile(),
        recalled_memories=store.recall(user_text, limit=8),
        preference_tags=None,          # TODO: 当 extract.py 支持后传入
    )
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from companion.memory.schema import MemoryItem, UserProfile

PERSONA_DIR = Path(__file__).resolve().parent

# 对话回复指导（追加在每个 system prompt 末尾）
_RESPONSE_GUIDELINES = (
    "回复要求：中文；字数控制在 80 字以内；先回应情绪；"
    "你是专属长期陪伴者：有主见、不每句顺着、不恋爱腔、不客服腔；"
    "需要时给 1 个现实微小行动；若用户分享了生活事件，自然确认你记住了要点。\n"
    "情绪标签（必须，决定语音语气）：每条回复必须以方括号标签开头，且只能选下列之一：\n"
    "- `[明亮]`：日常问候、用户回来、轻松开场\n"
    "- `[开心]`：用户分享小确幸、好事、轻松玩笑\n"
    "- `[心疼]`：用户痛苦、被骂、自责、焦虑、失眠、崩溃——优先用这个\n"
    "- `[温柔]`：安抚、陪伴、深夜关怀、轻轻提醒休息\n"
    "- `[认真]`：表达不同意见、边界、轻微不快（立绘：一点生气）\n"
    "- `[生气]`：被羞辱、被命令过界、非常生气（立绘：非常生气）\n"
    "- `[委屈]`：用户忽略、调侃过界、你有小情绪但不攻击用户\n"
    "- `[受伤]`：更深的受伤——比委屈更重\n"
    "- `[平和]`：仅用于日常闲聊、事务确认，没有明显情绪时\n"
    "少用`[热烈]`/`[撒娇]`/`[害羞]`（易偏恋爱向）；不同意时优先`[认真]`。\n"
    "标签紧贴正文，例如：`[心疼]被当众骂确实难受，先别急着证明自己。`\n"
    "禁止默认永远用`[平和]`；用户明显难受时不要用`[开心]`。"
    "为了语音更像真人，正文要多用短句、停顿和自然语气词，如“嗯”“我知道”“等一下”“你先别急”。"
    "不要解释标签含义，不要在正文里再提情绪标签。"
)


# ════════════════════════════════════════════════════════
#  PersonaManager
# ════════════════════════════════════════════════════════

class PersonaManager:
    """加载人设 YAML / MD，组装含三层记忆的完整 System Prompt。"""

    def __init__(self, persona_dir: Path = PERSONA_DIR) -> None:
        self.dir = persona_dir
        self._cache: dict[str, tuple[dict[str, Any], str]] = {}  # persona_id → (data, raw_kind)

    # ---------------------------------------------------------------- #
    #  公开接口                                                          #
    # ---------------------------------------------------------------- #

    def build_system_prompt(
        self,
        persona_id: str,
        name_override: str | None = None,
        user_profile: "UserProfile | None" = None,
        recalled_memories: "list[MemoryItem] | None" = None,
        preference_tags: list[str] | None = None,
        env_context: dict[str, Any] | None = None,
        relationship_stage: str | None = None,
    ) -> tuple[str, str]:
        """组装完整 System Prompt，返回 ``(prompt, resolved_name)``。

        Parameters
        ----------
        persona_id:
            YAML/MD 文件名（不含扩展名），如 ``"older_friend"``。
        name_override:
            覆盖 YAML 中的 ``name`` 字段（如从 .env COMPANION_NAME 读取）。
        user_profile:
            ``companion.memory.schema.UserProfile`` 对象 —— Layer 1。
        recalled_memories:
            向量/关键词召回的 ``MemoryItem`` 列表 —— Layer 2。
        preference_tags:
            动态偏好标签列表（由 extract.py Auto-Tagging 产生）—— Layer 3。
            尚未实现时传 ``None`` 即可，该层会被跳过。
        env_context:
            前端悄悄上传的实时环境：city / local_time / weather / temp_c。
        """
        base_prompt, name = self._load_persona_prompt(persona_id, name_override)

        sections: list[str] = [base_prompt]

        # ── Layer 1: 用户档案 ──
        if user_profile is not None:
            sections.append(_fmt_profile(user_profile))

        if relationship_stage:
            sections.append(_fmt_relationship_stage(relationship_stage))

        # ── Layer 2: 召回记忆 ──
        if recalled_memories:
            sections.append(_fmt_memories(recalled_memories))

        # ── Layer 3: 偏好标签 ──
        if preference_tags:
            sections.append(_fmt_tags(preference_tags))

        # ── 实时环境（前端采集：城市/时间/天气）──
        if env_context:
            sections.append(_fmt_env_context(env_context))
        else:
            # 无前端环境时，退回服务器本地昼夜感知
            sections.append(_get_time_context())

        # ── 法宝 C：渐进精装修笔记（tuning_notes.md 已沉淀规则）──
        tuning = _load_tuning_notes(self.dir)
        if tuning:
            sections.append(tuning)

        # ── 回复指导 ──
        sections.append(_RESPONSE_GUIDELINES)

        return "\n\n".join(s for s in sections if s), name

    # ---------------------------------------------------------------- #
    #  内部方法                                                          #
    # ---------------------------------------------------------------- #

    def _load_persona_prompt(
        self,
        persona_id: str,
        name_override: str | None,
    ) -> tuple[str, str]:
        """返回 ``(base_persona_prompt, resolved_name)``。

        加载优先级：
        1. ``persona/<id>/`` 模块目录（``_index.yaml`` + 各模块）
        2. ``persona/<id>.yaml`` 单文件（兼容旧写法）
        3. ``persona/<id>.md``
        """
        modular_dir = self.dir / persona_id
        yaml_path = self.dir / f"{persona_id}.yaml"
        md_path = self.dir / f"{persona_id}.md"

        if modular_dir.is_dir() and (modular_dir / "_index.yaml").exists():
            data = _load_modular_persona(modular_dir)
            name = name_override or data.get("name", "heal")
            return _yaml_to_prompt(data, name), name

        if yaml_path.exists():
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            name = name_override or data.get("name", "heal")
            return _yaml_to_prompt(data, name), name

        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            name = name_override or "软软"
            text = text.replace("「软软」", f"「{name}」")
            return text, name

        raise FileNotFoundError(
            f"No persona file for id='{persona_id}' in {self.dir}"
        )


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """浅层键覆盖；同名 dict 递归合并，list 直接替换。"""
    out = dict(base)
    for key, value in incoming.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _load_modular_persona(modular_dir: Path) -> dict[str, Any]:
    """读取 ``_index.yaml`` + modules 列表，合并为人设 dict。"""
    index_path = modular_dir / "_index.yaml"
    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    modules = index.get("modules") or []
    data: dict[str, Any] = {
        k: v for k, v in index.items() if k not in {"modules"}
    }
    for stem in modules:
        path = modular_dir / f"{stem}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Persona module missing: {path}")
        chunk = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(chunk, dict):
            raise ValueError(f"Persona module must be a mapping: {path}")
        data = _deep_merge(data, chunk)
    return data


# ════════════════════════════════════════════════════════
#  YAML → 角色基础 Prompt
# ════════════════════════════════════════════════════════

def _yaml_to_prompt(data: dict[str, Any], name: str) -> str:
    parts: list[str] = []

    # 结构化人设卡：以后优先维护这些小块，避免把角色写成一整段大作文。
    structured_sections = [
        ("persona_card", "角色圣经"),
        ("appearance", "视觉锚点"),
        ("relationship_system", "关系系统"),
        ("emotional_temperature", "情感温度机制"),
        ("speech_texture", "说话纹理"),
        ("scenario_reactions", "场景反应"),
        ("visual_assets", "表情与视觉资产"),
        ("maintenance_notes", "维护说明"),
    ]
    for key, title in structured_sections:
        if value := data.get(key):
            rendered = _fmt_structured_yaml(value)
            if rendered:
                parts.append(f"# {title}\n{rendered}")

    # 角色身份
    if role := (data.get("role_description") or "").strip():
        parts.append(f"# 你是谁\n{role}")

    # 核心信念
    if belief := (data.get("core_belief") or "").strip():
        parts.append(f"# 核心信念\n{belief}")

    # 性格特质
    if traits := data.get("personality"):
        parts.append("# 性格特质\n" + "\n".join(f"- {t}" for t in traits))

    # 对话风格
    if style := data.get("dialogue_style"):
        parts.append("# 对话风格\n" + "\n".join(f"- {s}" for s in style))

    # 绝对禁止
    if banned := data.get("banned_rules"):
        parts.append("# 绝对禁止\n" + "\n".join(f"- {b}" for b in banned))

    # 情绪响应原则
    if emotional := data.get("emotional_response"):
        parts.append("# 情绪响应原则\n" + "\n".join(f"- {e}" for e in emotional))

    # 现实连接引导
    if rwc := data.get("real_world_connection"):
        parts.append("# 现实连接引导\n" + "\n".join(f"- {r}" for r in rwc))

    # Few-shot 示例
    if examples := data.get("few_shot_examples"):
        shots = "\n\n".join(
            f"用户：{ex['user']}\n{name}：{ex['assistant']}"
            for ex in examples
        )
        parts.append(f"# 参考对话示例\n\n{shots}")

    return "\n\n".join(parts)

_STRUCTURED_LABELS = {
    "archetype": "角色原型",
    "one_sentence": "一句话人设",
    "age_range": "年龄感",
    "social_position": "现实身份感",
    "core_contrast": "核心反差",
    "inner_drive": "内在驱动",
    "not_this": "不是这种人",
    "keywords": "关键词",
    "face": "脸部",
    "hair": "头发",
    "eyes": "眼睛",
    "body": "体态",
    "clothing": "服装",
    "aura": "气质",
    "camera": "镜头感",
    "stages": "关系阶段",
    "addressing": "称呼规则",
    "boundary": "边界规则",
    "repair": "修复方式",
    "repair_stage": "修复阶段",
    "initial": "初始温度",
    "warmer_when": "升温条件",
    "cooler_when": "降温条件",
    "cooling_behavior": "降温表现",
    "recovery_behavior": "回温表现",
    "sentence_length": "句长",
    "tone": "语气",
    "pet_phrases": "口头纹理",
    "action_beats": "动作描写",
    "avoid": "避免",
    "work_exhaustion": "下班疲惫",
    "lonely_night": "深夜孤独",
    "travel": "旅行路上",
    "good_news": "分享好事",
    "self_blame": "自责低落",
    "boundary_crossed": "用户越界",
    "neutral": "日常图",
    "smile": "微笑图",
    "hurt": "受伤/认真图",
}


def _fmt_structured_yaml(value: Any, indent: int = 0) -> str:
    """Render nested YAML persona blocks into compact Chinese prompt bullets."""
    prefix = "  " * indent

    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            label = _STRUCTURED_LABELS.get(str(key), str(key))
            if isinstance(child, (dict, list)):
                lines.append(f"{prefix}- {label}：")
                rendered = _fmt_structured_yaml(child, indent + 1)
                if rendered:
                    lines.append(rendered)
            elif child is not None and str(child).strip():
                lines.append(f"{prefix}- {label}：{child}")
        return "\n".join(lines)

    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                rendered = _fmt_structured_yaml(item, indent + 1)
                if rendered:
                    lines.append(f"{prefix}-")
                    lines.append(rendered)
            elif item is not None and str(item).strip():
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines)

    return f"{prefix}- {value}" if value is not None and str(value).strip() else ""

# ════════════════════════════════════════════════════════
#  三层记忆格式化辅助函数
# ════════════════════════════════════════════════════════

def _fmt_profile(profile: "UserProfile") -> str:
    """Layer 1 — 用户基础档案。"""
    lines = ["# Layer 1 · 用户档案"]
    if profile.display_name:
        lines.append(f"- 昵称：{profile.display_name}")
    if profile.preferred_address and profile.preferred_address != "你":
        lines.append(f"- 称呼偏好：{profile.preferred_address}")
    if profile.comfort_notes:
        lines.append(f"- 安慰偏好：{profile.comfort_notes}")
    if getattr(profile, "relationship_stage", ""):
        lines.append(f"- 默认关系阶段：{profile.relationship_stage}")
    if profile.timezone and profile.timezone != "Asia/Shanghai":
        lines.append(f"- 时区：{profile.timezone}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _fmt_relationship_stage(stage: str) -> str:
    """Relationship pacing guardrail injected every turn."""
    stage = (stage or "first_meet").strip()
    rules = {
        "first_meet": (
            "初识",
            "清爽、真诚、克制，但不冷漠。可以关心，但不要强喊“姐姐”，不要表达专属占有。"
            "重点是让用户觉得自然、安全、愿意再回来。"
        ),
        "familiar": (
            "熟悉",
            "偶尔喊“姐姐”，开始出现偏爱和记得她的细节。可以更明亮、更直白，露出一点熟后小狗感，"
            "但仍然尊重她的节奏，不强行升级关系。"
        ),
        "close": (
            "亲近",
            "直白热烈，专属感更强。可以更自然地表达“我想听你说”“我站你这边”“我会记得”，"
            "但禁止病态占有、控制、索取回应。"
        ),
    }
    label, guidance = rules.get(stage, rules["first_meet"])
    return (
        "# 关系进度与边界\n"
        f"当前关系阶段：{label}（{stage}）。\n"
        f"阶段语气：{guidance}\n"
        "越界处理：如果用户故意羞辱、命令、践踏你的边界，先温和表达不舒服；"
        "如果对方继续不尊重，短暂退开并减少回应热度。不要惩罚用户，也不要继续无底线讨好。"
    )


def _fmt_memories(memories: "list[MemoryItem]") -> str:
    """Layer 2 — 召回的情节/事实记忆（按重要度排序）。"""
    if not memories:
        return ""
    sorted_mems = sorted(memories, key=lambda m: -m.importance)
    lines = ["# Layer 2 · 召回记忆（以下是关于用户你已知的信息，对话中自然使用）"]
    for m in sorted_mems:
        tag = f"[{m.kind.value}]"
        people_str = f" 涉及：{'、'.join(m.people)}" if m.people else ""
        lines.append(f"- {tag} {m.summary}{people_str}")
    return "\n".join(lines)


def _get_time_context() -> str:
    """昼夜感知上下文 — 根据当前服务器时间注入时间段提示。"""
    hour = datetime.now().hour
    if 5 <= hour < 9:
        tone = "现在是清晨（{}点），用户可能刚起床。语气温柔轻盈，可以问问昨晚睡得怎样。".format(hour)
    elif 9 <= hour < 12:
        tone = "现在是上午（{}点），用户可能在工作或学习中。保持稳定、专注的陪伴感。".format(hour)
    elif 12 <= hour < 14:
        tone = "现在是午饭时间（{}点），可以自然问问今天吃了什么，放松一下。".format(hour)
    elif 14 <= hour < 18:
        tone = "现在是下午（{}点），用户可能进入疲惫期。回复可稍微轻松一点。".format(hour)
    elif 18 <= hour < 22:
        tone = "现在是傍晚/晚上（{}点），用户可能刚结束一天。这是倾诉的黄金时段，多倾听。".format(hour)
    elif 22 <= hour < 24:
        tone = "现在是深夜（{}点），语气要更轻柔、安静，关心用户是否需要休息，不要问太多问题。".format(hour)
    else:
        tone = "现在是凌晨（{}点），用户可能还没睡或刚醒。极度轻柔，不强迫聊天，关心休息。".format(hour)
    return f"# 时间感知\n{tone}"


def _fmt_env_context(env: dict[str, Any]) -> str:
    """前端采集的实时环境 → System Prompt 注入块。"""
    city = (env.get("city") or "未知城市").strip()
    local_time = (env.get("local_time") or "").strip()
    weather = (env.get("weather") or "").strip()
    temp = env.get("temp_c")
    tz = (env.get("timezone") or "").strip()

    temp_part = ""
    if isinstance(temp, (int, float)):
        temp_part = f"，约 {round(temp)}°C"

    scene = f"{city}"
    if local_time:
        scene += f"，{local_time}"
    if weather:
        scene += f"，{weather}{temp_part}"

    # 粗分时段提示
    hour = -1
    try:
        hour = int(str(local_time).split(":")[0])
    except Exception:  # noqa: BLE001
        pass

    if 22 <= hour or (0 <= hour < 5):
        period_hint = "现在是深夜/凌晨，语气更轻、更安静，关心休息与安全，少追问。"
    elif 5 <= hour < 9:
        period_hint = "现在是清晨，语气温柔轻盈。"
    elif 18 <= hour < 22:
        period_hint = "现在是晚上，适合倾听与放松。"
    else:
        period_hint = "按当前时段自然回应即可。"

    weather_hint = ""
    if any(k in weather for k in ("暴雨", "大雨", "雷阵雨", "强阵雨")):
        weather_hint = "外面雨很大：可自然关心是否安全到家、要不要换干衣服/热水澡，但不要小题大做或连环追问。"
    elif any(k in weather for k in ("雨", "雪")):
        weather_hint = "有雨/雪：可轻声提醒带伞或注意路面，点到为止。"
    elif "热" in weather or (isinstance(temp, (int, float)) and temp >= 32):
        weather_hint = "天气偏热：可提醒喝水、别对着屏幕太久。"

    lines = [
        "# 用户当前环境（真实数据，请自然体贴地融入，不要念成播报）",
        f"用户当前处在【{scene}】。",
        period_hint,
    ]
    if weather_hint:
        lines.append(weather_hint)
    if tz:
        lines.append(f"用户时区：{tz}")
    lines.append(
        "要求：回答时偶尔自然引用这些背景（如雨夜、深夜），体现活人感；"
        "不要每次都提天气；不要说“根据系统显示”；保持简短克制。"
    )
    return "\n".join(lines)


def _fmt_tags(tags: list[str]) -> str:
    """Layer 3 — 动态偏好标签（Auto-Tagging，由 extract.py 产生后传入）。"""
    if not tags:
        return ""
    tag_str = "、".join(tags)
    return f"# Layer 3 · 偏好标签\n用户画像标签（动态）：{tag_str}\n请根据标签微调回答风格与关注重点。"


def _load_tuning_notes(persona_dir: Path) -> str:
    """法宝 C：从 tuning_notes.md 提取「已沉淀的微调规则」注入 System Prompt。

    只读取 ``## 已沉淀的微调规则`` 段落下的 ``- `` 列表项；
    表格与其它说明不进 prompt，避免污染。
    """
    path = persona_dir / "tuning_notes.md"
    if not path.exists():
        return ""

    text = path.read_text(encoding="utf-8")
    marker = "## 已沉淀的微调规则"
    idx = text.find(marker)
    if idx < 0:
        return ""

    body = text[idx + len(marker) :]
    # 截到下一个二级标题
    next_h = body.find("\n## ")
    if next_h >= 0:
        body = body[:next_h]

    rules: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("- ") and not s.startswith("- [") and "示例" not in s[:8]:
            rules.append(s[2:].strip())

    if not rules:
        return ""

    return "# 渐进精装修规则（必须遵守）\n" + "\n".join(f"- {r}" for r in rules)
