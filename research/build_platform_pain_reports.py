# -*- coding: utf-8 -*-
"""仅基于 2026-08-06 四份 jsonl：分别产出 B站 / 小红书 SVG 可视化 + 痛点报告。"""

from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "crawler_raw"
OUT_DIR = ROOT / "research" / "reports_2026-08-06"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_DEFS = {
    "付费/通讯费/月卡": [
        "付费", "月卡", "会员", "开通", "充值", "氪", "氪金", "花钱", "通讯费",
        "token", "太贵", "贵", "价格", "退款", "续费", "畅聊", "钱", "68", "128",
        "328", "清零", "套餐", "pro", "订阅",
    ],
    "购买兴趣/种草": [
        "想买", "想要", "从哪买", "在哪里买", "买一个", "购买", "求链接",
        "求教程", "想入坑", "种草", "安利",
    ],
    "建模/审美/动作": [
        "建模", "丑", "好看", "颜值", "脸", "3d", "3D", "2d", "2D", "live2d",
        "Live2D", "表情", "空洞", "木偶", "站桩", "动作", "戳戳", "僵硬", "精致",
        "立绘", "画风",
    ],
    "语音/通话/低屏幕": [
        "语音", "声音", "通话", "音色", "tts", "TTS", "自动播放", "三角",
        "播放", "听", "说话", "耳机", "闹钟", "叫醒",
    ],
    "剧情/等级/沉浸": [
        "弹窗", "等级", "任务", "解锁", "好感", "剧情", "代入", "主线", "女主",
        "身份", "沉浸", "红点", "抽", "卡面", "小剧场", "日常", "乙游",
    ],
    "隐私/数据安全": ["隐私", "暴露", "安全", "数据", "录音", "自己信息", "泄露"],
    "现实/下班/职场倾诉": [
        "下班", "上班", "职场", "工作", "加班", "累", "现实", "陪伴", "倾诉",
        "低耗能", "早安", "失眠", "孤独",
    ],
    "记忆/活人感": [
        "记忆", "记得", "活人感", "真实感", "真实", "替代品", "好玩", "聊什么",
        "联结", "陪伴感", "人设", "人格",
    ],
    "AI感/信任疑虑": [
        "AI骗", "像AI", "人机", "不像人", "假", "骗人", "骗", "机器人", "AI味",
        "怪", "套话", "模板",
    ],
    "硬件/现实载体": ["硬件", "戒指", "手环", "吊坠", "玩偶", "娃娃", "硅胶", "实体", "载体"],
    "关停/续命焦虑": ["关门", "关服", "停运", "跑路", "倒闭", "续命", "活不久", "凉了", "寄了"],
    "客服/售后体验": ["客服", "售后", "退款", "无回应", "不理", "投诉", "骗钱"],
}

INSIGHTS = {
    "付费/通讯费/月卡": "价格与通讯费是付费转化与流失的核心摩擦",
    "建模/审美/动作": "视觉与动作完成度直接影响“愿不愿意继续聊”",
    "现实/下班/职场倾诉": "用户真实需求偏低耗能倾诉，而非恋爱剧本",
    "记忆/活人感": "记得我、不像模板，是长期留存关键",
    "语音/通话/低屏幕": "语音直出/少操作符合高压人群使用场景",
    "剧情/等级/沉浸": "乙游化玩法既吸人也制造压力与打断",
    "AI感/信任疑虑": "套话与“像机器人”会瞬间破功",
    "隐私/数据安全": "倾诉场景对隐私极度敏感",
    "关停/续命焦虑": "产品存续不确定性伤害付费信心",
    "购买兴趣/种草": "仍有明确购买意向，可转化为验证样本",
    "硬件/现实载体": "实体载体是差异化想象，但非当前主因",
    "客服/售后体验": "售后体验会放大付费后悔感",
}


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


def classify(text: str) -> list[str]:
    low = (text or "").lower()
    hits = []
    for name, keywords in CATEGORY_DEFS.items():
        if any(k.lower() in low for k in keywords):
            hits.append(name)
    return hits


def short(text: str, n: int = 90) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return t if len(t) <= n else t[:n] + "…"


def esc(s: str) -> str:
    return html.escape(str(s or ""), quote=True)


def svg_barh(items: list[tuple[str, int]], title: str, width: int = 860) -> str:
    if not items:
        return f"<p>{esc(title)}：无数据</p>"
    row_h = 34
    left = 210
    right = 70
    top = 48
    height = top + row_h * len(items) + 24
    max_v = max(v for _, v in items) or 1
    bar_w = width - left - right
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<rect width="100%" height="100%" fill="#FBF8FF"/>',
        f'<text x="24" y="28" font-size="16" font-family="Segoe UI, Microsoft YaHei, sans-serif" '
        f'fill="#3D2A55" font-weight="600">{esc(title)}</text>',
    ]
    for i, (label, value) in enumerate(items):
        y = top + i * row_h
        w = max(4, int(bar_w * value / max_v))
        parts.append(
            f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" font-size="12" '
            f'font-family="Segoe UI, Microsoft YaHei, sans-serif" fill="#5A4A6E">{esc(label)}</text>'
        )
        parts.append(
            f'<rect x="{left}" y="{y + 4}" width="{w}" height="20" rx="6" fill="#9D80D4"/>'
        )
        parts.append(
            f'<text x="{left + w + 8}" y="{y + 18}" font-size="12" '
            f'font-family="Segoe UI, Microsoft YaHei, sans-serif" fill="#3D2A55">{value}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def analyze_platform(
    name: str,
    slug: str,
    contents: list[dict],
    comments: list[dict],
    id_key: str,
    title_key: str,
    url_key: str,
    content_like_key: str,
    content_comment_key: str,
    comment_parent_key: str,
) -> dict:
    cmap = {str(c.get(id_key)): c for c in contents}
    enriched = []
    for row in comments:
        sid = str(row.get(comment_parent_key) or "")
        src = cmap.get(sid, {})
        text = str(row.get("content") or "")
        cats = classify(text)
        enriched.append(
            {
                "text": text,
                "like": to_int(row.get("like_count")),
                "date": ts_to_date(row.get("create_time")),
                "source_id": sid,
                "source_title": str(src.get(title_key) or sid),
                "source_url": str(src.get(url_key) or ""),
                "source_keyword": str(src.get("source_keyword") or ""),
                "categories": cats,
            }
        )

    relevant = [c for c in enriched if c["categories"]]
    cat_count = Counter(cat for c in relevant for cat in c["categories"])
    cat_likes = Counter()
    for c in relevant:
        for cat in c["categories"]:
            cat_likes[cat] += c["like"]

    keyword_count = Counter(str(c.get("source_keyword") or "未知") for c in contents)
    content_engagement = sorted(
        [
            {
                "title": short(str(c.get(title_key) or ""), 36),
                "likes": to_int(c.get(content_like_key)),
                "comments": to_int(c.get(content_comment_key)),
                "keyword": str(c.get("source_keyword") or ""),
                "url": str(c.get(url_key) or ""),
                "score": to_int(c.get(content_like_key)) + to_int(c.get(content_comment_key)) * 3,
            }
            for c in contents
        ],
        key=lambda x: x["score"],
        reverse=True,
    )

    evidence: dict[str, list[dict]] = defaultdict(list)
    for c in relevant:
        for cat in c["categories"]:
            evidence[cat].append(c)
    for cat in evidence:
        evidence[cat].sort(key=lambda x: x["like"], reverse=True)

    return {
        "name": name,
        "slug": slug,
        "n_contents": len(contents),
        "n_comments": len(enriched),
        "n_relevant": len(relevant),
        "cat_count": cat_count,
        "cat_likes": cat_likes,
        "keyword_count": keyword_count,
        "content_engagement": content_engagement,
        "evidence": evidence,
        "top_liked_comments": sorted(enriched, key=lambda x: x["like"], reverse=True)[:12],
    }


def write_report(data: dict) -> Path:
    name = data["name"]
    slug = data["slug"]
    path = OUT_DIR / f"{slug}_pain_report.md"
    html_path = OUT_DIR / f"{slug}_pain_report.html"

    pain_items = list(data["cat_count"].most_common())
    like_items = [(k, data["cat_likes"][k]) for k, _ in pain_items]
    kw_items = list(data["keyword_count"].most_common())
    heat_items = [(c["title"], c["score"]) for c in data["content_engagement"][:8]]

    # Markdown
    md: list[str] = []
    md.append(f"# {name} AI 陪伴竞品痛点报告（2026-08-06）")
    md.append("")
    md.append("## 数据范围")
    md.append(f"- 内容：{data['n_contents']} 条")
    md.append(f"- 评论：{data['n_comments']} 条")
    md.append(
        f"- 命中痛点分类：{data['n_relevant']} 条"
        f"（{data['n_relevant'] / max(data['n_comments'], 1) * 100:.0f}%）"
    )
    md.append("")
    md.append(f"> 打开同目录 `{slug}_pain_report.html` 可看交互式图表。")
    md.append("")
    md.append("## 痛点排行（按命中条数）")
    md.append("")
    md.append("| 排名 | 痛点 | 命中条数 | 点赞权重 | 解读 |")
    md.append("|---|---|---:|---:|---|")
    for i, (cat, n) in enumerate(pain_items, 1):
        md.append(
            f"| {i} | {cat} | {n} | {data['cat_likes'][cat]} | {INSIGHTS.get(cat, '—')} |"
        )
    md.append("")
    md.append("## 搜索词分布")
    for k, v in kw_items:
        md.append(f"- `{k}` × {v}")
    md.append("")
    md.append("## 各痛点代表评论（按点赞）")
    for cat, _ in pain_items:
        md.append(f"### {cat}")
        for item in data["evidence"][cat][:5]:
            md.append(
                f"- （赞 {item['like']}）{short(item['text'], 140)}  \n"
                f"  来源：[{short(item['source_title'], 40)}]({item['source_url']})"
            )
        md.append("")
    md.append("## 高赞评论速览")
    for item in data["top_liked_comments"]:
        cats = "、".join(item["categories"]) or "未分类"
        md.append(f"- （赞 {item['like']}｜{cats}）{short(item['text'], 140)}")
    md.append("")
    md.append("## 对 heal-companion 的产品启示")
    ranked = [c for c, _ in pain_items[:6]]
    if "付费/通讯费/月卡" in ranked:
        md.append("- 付费叙事要透明：避免通讯费/token 不清；免费层保证核心陪伴体验。")
    if "建模/审美/动作" in ranked:
        md.append("- 视觉先“不破功”：呼吸微动 + 稳定人设，比复杂 Live2D 更优先。")
    if "现实/下班/职场倾诉" in ranked:
        md.append("- 场景锚点放在下班/深夜倾诉，而不是恋爱养成。")
    if "记忆/活人感" in ranked:
        md.append("- 强化三层记忆与 Auto-Tag，让“它记得我”可感知。")
    if "语音/通话/低屏幕" in ranked:
        md.append("- 坚持 Auto-TTS + 懒人胶囊，降低打字负担。")
    if "关停/续命焦虑" in ranked:
        md.append("- 竞品关停焦虑说明用户怕情感资产归零；本地/可导出记忆是信任点。")
    if "AI感/信任疑虑" in ranked:
        md.append("- 严控套话与爹味；语气标签要贴合语境。")
    md.append("")
    path.write_text("\n".join(md), encoding="utf-8")

    # HTML visual report
    rows = "".join(
        f"<tr><td>{i}</td><td>{esc(cat)}</td><td>{n}</td><td>{data['cat_likes'][cat]}</td>"
        f"<td>{esc(INSIGHTS.get(cat, '—'))}</td></tr>"
        for i, (cat, n) in enumerate(pain_items, 1)
    )
    evidence_html = []
    for cat, _ in pain_items:
        evidence_html.append(f"<h3>{esc(cat)}</h3><ul>")
        for item in data["evidence"][cat][:5]:
            evidence_html.append(
                f"<li><strong>赞 {item['like']}</strong> {esc(short(item['text'], 160))}"
                f"<br/><small>来源：<a href=\"{esc(item['source_url'])}\" target=\"_blank\">"
                f"{esc(short(item['source_title'], 48))}</a></small></li>"
            )
        evidence_html.append("</ul>")

    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{esc(name)} 痛点报告 2026-08-06</title>
  <style>
    body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 0; background: linear-gradient(180deg,#F2ECFC,#FFF); color:#2F243D; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 60px; }}
    h1,h2,h3 {{ color:#3D2A55; }}
    .card {{ background: rgba(255,255,255,.78); backdrop-filter: blur(12px); border: 1px solid rgba(157,128,212,.25);
             border-radius: 18px; padding: 16px 18px; margin: 16px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #E8DFF5; padding: 8px 6px; text-align: left; vertical-align: top; }}
    th {{ color:#6B5A82; font-weight: 600; }}
    .meta {{ color:#6B5A82; }}
    a {{ color:#7A62B0; }}
    svg {{ width: 100%; height: auto; display:block; }}
  </style>
</head>
<body>
<main>
  <h1>{esc(name)} AI 陪伴竞品痛点报告</h1>
  <p class="meta">数据日期 2026-08-06 · 内容 {data['n_contents']} · 评论 {data['n_comments']} · 痛点命中 {data['n_relevant']}</p>

  <div class="card">{svg_barh(pain_items, f"{name} · 痛点命中条数")}</div>
  <div class="card">{svg_barh(like_items, f"{name} · 痛点点赞权重")}</div>
  <div class="card">{svg_barh(kw_items, f"{name} · 搜索词分布")}</div>
  <div class="card">{svg_barh(heat_items, f"{name} · 内容热度 Top（赞+评×3）")}</div>

  <div class="card">
    <h2>痛点排行</h2>
    <table>
      <thead><tr><th>#</th><th>痛点</th><th>条数</th><th>赞权</th><th>解读</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>代表评论</h2>
    {''.join(evidence_html)}
  </div>
</main>
</body>
</html>
"""
    html_path.write_text(html_doc, encoding="utf-8")
    return path


def write_index(bili: dict, xhs: dict) -> Path:
    path = OUT_DIR / "INDEX.md"
    path.write_text(
        f"""# 2026-08-06 双平台痛点可视化索引

## 数据源
- B站内容 `{bili['n_contents']}` / 评论 `{bili['n_comments']}`
- 小红书内容 `{xhs['n_contents']}` / 评论 `{xhs['n_comments']}`

## 打开报告
- [B站 Markdown](bili_pain_report.md) · [B站 可视化 HTML](bili_pain_report.html)
- [小红书 Markdown](xhs_pain_report.md) · [小红书 可视化 HTML](xhs_pain_report.html)

## B站 Top 痛点
{chr(10).join(f"- {k}：{v} 条（赞权 {bili['cat_likes'][k]}）" for k,v in bili['cat_count'].most_common(6)) or '- （无明显命中）'}

## 小红书 Top 痛点
{chr(10).join(f"- {k}：{v} 条（赞权 {xhs['cat_likes'][k]}）" for k,v in xhs['cat_count'].most_common(6)) or '- （无明显命中）'}
""",
        encoding="utf-8",
    )
    return path


def main() -> None:
    bili = analyze_platform(
        "B站",
        "bili",
        load_jsonl(RAW / "bili/jsonl/search_contents_2026-08-06.jsonl"),
        load_jsonl(RAW / "bili/jsonl/search_comments_2026-08-06.jsonl"),
        id_key="video_id",
        title_key="title",
        url_key="video_url",
        content_like_key="liked_count",
        content_comment_key="video_comment",
        comment_parent_key="video_id",
    )
    xhs = analyze_platform(
        "小红书",
        "xhs",
        load_jsonl(RAW / "xhs/jsonl/search_contents_2026-08-06.jsonl"),
        load_jsonl(RAW / "xhs/jsonl/search_comments_2026-08-06.jsonl"),
        id_key="note_id",
        title_key="title",
        url_key="note_url",
        content_like_key="liked_count",
        content_comment_key="comment_count",
        comment_parent_key="note_id",
    )
    bp = write_report(bili)
    xp = write_report(xhs)
    ip = write_index(bili, xhs)
    print("OK")
    print(bp)
    print(xp)
    print(ip)


if __name__ == "__main__":
    main()
