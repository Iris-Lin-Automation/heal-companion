"""Real-world Bridge — 现实桥梁内容池 (MVP 版)

策略
----
- MVP 使用精选静态内容池 + 偏好标签匹配，无需外部 RSS / API。
- 后续可替换 pick_for_user() 的数据源为真实早报/小红书 RSS。
- 每条内容 (BridgeItem) 有若干 tags，与用户 preference_tags 交叉匹配得分。
- 每天最多推送一次，通过 last_bridge_date 防止重复。

用法
----
    from companion.bridge.curated import pick_for_user
    item = pick_for_user(store)
    if item:
        # 将 item.message 自然嵌入 AI 对话
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from companion.memory.store import MemoryStore


@dataclass
class BridgeItem:
    tags: list[str]        # 偏好标签，用于匹配用户画像
    message: str           # 自然融入对话的内容句子（AI 口吻）
    category: str = ""     # 分类：life / study / wellness / fun


# ── 内容池 ────────────────────────────────────────────────────────────
_POOL: list[BridgeItem] = [
    # ── 养生 / 食谱 ──
    BridgeItem(
        tags=["喜欢喝茶", "无咖啡因", "温热食品", "独居"],
        message="对了，刚看到一个做热巧的配方，只要把可可粉加一点肉桂粉冲热牛奶就好了——你这两天好像有点累，感觉挺适合你喝的。",
        category="wellness",
    ),
    BridgeItem(
        tags=["痛经", "生理期", "温热食品"],
        message="查了一下，红糖加两片生姜煮水，喝完肚子会暖一点。你要是这两天不舒服，可以试试，挺简单的。",
        category="wellness",
    ),
    BridgeItem(
        tags=["焦虑", "睡眠", "深度放松"],
        message="看到一个小方法：睡前把手放在胸口，感受自己的呼吸，慢数 4-4-6（吸-屏-呼），很多人说效果比数羊好。",
        category="wellness",
    ),
    BridgeItem(
        tags=["独居", "下班后", "放松"],
        message="刚看到一个说法：下班后 15 分钟什么都不做——不看手机、不刷视频——只是静静待着，对压力恢复很有帮助。",
        category="wellness",
    ),
    BridgeItem(
        tags=["考研", "学习", "疲惫"],
        message="读到一个学习研究：每 50 分钟站起来走动 5 分钟，效率反而比一直坐着高。你今天有没有给自己留出喘息的间隙？",
        category="study",
    ),

    # ── 轻松 / 生活 ──
    BridgeItem(
        tags=["二次元", "动漫", "喜欢科技"],
        message="最近好多人在聊《Solo Leveling》的新季，不知道你有没有在追——画面确实很燃。",
        category="fun",
    ),
    BridgeItem(
        tags=["独居", "猫咪", "喜欢小动物"],
        message="刷到一个猫咪视频：橘猫一脸不屑地推下桌上的杯子，然后直视主人——太能绷了。",
        category="fun",
    ),
    BridgeItem(
        tags=["音乐", "放松", "喜欢听雨声"],
        message="最近有一张纯钢琴雨声混音专辑挺火，叫《Rainy Afternoon》，适合戴耳机放空。",
        category="fun",
    ),
    BridgeItem(
        tags=["独居", "下班后", "晚餐"],
        message="刚看到一个 10 分钟懒人晚餐：藜麦 + 水煮蛋 + 任意蔬菜，撒点盐和橄榄油。一个人吃饭，也可以吃得很舒服。",
        category="life",
    ),
    BridgeItem(
        tags=["考研", "论文", "工作压力"],
        message="看到一个建议：把「我要做完这件事」换成「我今天只需要做第一步」——有时候开头的那一小步，才是最难的。",
        category="study",
    ),

    # ── 情绪支持 ──
    BridgeItem(
        tags=["焦虑", "高压", "PMS情绪低落"],
        message="读到一句话，觉得挺好的：「情绪不需要被解决，只需要被感受到。」不一定有用，但分享给你。",
        category="wellness",
    ),
    BridgeItem(
        tags=["找工作", "毕业", "迷茫"],
        message="看到一个帖子说，很多人在找到方向之前，都经历过一段「什么都不确定」的时期。感觉你现在经历的，很多人都有过。",
        category="life",
    ),
    BridgeItem(
        tags=["失眠", "深夜", "凌晨"],
        message="睡不着的时候可以试试「感恩清单」：在脑子里随便想三件今天还不错的事，哪怕很小——这能帮大脑切换状态。",
        category="wellness",
    ),

    # ── 天气/季节 ──
    BridgeItem(
        tags=["天气", "下雨天", "喜欢听雨声"],
        message="今天应该有雨，如果你不需要外出，其实是个适合待在家里、喝点热的、什么都不用做的好天气。",
        category="life",
    ),
    BridgeItem(
        tags=["天气", "换季", "高敏"],
        message="换季的时候身体会比平时更容易累，如果最近感觉提不起劲，不一定是你的问题，可能只是身体在适应。",
        category="wellness",
    ),
]


def pick_for_user(store: "MemoryStore", force: bool = False) -> BridgeItem | None:
    """根据用户偏好标签，从内容池中挑选今日推送内容。

    Parameters
    ----------
    store:   用户 MemoryStore
    force:   若 True，跳过「每天最多一次」限制（调试用）

    Returns
    -------
    BridgeItem or None（今天已推送过，或无匹配内容时返回 None）
    """
    # 每天最多一次
    if not force:
        last_date = _load_last_date(store)
        if last_date == date.today():
            return None

    # 读取用户偏好标签
    memories = store.list_memories()
    from companion.memory.schema import MemoryKind  # local import 避免循环
    pref_tags: set[str] = set()
    for m in memories:
        if m.kind == MemoryKind.preference:
            # summary 通常是一段描述，简单分词匹配
            pref_tags.update(m.summary.split())

    # 也从 profile.comfort_notes 提取关键词
    profile = store.load_profile()
    if profile.comfort_notes:
        pref_tags.update(profile.comfort_notes.split())

    # 计算匹配分数
    scored: list[tuple[int, BridgeItem]] = []
    for item in _POOL:
        score = 0
        for tag in item.tags:
            if any(tag in pt or pt in tag for pt in pref_tags):
                score += 2
            # 也做模糊匹配（单字关键词）
            for pt in pref_tags:
                for word in tag:
                    if len(word) >= 2 and word in pt:
                        score += 1
        scored.append((score, item))

    # 按分数排序，分数相同则随机
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0] if scored else 0

    # 从最高分组里随机选一条
    candidates = [item for s, item in scored if s >= max(top_score, 1)]
    if not candidates:
        candidates = [random.choice(_POOL)]

    chosen = random.choice(candidates)

    # 记录今日推送日期
    _save_last_date(store)

    return chosen


# ── 持久化：记录最后推送日期 ─────────────────────────────────────────────

def _load_last_date(store: "MemoryStore") -> date | None:
    loader = getattr(store, "load_bridge_date", None)
    if callable(loader):
        return loader()
    path = store.dir / "bridge_last.txt"
    if not path.exists():
        return None
    try:
        return date.fromisoformat(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _save_last_date(store: "MemoryStore") -> None:
    saver = getattr(store, "save_bridge_date", None)
    if callable(saver):
        saver()
        return
    path = store.dir / "bridge_last.txt"
    path.write_text(date.today().isoformat(), encoding="utf-8")
