# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "taptap_raw"
HTML_PATH = RAW / "eve_taptap_review_page_2026-08-06.html"
OUT_JSONL = RAW / "eve_taptap_reviews_public_page_2026-08-06.jsonl"
OUT_STRUCTURED_JSONL = RAW / "eve_taptap_reviews_structured_2026-08-06.jsonl"
OUT_MD = RAW / "eve_taptap_reviews_public_summary_2026-08-06.md"


def walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")


def short(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def deref_once(data: list, value: Any) -> Any:
    if isinstance(value, int) and 0 <= value < len(data):
        return data[value]
    return value


def resolve_path(data: list, value: Any, path: list[str]) -> Any:
    current = deref_once(data, value)
    for key in path:
        if not isinstance(current, dict):
            return None
        current = deref_once(data, current.get(key))
    return current


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'<script[^>]+id="__NUXT_DATA__"[^>]*>(.*?)</script>',
        html,
        flags=re.S | re.I,
    )
    if not match:
        raise RuntimeError("No __NUXT_DATA__ script found")
    data = json.loads(match.group(1))

    keywords = [
        "通讯费",
        "月卡",
        "氪",
        "充值",
        "付费",
        "建模",
        "好感度",
        "畅聊",
        "328",
        "68",
        "10点",
        "卸载",
        "活人感",
    ]

    hits: list[dict[str, Any]] = []
    seen = set()
    for path, value in walk(data):
        if not isinstance(value, str):
            continue
        text = value.strip()
        if len(text) < 20:
            continue
        if not any(k in text for k in keywords):
            continue
        key = text[:120]
        if key in seen:
            continue
        seen.add(key)
        hits.append(
            {
                "platform": "TapTap",
                "app": "EVE",
                "source_url": "https://www.taptap.cn/app/788667/review",
                "path": path,
                "content": text,
                "matched_keywords": [k for k in keywords if k in text],
            }
        )

    RAW.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in hits) + "\n",
        encoding="utf-8",
    )

    structured: list[dict[str, Any]] = []
    seen_review_ids = set()
    for i, value in enumerate(data):
        if not isinstance(value, dict):
            continue
        if not {"id_str", "review", "stat", "author"}.issubset(value.keys()):
            continue
        row_id = resolve_path(data, value, ["id_str"])
        created_time = resolve_path(data, value, ["created_time"])
        edited_time = resolve_path(data, value, ["edited_time"])
        review = resolve_path(data, value, ["review"]) or {}
        stage_label = resolve_path(data, value, ["stage_label"]) or ""
        review_id = str(resolve_path(data, review, ["id"]) or "")
        if not review_id or review_id in seen_review_ids:
            continue
        text = resolve_path(data, review, ["contents", "raw_text"]) or resolve_path(
            data, review, ["contents", "text"]
        ) or ""
        if not str(text).strip():
            continue
        author = resolve_path(data, value, ["author"]) or {}
        stat = resolve_path(data, value, ["stat"]) or {}
        device = resolve_path(data, value, ["device"]) or ""
        score = resolve_path(data, review, ["score"])
        review_stage_label = resolve_path(data, review, ["stage_label"])
        author_name = resolve_path(data, author, ["user", "name"]) or ""
        author_id = resolve_path(data, author, ["user", "id"])
        ups = resolve_path(data, stat, ["ups"]) or 0
        pv_total = resolve_path(data, stat, ["pv_total"]) or 0
        comments = resolve_path(data, stat, ["comments"]) or 0
        structured.append(
            {
                "platform": "TapTap",
                "app": "EVE",
                "source_url": f"https://www.taptap.cn/review/{review_id}",
                "app_review_url": "https://www.taptap.cn/app/788667/review",
                "moment_id": str(row_id or ""),
                "review_id": review_id,
                "created_time": created_time,
                "edited_time": edited_time,
                "stage_label": review_stage_label or stage_label,
                "score": score,
                "device": device,
                "author_name": author_name,
                "author_id": author_id,
                "ups": ups,
                "pv_total": pv_total,
                "comments": comments,
                "content": re.sub(r"<br\\s*/?>", "\n", str(text)).strip(),
                "matched_keywords": [k for k in keywords if k in str(text)],
            }
        )
        seen_review_ids.add(review_id)
    structured.sort(key=lambda r: int(r.get("ups") or 0), reverse=True)
    OUT_STRUCTURED_JSONL.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in structured) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# TapTap EVE 公开评价页采样摘要",
        "",
        "- 来源：https://www.taptap.cn/app/788667/review",
        f"- 结构化评价：{len(structured)} 条",
        f"- 页面内命中长文本：{len(hits)} 条",
        f"- 结构化原始文件：`research/taptap_raw/{OUT_STRUCTURED_JSONL.name}`",
        f"- 原始解析文件：`research/taptap_raw/{OUT_JSONL.name}`",
        "",
        "## 结构化高赞评价摘录",
        "",
    ]
    for row in structured[:30]:
        lines.append(
            f"- [赞 {row['ups']}｜浏览 {row['pv_total']}｜{row['stage_label']}｜score {row['score']}｜review_id {row['review_id']}]"
        )
        lines.append(f"  - {short(row['content'])}")
        lines.append(f"  - 来源：{row['source_url']}")
    lines += ["", "## 页面内高信号文本摘录", ""]
    for row in hits[:50]:
        lines.append(
            f"- 关键词：{', '.join(row['matched_keywords'])}｜路径：`{row['path']}`"
        )
        lines.append(f"  - {short(row['content'])}")
        lines.append(f"  - 来源：{row['source_url']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(OUT_JSONL)
    print(OUT_STRUCTURED_JSONL)
    print(OUT_MD)
    print(f"structured={len(structured)} hits={len(hits)}")


if __name__ == "__main__":
    main()
