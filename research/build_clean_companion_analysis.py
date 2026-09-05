# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "ai_companion_clean_analysis_report_2026-08-06.md"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def to_int(value) -> int:
    try:
        return int(float(str(value or "0").replace(",", "")))
    except Exception:
        return 0


def ts_date(value) -> str:
    try:
        ts = to_int(value)
        if ts > 10_000_000_000:
            ts //= 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def iso_date(value) -> str:
    text = str(value or "")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return text[:10]


def short(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def bullet_escape(text: str) -> str:
    return short(text).replace("\n", " ").replace("|", "｜")


def main() -> None:
    bili_contents = load_jsonl(ROOT / "research/crawler_raw/bili/jsonl/search_contents_2026-08-06.jsonl")
    bili_comments = load_jsonl(ROOT / "research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl")
    xhs_contents = load_jsonl(ROOT / "research/crawler_raw/xhs/jsonl/search_contents_2026-08-06.jsonl")
    xhs_comments = load_jsonl(ROOT / "research/crawler_raw/xhs/jsonl/search_comments_2026-08-06.jsonl")
    appstore = load_jsonl(ROOT / "research/appstore_raw/eve_appstore_cn_reviews_recent_pages_1_10_2026-08-06.jsonl")
    taptap = load_jsonl(ROOT / "research/taptap_raw/eve_taptap_reviews_structured_2026-08-06.jsonl")
    taptap_hits = load_jsonl(ROOT / "research/taptap_raw/eve_taptap_reviews_public_page_2026-08-06.jsonl")

    wrong_source_terms = ["硅胶娃娃", "AI偶像", "爱心代码", "程序员剧"]
    vertical_terms = ["EVE", "AI陪伴", "AI伴侣", "AI男友", "AI恋爱", "AI谈恋爱", "月卡", "通讯费", "畅聊卡"]
    paid_terms = ["月卡", "通讯费", "畅聊", "付费", "收费", "充值", "充钱", "氪", "太贵", "价格", "定价", "退款", "68", "128", "328", "套餐", "会员", "清零"]
    design_terms = ["建模", "丑", "颜值", "好看", "脸", "3d", "3D", "2d", "2D", "Live2D", "动作", "表情", "僵硬", "卡面"]
    voice_terms = ["语音", "通话", "声音", "自动", "播放", "电话", "听", "说话", "打断"]
    immersion_terms = ["弹窗", "等级", "任务", "好感", "剧情", "沉浸", "主线", "红点", "解锁", "排队", "服务器"]
    memory_terms = ["记忆", "记得", "活人感", "真实", "人机", "AI味", "不像人", "长期陪伴", "陪伴感"]

    bili_map = {str(row.get("video_id")): row for row in bili_contents}
    xhs_map = {str(row.get("note_id")): row for row in xhs_contents}

    evidence: list[dict] = []

    def classify(text: str) -> list[str]:
        cats = []
        checks = [
            ("付费机制", paid_terms),
            ("审美/建模", design_terms),
            ("语音/通话", voice_terms),
            ("沉浸/任务", immersion_terms),
            ("记忆/活人感", memory_terms),
        ]
        low = text.lower()
        for name, terms in checks:
            if any(term.lower() in low for term in terms):
                cats.append(name)
        return cats

    def add(platform: str, source_type: str, date: str, like: int, text: str, source_title: str, source_url: str, source_id: str, raw_file: str, rating: str = "") -> None:
        cats = classify(text)
        if not cats:
            return
        evidence.append(
            {
                "platform": platform,
                "source_type": source_type,
                "date": date,
                "like": like,
                "text": text,
                "source_title": source_title,
                "source_url": source_url,
                "source_id": source_id,
                "raw_file": raw_file,
                "rating": rating,
                "categories": cats,
                "paid_proxy": any(term in text for term in paid_terms),
            }
        )

    cleaned_bili_videos = []
    dropped_bili_videos = []
    for row in bili_contents:
        title = str(row.get("title") or "")
        if any(term in title for term in wrong_source_terms):
            dropped_bili_videos.append(row)
            continue
        if any(term in title or term in str(row.get("source_keyword") or "") for term in vertical_terms):
            cleaned_bili_videos.append(row)
    cleaned_bili_ids = {str(row.get("video_id")) for row in cleaned_bili_videos}

    for row in bili_comments:
        if str(row.get("video_id")) not in cleaned_bili_ids:
            continue
        src = bili_map.get(str(row.get("video_id")), {})
        add(
            "B站",
            "EVE测评视频评论",
            ts_date(row.get("create_time")),
            to_int(row.get("like_count")),
            str(row.get("content") or ""),
            str(src.get("title") or ""),
            str(src.get("video_url") or ""),
            str(row.get("comment_id") or row.get("video_id") or ""),
            "research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl",
        )

    for row in xhs_comments:
        src = xhs_map.get(str(row.get("note_id")), {})
        title = str(src.get("title") or "")
        if any(term in title or term in str(src.get("source_keyword") or "") for term in vertical_terms):
            add(
                "小红书",
                "EVE月卡/畅聊卡笔记评论",
                ts_date(row.get("create_time")),
                to_int(row.get("like_count")),
                str(row.get("content") or ""),
                title,
                str(src.get("note_url") or ""),
                str(row.get("comment_id") or row.get("note_id") or ""),
                "research/crawler_raw/xhs/jsonl/search_comments_2026-08-06.jsonl",
            )

    for row in appstore:
        title = str(row.get("title") or "")
        content = str(row.get("content") or "")
        add(
            "App Store CN",
            "EVE公开商店评价",
            iso_date(row.get("updated")),
            to_int(row.get("vote_sum")),
            f"{title}｜{content}",
            f"EVE App Store {row.get('rating')}星评价",
            str(row.get("review_url") or row.get("source_url") or ""),
            str(row.get("review_id") or ""),
            "research/appstore_raw/eve_appstore_cn_reviews_recent_pages_1_10_2026-08-06.jsonl",
            str(row.get("rating") or ""),
        )

    for row in taptap:
        add(
            "TapTap",
            "EVE公开长评",
            ts_date(row.get("created_time")),
            to_int(row.get("ups")),
            str(row.get("content") or ""),
            f"EVE TapTap 长评 score {row.get('score')}",
            str(row.get("source_url") or ""),
            str(row.get("review_id") or ""),
            "research/taptap_raw/eve_taptap_reviews_structured_2026-08-06.jsonl",
            str(row.get("score") or ""),
        )

    evidence.sort(
        key=lambda row: row["like"]
        + (120 if row["platform"] == "TapTap" else 0)
        + (90 if row["paid_proxy"] else 0)
        + (40 if "App Store" in row["platform"] and row["rating"] in {"1", "2"} else 0),
        reverse=True,
    )

    platform_counts = Counter(row["platform"] for row in evidence)
    category_counts = Counter(cat for row in evidence for cat in row["categories"])
    paid_by_platform = Counter(row["platform"] for row in evidence if row["paid_proxy"])
    appstore_ratings = Counter(str(row.get("rating") or "") for row in appstore)

    top_by_category: dict[str, list[dict]] = defaultdict(list)
    for row in evidence:
        for cat in row["categories"]:
            if len(top_by_category[cat]) < 5:
                top_by_category[cat].append(row)

    lines = [
        "# AI 情感陪伴竞品评论清洗分析报告",
        "",
        "生成日期：2026-08-06",
        "",
        "## 这次修正了什么",
        "",
        "- 剔除了跑偏 B站来源：硅胶娃娃工厂、AI偶像作品、程序员爱心代码等泛 AI/泛亲密关系内容。",
        "- 主证据只保留 EVE、AI陪伴、AI伴侣、AI男友、月卡、通讯费、畅聊卡等垂直语境。",
        "- 可视化报告暂停，下面只输出对产品开发有用的结论和证据索引。",
        "",
        "## 数据口径",
        "",
        f"- App Store CN：EVE 近 500 条公开商店评价；评分分布 {dict(sorted(appstore_ratings.items()))}。",
        f"- TapTap：EVE 公开评价页结构化长评 {len(taptap)} 条，页面内高信号文本 {len(taptap_hits)} 条。",
        f"- 小红书：EVE 月卡/畅聊卡/避雷/充值相关笔记 {len(xhs_contents)} 篇，评论 {len(xhs_comments)} 条。",
        f"- B站：原抓取 {len(bili_contents)} 个视频，清洗后保留 {len(cleaned_bili_videos)} 个 EVE/AI陪伴测评视频，剔除 {len(dropped_bili_videos)} 个跑偏视频。",
        f"- 清洗后进入分析的高信号证据：{len(evidence)} 条；其中付费代理证据 {sum(1 for row in evidence if row['paid_proxy'])} 条。",
        "",
        "## 平台分布",
        "",
    ]
    for platform, count in platform_counts.most_common():
        lines.append(f"- {platform}：{count} 条高信号证据，其中付费代理 {paid_by_platform[platform]} 条")

    lines += ["", "## 痛点排序", ""]
    for cat, count in category_counts.most_common():
        lines.append(f"- {cat}：{count} 条")

    lines += [
        "",
        "## 核心判断",
        "",
        "1. EVE 验证了需求，但也验证了一个大坑：当产品承诺“现实陪伴/长期陪伴”，用户会把聊天中断、通讯费不足、弹窗收费理解成关系被打断，而不是普通游戏付费。",
        "2. 高付费女性不是不付费，她们是不愿意在“还没建立关系”时被按句收费。她们能接受月卡、会员、卡面、剧情、外观、长期记忆，但很反感情绪倾诉中途被提醒余额。",
        "3. 低质量 3D 对女性向陪伴是减分项。评论里对“建模一般、僵硬、卡面丑、动作不自然”的情绪非常强，反过来说明你想做 2D/Live2D 是一个更适合个人开发者的切口。",
        "4. 产品不应该从“乙游身份/异世界剧情”开场，而应该从“现实生活里这个人一直在”开场。乙游强剧情能赚钱，但它解决的是幻想消费；你想做的是下班后低能量陪伴，两者开场机制不一样。",
        "5. 你要避免和大厂正面打营销、抽卡、3D、剧情产能。个人开发更适合做一个窄但深的体验：固定一个高审美 2D 男性形象、自动语音回复、强记忆、低打扰、现实日程陪伴。",
        "",
        "## 最有价值的产品机会",
        "",
        "### 1. 付费设计：卖稳定陪伴，不卖通讯费焦虑",
        "",
        "建议 MVP 不做按句 token 余额露出。可做 3 档订阅：",
        "",
        "- 免费：每日固定陪伴额度，能完整体验 1 次下班倾诉和 1 次晚安。",
        "- 月卡：无限/高额度文字，自动语音回复，长期记忆，日程/情绪回顾。",
        "- 高阶：更高质量语音、专属 Live2D 动作、旅行/出差模式、私密记忆库、关系月报。",
        "",
        "### 2. 视觉：先做 2D/Live2D 半身，不做 3D 男主",
        "",
        "原因不是 2D 一定高级，而是女性向审美容错率很低。个人开发做 3D 容易落入 EVE 被骂的区间；Live2D 能把成本集中在脸、眼神、呼吸、嘴型、表情和触摸反馈上。",
        "",
        "### 3. 交互：语音优先，减少手机屏幕负担",
        "",
        "你前面说的“上班累了还要点三角播放”很关键。MVP 里应该默认：用户发文字或语音，他自动用语音回；文字只是辅助字幕。这样你的产品从第一天就和普通聊天框分开。",
        "",
        "### 4. 关系系统：慢热但不要游戏化弹窗",
        "",
        "关系可以升温，但不要红点、等级、任务弹窗压到聊天前面。更好的表达是：他记得你昨天提到的事、下班时间主动问一句、旅行时根据定位/天气/行程问候。",
        "",
        "### 5. 现实载体：先做轻载体，不急着硬件",
        "",
        "戒指、手环、桌面小设备有想象空间，但硬件会拉高现金流和供应链风险。更现实的路线：先做桌面小窗、锁屏组件、耳机语音、Apple Watch/安卓手表通知；验证高净值女性是否真的愿意为“现实进入感”多付钱。",
        "",
        "## 不建议你现在做的方向",
        "",
        "- 不要先做心理咨询/疗愈式产品：市场更窄，还容易碰医疗合规和效果承诺。",
        "- 不要做多男主大世界：内容产能会把个人开发拖垮，也会被用户拿去和乙游比。",
        "- 不要做显性的虚拟恋人擦边：付费强但竞争红海、平台审核和用户信任成本都高。",
        "- 不要先做实体硬件：除非已经有小批量供应链和预售转化，否则会过早耗尽精力。",
        "",
        "## 证据摘录",
        "",
    ]

    for cat in ["付费机制", "审美/建模", "语音/通话", "沉浸/任务", "记忆/活人感"]:
        lines += [f"### {cat}", ""]
        for row in top_by_category.get(cat, [])[:5]:
            lines.append(
                f"- {row['platform']}｜{row['source_type']}｜赞/有用 {row['like']}｜{row['date']}｜{', '.join(row['categories'])}"
            )
            lines.append(f"  - 摘要：{bullet_escape(row['text'])}")
            lines.append(f"  - 来源：{row['source_url']}")
            lines.append(f"  - source_id/comment_id：`{row['source_id']}`；原始文件：`{row['raw_file']}`")
        lines.append("")

    lines += [
        "## 结论：现在该怎么开发",
        "",
        "你的定位建议收窄成：面向国内有稳定收入、熟悉女性向内容、但不想被乙游任务和抽卡消耗的女性，做一个现实系、低打扰、语音优先、2D/Live2D 男性 AI 陪伴。",
        "",
        "第一版只需要证明三件事：",
        "",
        "1. 她愿不愿意每天打开 5-10 分钟倾诉。",
        "2. 她是否觉得这个人“记得我、懂我、不会突然打断我”。",
        "3. 她是否愿意为自动语音、长期记忆、Live2D 陪伴和现实日程陪伴付月费。",
        "",
        "如果这三件事成立，再做旅行模式、手表/戒指/桌面载体。不要反过来先做大系统。",
    ]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)
    print(f"evidence={len(evidence)} paid_proxy={sum(1 for row in evidence if row['paid_proxy'])}")
    print(f"bili_kept={len(cleaned_bili_videos)} bili_dropped={len(dropped_bili_videos)}")


if __name__ == "__main__":
    main()
