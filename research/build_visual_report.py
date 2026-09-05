# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "crawler_raw"
APPSTORE_RAW = ROOT / "research" / "appstore_raw"
TAPTAP_RAW = ROOT / "research" / "taptap_raw"
OUT = ROOT / "research" / "ai_companion_comment_visual_report.html"
SUMMARY = ROOT / "research" / "ai_companion_comment_visual_report_summary.md"
LEGACY_NOTE = Path("D:/Projects/MediaCrawler/database/xhs_note.csv")
LEGACY_COMMENT = Path("D:/Projects/MediaCrawler/database/xhs_note_comment.csv")


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_int(value, default: int = 0) -> int:
    try:
        text = str(value or "").replace(",", "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def ts_to_date(ts) -> str:
    try:
        value = to_int(ts)
        if value > 10_000_000_000:
            value //= 1000
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d")
    except Exception:
        return ""


def iso_to_date(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return text[:10] if len(text) >= 10 else ""


def month_of(date: str) -> str:
    return date[:7] if date and len(date) >= 7 else "未知"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def short(value, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def build_dataset() -> tuple[list[dict], list[dict], dict[str, int], dict[str, int], Counter, Counter, Counter, Counter, defaultdict]:
    b_contents = load_jsonl(RAW / "bili/jsonl/search_contents_2026-08-06.jsonl")
    b_comments = load_jsonl(RAW / "bili/jsonl/search_comments_2026-08-06.jsonl")
    x_contents = load_jsonl(RAW / "xhs/jsonl/search_contents_2026-08-06.jsonl")
    x_comments = load_jsonl(RAW / "xhs/jsonl/search_comments_2026-08-06.jsonl")
    legacy_notes = load_csv(LEGACY_NOTE)
    legacy_comments = load_csv(LEGACY_COMMENT)
    appstore_reviews = load_jsonl(APPSTORE_RAW / "eve_appstore_cn_reviews_recent_pages_1_10_2026-08-06.jsonl")
    taptap_reviews = load_jsonl(TAPTAP_RAW / "eve_taptap_reviews_structured_2026-08-06.jsonl")

    b_map = {str(v.get("video_id")): v for v in b_contents}
    x_map = {str(v.get("note_id")): v for v in x_contents}
    legacy_map = {str(v.get("note_id")): v for v in legacy_notes}

    comments: list[dict] = []

    def add_comment(platform, batch, date, like, text, comment_id, source_id, source_title, source_url, source_keyword, raw_file):
        comments.append(
            {
                "platform": platform,
                "batch": batch,
                "date": date,
                "month": month_of(date),
                "like": like,
                "text": text,
                "comment_id": comment_id,
                "source_id": source_id,
                "source_title": source_title or source_id,
                "source_url": source_url or "",
                "source_keyword": source_keyword or "",
                "raw_file": raw_file,
            }
        )

    for row in b_comments:
        src = b_map.get(str(row.get("video_id")), {})
        add_comment(
            "B站",
            "2026-08-06 新抓",
            ts_to_date(row.get("create_time")),
            to_int(row.get("like_count")),
            str(row.get("content") or ""),
            str(row.get("comment_id") or ""),
            str(row.get("video_id") or ""),
            src.get("title"),
            src.get("video_url"),
            src.get("source_keyword"),
            "research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl",
        )

    for row in x_comments:
        src = x_map.get(str(row.get("note_id")), {})
        add_comment(
            "小红书",
            "2026-08-06 新抓",
            ts_to_date(row.get("create_time")),
            to_int(row.get("like_count")),
            str(row.get("content") or ""),
            str(row.get("comment_id") or ""),
            str(row.get("note_id") or ""),
            src.get("title"),
            src.get("note_url"),
            src.get("source_keyword"),
            "research/crawler_raw/xhs/jsonl/search_comments_2026-08-06.jsonl",
        )

    for row in legacy_comments:
        src = legacy_map.get(str(row.get("note_id")), {})
        add_comment(
            "小红书",
            "历史小红书样本",
            ts_to_date(row.get("create_time")),
            to_int(row.get("like_count")),
            str(row.get("content") or ""),
            str(row.get("comment_id") or ""),
            str(row.get("note_id") or ""),
            src.get("title"),
            src.get("note_url"),
            src.get("source_keyword"),
            "D:/Projects/MediaCrawler/database/xhs_note_comment.csv",
        )

    for row in appstore_reviews:
        title = str(row.get("title") or "").strip()
        content = str(row.get("content") or "").strip()
        text = f"{title}｜{content}" if title and content else title or content
        rating = str(row.get("rating") or "")
        add_comment(
            "App Store CN",
            "2026-08-06 EVE 近500条",
            iso_to_date(row.get("updated")),
            to_int(row.get("vote_sum")),
            text,
            str(row.get("review_id") or ""),
            str(row.get("app_id") or "6499481710"),
            f"EVE App Store 评分 {rating} 星",
            row.get("review_url") or row.get("source_url"),
            f"rating:{rating}",
            "research/appstore_raw/eve_appstore_cn_reviews_recent_pages_1_10_2026-08-06.jsonl",
        )

    for row in taptap_reviews:
        add_comment(
            "TapTap",
            "2026-08-06 EVE 公开评价页",
            ts_to_date(row.get("created_time")),
            to_int(row.get("ups")),
            str(row.get("content") or ""),
            str(row.get("review_id") or ""),
            str(row.get("review_id") or ""),
            f"EVE TapTap 长评｜{row.get('stage_label') or ''}｜score {row.get('score')}",
            row.get("source_url") or row.get("app_review_url"),
            str(row.get("stage_label") or ""),
            "research/taptap_raw/eve_taptap_reviews_structured_2026-08-06.jsonl",
        )

    category_defs = {
        "付费/通讯费/月卡": ["付费", "收费", "月卡", "会员", "开通", "充值", "充钱", "氪", "氪金", "花钱", "通讯费", "token", "太贵", "贵", "价格", "定价", "首月", "退款", "续费", "畅聊", "钱", "68", "128", "328", "清零", "套餐", "pro"],
        "购买兴趣/种草": ["想买", "想要", "想要一个", "从哪买", "在哪里买", "买一个", "购买", "求链接", "求教程", "想入坑", "有点想花钱", "不够花", "需要"],
        "建模/审美/动作": ["建模", "丑", "好看", "颜值", "脸", "3d", "3D", "2d", "2D", "live2d", "Live2D", "表情", "空洞", "木偶", "站桩", "动作", "戳戳", "僵硬", "精致"],
        "语音/通话/低屏幕": ["语音", "声音", "通话", "自动", "手动", "三角", "播放", "听", "说话", "耳机", "闹钟", "叫醒"],
        "剧情/等级/沉浸": ["弹窗", "等级", "任务", "解锁", "好感", "剧情", "代入", "主线", "女主", "身份", "沉浸", "红点", "抽", "卡面", "小剧场", "日常"],
        "隐私/数据安全": ["隐私", "暴露", "信息", "安全", "数据", "录音", "自己信息"],
        "现实/下班/职场倾诉": ["下班", "上班", "职场", "工作", "累", "现实", "陪伴", "倾诉", "低耗能", "早安", "日常"],
        "记忆/活人感": ["记忆", "记得", "活人感", "真实感", "真实", "人类意识", "替代品", "好玩", "聊什么", "联结", "陪伴感"],
        "AI感/信任疑虑": ["AI骗", "像AI", "人机", "不像人", "假", "骗人", "骗", "机器人", "AI味", "怪"],
        "硬件/现实载体": ["硬件", "戒指", "手环", "吊坠", "玩偶", "娃娃", "硅胶", "实体", "载体", "小猫"],
    }
    paid_terms = ["328", "128", "68", "月卡", "通讯费", "畅聊", "token", "氪金", "充值", "充钱", "会员", "付费", "收费", "价格", "定价", "首月", "太贵", "退款", "清零", "套餐", "pro"]

    for item in comments:
        low = item["text"].lower()
        cats = []
        for name, keywords in category_defs.items():
            if any(keyword.lower() in low for keyword in keywords):
                cats.append(name)
        item["categories"] = cats
        item["is_relevant"] = bool(cats)

    relevant = [c for c in comments if c["is_relevant"]]
    platform_counts = Counter(c["platform"] + "｜" + c["batch"] for c in comments)
    platform_rel_counts = Counter(c["platform"] + "｜" + c["batch"] for c in relevant)
    cat_counts = Counter(cat for c in relevant for cat in c["categories"])
    cat_likes = Counter()
    for item in relevant:
        for cat in item["categories"]:
            cat_likes[cat] += item["like"]

    term_counts = Counter()
    term_likes = Counter()
    for item in comments:
        low = item["text"].lower()
        for term in paid_terms:
            if term.lower() in low:
                term_counts[term] += 1
                term_likes[term] += item["like"]

    month_counts = Counter(c["month"] for c in relevant)
    platform_cat = defaultdict(Counter)
    for item in relevant:
        for cat in item["categories"]:
            platform_cat[item["platform"]][cat] += 1

    sources: list[dict] = []
    for v in b_contents:
        sources.append(
            {
                "platform": "B站",
                "title": v.get("title", ""),
                "url": v.get("video_url", ""),
                "id": str(v.get("video_id", "")),
                "keyword": v.get("source_keyword", ""),
                "likes": to_int(v.get("liked_count")),
                "comments": to_int(v.get("video_comment")),
                "plays": to_int(v.get("video_play_count")),
            }
        )
    for v in x_contents:
        sources.append(
            {
                "platform": "小红书",
                "title": v.get("title", ""),
                "url": v.get("note_url", ""),
                "id": str(v.get("note_id", "")),
                "keyword": v.get("source_keyword", ""),
                "likes": to_int(v.get("liked_count")),
                "comments": to_int(v.get("comment_count")),
                "plays": 0,
            }
        )
    for v in legacy_notes:
        sources.append(
            {
                "platform": "小红书",
                "title": v.get("title", ""),
                "url": v.get("note_url", ""),
                "id": str(v.get("note_id", "")),
                "keyword": v.get("source_keyword", ""),
                "likes": to_int(v.get("liked_count")),
                "comments": to_int(v.get("comment_count")),
                "plays": 0,
            }
        )
    if appstore_reviews:
        sources.append(
            {
                "platform": "App Store CN",
                "title": "EVE - AI 伴侣 App Store 中国区近500条用户评价 RSS",
                "url": "https://apps.apple.com/cn/app/eve-ai-%E4%BC%B4%E4%BE%A3/id6499481710?see-all=reviews&platform=iphone",
                "id": "6499481710",
                "keyword": "App Store reviews",
                "likes": 0,
                "comments": len(appstore_reviews),
                "plays": 0,
            }
        )
    for row in taptap_reviews:
        sources.append(
            {
                "platform": "TapTap",
                "title": f"EVE TapTap 长评｜{row.get('author_name') or row.get('review_id')}",
                "url": row.get("source_url", ""),
                "id": str(row.get("review_id", "")),
                "keyword": row.get("stage_label", ""),
                "likes": to_int(row.get("ups")),
                "comments": to_int(row.get("comments")),
                "plays": to_int(row.get("pv_total")),
            }
        )

    stats = {
        "b_comments": len(b_comments),
        "b_contents": len(b_contents),
        "x_comments": len(x_comments),
        "x_contents": len(x_contents),
        "legacy_comments": len(legacy_comments),
        "legacy_notes": len(legacy_notes),
        "appstore_reviews": len(appstore_reviews),
        "taptap_reviews": len(taptap_reviews),
    }
    return comments, sources, stats, category_defs, platform_counts, platform_rel_counts, cat_counts, cat_likes, term_counts, term_likes, month_counts, platform_cat


def bar_rows(counter: Counter, max_items: int | None = None, color: str = "#7c5cff") -> str:
    items = counter.most_common(max_items)
    if not items:
        return '<p class="empty">暂无命中</p>'
    max_value = max(v for _, v in items) or 1
    rows = []
    for key, value in items:
        pct = max(4, round(value / max_value * 100, 1))
        rows.append(
            f'<div class="bar-row"><div class="bar-label">{esc(key)}</div><div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{color}"></div></div><div class="bar-value">{value}</div></div>'
        )
    return "\n".join(rows)


def build_html() -> None:
    comments, sources, stats, category_defs, platform_counts, platform_rel_counts, cat_counts, cat_likes, term_counts, term_likes, month_counts, platform_cat = build_dataset()
    relevant = [c for c in comments if c["is_relevant"]]
    paid_related = [c for c in relevant if "付费/通讯费/月卡" in c["categories"]]

    for item in relevant:
        item["score"] = (
            item["like"]
            + (80 if "付费/通讯费/月卡" in item["categories"] else 0)
            + (60 if "购买兴趣/种草" in item["categories"] else 0)
            + (45 if "建模/审美/动作" in item["categories"] else 0)
            + (35 if "语音/通话/低屏幕" in item["categories"] else 0)
            + (25 if "记忆/活人感" in item["categories"] else 0)
        )
    top_comments = sorted(relevant, key=lambda c: c["score"], reverse=True)[:56]
    source_top = sorted(sources, key=lambda x: (x["likes"] + x["comments"] * 3 + x["plays"] // 100), reverse=True)[:24]

    def matrix() -> str:
        cats = list(category_defs.keys())
        lines = ['<table class="data-table compact"><thead><tr><th>平台</th>' + "".join(f"<th>{esc(c)}</th>" for c in cats) + "</tr></thead><tbody>"]
        for p in ["B站", "小红书"]:
            lines.append("<tr><td><strong>" + esc(p) + "</strong></td>" + "".join(f"<td>{platform_cat[p][c]}</td>" for c in cats) + "</tr>")
        lines.append("</tbody></table>")
        return "".join(lines)

    def comment_cards(rows: list[dict]) -> str:
        chunks = []
        for item in rows:
            cats = "".join(f'<span class="pill">{esc(cat)}</span>' for cat in item["categories"])
            if item["source_url"]:
                source = f'<a href="{esc(item["source_url"])}" target="_blank">{esc(short(item["source_title"], 70))}</a>'
            else:
                source = esc(short(item["source_title"], 70))
            chunks.append(
                f'''<article class="comment-card" data-platform="{esc(item['platform'])}" data-cats="{esc(' '.join(item['categories']))}">
  <div class="comment-meta"><span>{esc(item['platform'])}</span><span>{esc(item['batch'])}</span><span>{esc(item['date'])}</span><span>赞 {item['like']}</span></div>
  <p class="quote">{esc(short(item['text'], 280))}</p>
  <div class="pill-row">{cats}</div>
  <div class="source-line">出处：{source}<br><code>{esc(item['source_id'])}</code> · comment_id <code>{esc(item['comment_id'])}</code><br>原始文件：<code>{esc(item['raw_file'])}</code></div>
</article>'''
            )
        return "\n".join(chunks)

    def source_table(rows: list[dict]) -> str:
        body = []
        for item in rows:
            if item["url"]:
                link = f'<a href="{esc(item["url"])}" target="_blank">{esc(short(item["title"], 80))}</a>'
            else:
                link = esc(short(item["title"], 80))
            body.append(f'<tr><td>{esc(item["platform"])}</td><td>{link}<br><code>{esc(item["id"])}</code></td><td>{esc(item["keyword"])}</td><td>{item["likes"]}</td><td>{item["comments"]}</td><td>{item["plays"] or ""}</td></tr>')
        return '<table class="data-table"><thead><tr><th>平台</th><th>来源</th><th>搜索词</th><th>赞</th><th>评论</th><th>播放</th></tr></thead><tbody>' + "".join(body) + "</tbody></table>"

    insights = [
        ("不要做“通讯费/token 消耗感”", "付费相关命中集中在 EVE 评论，328/月、68/月、通讯费和清零机制会被用户直接拿来和乙游月卡、AI 工具、真人服务比较。", "订阅权益应是长记忆、自动语音、主动关心、关系回顾；不要在倾诉中段弹付费。"),
        ("先做高审美 2D/Live2D，不硬卷 3D", "建模/审美是强痛点，B站高赞明确出现“想要 2D 有自己美术的 AI 陪聊”。", "用 Live2D 半身、表情/呼吸/说话动作，避开低质量 3D 的站桩和僵硬。"),
        ("把“想买/种草”当作硬件长线信号", "历史小红书样本里高赞出现“从哪买”“真想要”等购买兴趣，说明具身/实体陪伴有好奇心。", "第一阶段先做 App 内 soul，第二阶段接锁屏、耳机、手表、桌面组件，再考虑实体。"),
        ("关系系统藏在体验后面", "用户反感任务/主线/等级抢走沉浸，但认可 24 小时互动、真实感和记忆。", "关系慢热可选，外显为“他记得你”，不要外显为红点、等级、弹窗。"),
    ]

    html_doc = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AI 陪伴竞品评论可视化报告</title>
<style>
:root{{--bg:#f6f3ef;--ink:#221f1c;--muted:#746c63;--line:#ded6cc;--card:#fffaf4;--accent:#6e56cf;--accent2:#d05a3f;--green:#2f8f71;--gold:#b7791f}}
*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}}a{{color:#4f3bb5;text-decoration:none}}a:hover{{text-decoration:underline}}
.hero{{padding:48px 32px 28px;background:linear-gradient(135deg,#fffaf4 0%,#efe8ff 48%,#e7f4ee 100%);border-bottom:1px solid var(--line)}}.hero-inner{{max-width:1180px;margin:auto}}h1{{margin:0 0 12px;font-size:34px;letter-spacing:0}}.subtitle{{max-width:900px;margin:0;color:var(--muted);font-size:16px}}.wrap{{max-width:1180px;margin:0 auto;padding:24px 28px 60px}}.grid{{display:grid;gap:16px}}.grid-4{{grid-template-columns:repeat(4,minmax(0,1fr))}}.grid-2{{grid-template-columns:repeat(2,minmax(0,1fr))}}.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px;box-shadow:0 8px 24px rgba(58,42,20,.05)}}.metric .num{{font-size:30px;font-weight:760}}.metric .label{{color:var(--muted);margin-top:4px}}h2{{margin:34px 0 12px;font-size:23px}}h3{{margin:0 0 12px;font-size:16px}}.note{{color:var(--muted);font-size:13px;margin-top:8px}}.bar-row{{display:grid;grid-template-columns:150px 1fr 58px;align-items:center;gap:10px;margin:10px 0}}.bar-label{{font-size:13px;color:#3d3730;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.bar-track{{height:12px;background:#ebe3d8;border-radius:999px;overflow:hidden}}.bar-fill{{height:100%;border-radius:999px}}.bar-value{{font-variant-numeric:tabular-nums;color:var(--muted);text-align:right}}.data-table{{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden}}.data-table th,.data-table td{{border-bottom:1px solid var(--line);padding:10px;vertical-align:top;text-align:left}}.data-table th{{background:#eee6dd;font-weight:700}}.data-table tr:last-child td{{border-bottom:0}}.compact th,.compact td{{text-align:center;font-size:12px;padding:8px}}.compact td:first-child,.compact th:first-child{{text-align:left}}.comment-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.comment-card{{background:#fffdf9;border:1px solid var(--line);border-radius:8px;padding:14px}}.comment-meta{{display:flex;flex-wrap:wrap;gap:8px;color:var(--muted);font-size:12px;margin-bottom:8px}}.comment-meta span{{background:#f1ebe3;padding:3px 7px;border-radius:999px}}.quote{{margin:0 0 10px;font-size:14px}}.pill-row{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}}.pill{{color:#5039a5;background:#eee8ff;border:1px solid #ddd2ff;border-radius:999px;padding:3px 8px;font-size:12px}}.source-line{{color:var(--muted);font-size:12px;border-top:1px dashed var(--line);padding-top:8px;margin-top:8px}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;background:#f0e8df;padding:1px 4px;border-radius:4px}}.insight{{display:grid;grid-template-columns:220px 1fr 1fr;gap:12px;padding:14px;border-bottom:1px solid var(--line)}}.insight:last-child{{border-bottom:0}}.insight strong{{color:#3d2d8a}}.toolbar{{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 16px}}.filter-btn{{border:1px solid var(--line);background:#fffaf4;border-radius:999px;padding:8px 12px;cursor:pointer;color:#3c342d}}.filter-btn.active{{background:#2e2a25;color:#fff}}.footer{{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--line);padding-top:16px}}
@media(max-width:900px){{.grid-4,.grid-2,.comment-grid{{grid-template-columns:1fr}}.bar-row{{grid-template-columns:118px 1fr 44px}}.insight{{grid-template-columns:1fr}}h1{{font-size:27px}}.wrap{{padding:18px}}}}
</style>
</head>
<body>
<header class="hero"><div class="hero-inner"><h1>AI 陪伴竞品评论可视化报告</h1><p class="subtitle">整合 2026-08-06 新抓 B站/小红书样本，以及历史小红书样本。重点观察已付费、开月卡、通讯费、建模、语音、沉浸、购买兴趣和现实陪伴相关评论。每条证据都保留原始出处、comment_id 和原始文件路径。</p></div></header>
<main class="wrap">
<section class="grid grid-4"><div class="card metric"><div class="num">{len(comments)}</div><div class="label">评论总数</div></div><div class="card metric"><div class="num">{len(relevant)}</div><div class="label">痛点/机会命中评论</div></div><div class="card metric"><div class="num">{len(paid_related)}</div><div class="label">付费/月卡/通讯费相关</div></div><div class="card metric"><div class="num">{sum(c['like'] for c in relevant)}</div><div class="label">相关评论点赞合计</div></div></section>
<h2>1. 数据来源结构</h2><section class="grid grid-2"><div class="card"><h3>评论样本量</h3>{bar_rows(platform_counts,color="#6e56cf")}<p class="note">来源：B站/小红书 2026-08-06 jsonl + 历史 MediaCrawler 小红书 CSV。</p></div><div class="card"><h3>相关评论命中量</h3>{bar_rows(platform_rel_counts,color="#2f8f71")}<p class="note">命中任一类：付费、购买兴趣、建模、语音、剧情沉浸、隐私、现实陪伴、记忆、硬件。</p></div></section>
<h2>2. 痛点类型分布</h2><section class="grid grid-2"><div class="card"><h3>按评论条数</h3>{bar_rows(cat_counts,color="#d05a3f")}</div><div class="card"><h3>按点赞权重</h3>{bar_rows(cat_likes,color="#b7791f")}<p class="note">点赞权重更接近“社区共鸣度”，不是绝对市场规模。</p></div></section>
<h2>3. 付费关键词热度</h2><section class="grid grid-2"><div class="card"><h3>关键词出现次数</h3>{bar_rows(term_counts,17,color="#6e56cf")}</div><div class="card"><h3>关键词点赞权重</h3>{bar_rows(term_likes,17,color="#d05a3f")}</div></section>
<h2>4. 时间分布</h2><div class="card">{bar_rows(month_counts,color="#2f8f71")}<p class="note">历史样本与新抓样本混合展示，适合观察讨论是否持续存在。</p></div>
<h2>5. 平台 x 痛点矩阵</h2><div class="card">{matrix()}<p class="note">B站更集中呈现测评/吐槽/价格锚点，小红书更集中呈现入坑、套餐、畅聊卡、玩家日常和种草/避雷。</p></div>
<h2>6. 产品机会矩阵</h2><div class="card">{''.join(f'<div class="insight"><strong>{esc(t)}</strong><span>{esc(e)}</span><span>{esc(a)}</span></div>' for t,e,a in insights)}</div>
<h2>7. 高赞评论证据墙</h2><div class="toolbar"><button class="filter-btn active" data-filter="all">全部</button><button class="filter-btn" data-filter="付费/通讯费/月卡">付费/月卡</button><button class="filter-btn" data-filter="购买兴趣/种草">购买兴趣</button><button class="filter-btn" data-filter="建模/审美/动作">建模</button><button class="filter-btn" data-filter="语音/通话/低屏幕">语音</button><button class="filter-btn" data-filter="剧情/等级/沉浸">沉浸</button><button class="filter-btn" data-filter="小红书">小红书</button><button class="filter-btn" data-filter="B站">B站</button></div><section class="comment-grid" id="commentGrid">{comment_cards(top_comments)}</section>
<h2>8. 原始帖子 / 视频来源 Top 索引</h2>{source_table(source_top)}
<div class="footer"><p>原始证据索引：<a href="source_attributed_comment_evidence_2026-08-06.md">source_attributed_comment_evidence_2026-08-06.md</a></p><p>主调研文档：<a href="ai_companion_paid_user_market_research.md">ai_companion_paid_user_market_research.md</a></p><p>报告生成时间：2026-08-06。所有评论均来自公开可访问页面或本地已授权 MediaCrawler 采集结果；小红书评论使用笔记 URL + comment_id 追溯，B站评论使用视频 URL + comment_id 追溯。</p></div>
</main><script>const buttons=document.querySelectorAll('.filter-btn');const cards=document.querySelectorAll('.comment-card');buttons.forEach(btn=>btn.addEventListener('click',()=>{{buttons.forEach(b=>b.classList.remove('active'));btn.classList.add('active');const f=btn.dataset.filter;cards.forEach(card=>{{if(f==='all'||card.dataset.platform.includes(f)||card.dataset.cats.includes(f))card.style.display='';else card.style.display='none';}});}}));</script></body></html>'''

    OUT.write_text(html_doc, encoding="utf-8")

    summary = [
        "# AI 陪伴竞品评论可视化报告摘要",
        "",
        "- 报告文件：`research/ai_companion_comment_visual_report.html`",
        f"- 评论总数：{len(comments)}",
        f"- 相关命中评论：{len(relevant)}",
        f"- 付费/月卡/通讯费相关：{len(paid_related)}",
        f"- B站新抓：{stats['b_comments']} 条评论，{stats['b_contents']} 个视频",
        f"- 小红书新抓：{stats['x_comments']} 条评论，{stats['x_contents']} 篇笔记",
        f"- 小红书历史样本：{stats['legacy_comments']} 条评论，{stats['legacy_notes']} 篇笔记",
        "",
        "## Top 痛点",
        "",
    ]
    for key, value in cat_counts.most_common():
        summary.append(f"- {key}：{value} 条，点赞权重 {cat_likes[key]}")
    summary += ["", "## Top 付费关键词", ""]
    for key, value in term_counts.most_common(12):
        summary.append(f"- {key}：{value} 次，点赞权重 {term_likes[key]}")
    SUMMARY.write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_html()
    print(OUT)
    print(SUMMARY)
