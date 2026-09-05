"""免费天气桥接 — Open-Meteo（无需 API Key，商用友好）。

文档：https://open-meteo.com/
地理编码：https://geocoding-api.open-meteo.com/
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

# 默认城市（可用 .env WEATHER_CITY 覆盖，如 Shanghai / Beijing / Hangzhou）
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Shanghai")


@dataclass
class WeatherBrief:
    city: str
    temp_c: float
    humidity: int
    code: int
    summary: str  # 中文天气简述
    care_line: str  # heal 口吻的关怀句


# WMO Weather interpretation codes → 中文
_CODE_MAP: dict[int, str] = {
    0: "晴朗",
    1: "大部晴朗",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "雾凇",
    51: "毛毛雨",
    53: "小雨",
    55: "中雨",
    61: "小雨",
    63: "中雨",
    65: "暴雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "强阵雨",
    82: "暴雨",
    95: "雷阵雨",
    96: "雷阵雨",
    99: "雷阵雨",
}


def _geocode(city: str) -> tuple[float, float, str] | None:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url, params={"name": city, "count": 1, "language": "zh"})
            r.raise_for_status()
            results = (r.json() or {}).get("results") or []
            if not results:
                return None
            hit = results[0]
            name = hit.get("name") or city
            return float(hit["latitude"]), float(hit["longitude"]), name
    except Exception:  # noqa: BLE001
        return None


def fetch_weather(city: str | None = None) -> WeatherBrief | None:
    """拉取当前天气；失败返回 None（不阻断主流程）。"""
    city = (city or DEFAULT_CITY).strip() or "Shanghai"
    geo = _geocode(city)
    if not geo:
        # 上海兜底坐标
        lat, lon, label = 31.23, 121.47, city
    else:
        lat, lon, label = geo

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "auto",
    }
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            cur = (r.json() or {}).get("current") or {}
    except Exception:  # noqa: BLE001
        return None

    temp = float(cur.get("temperature_2m") or 0)
    humidity = int(cur.get("relative_humidity_2m") or 0)
    code = int(cur.get("weather_code") or 0)
    summary = _CODE_MAP.get(code, "天气一般")

    care = _care_line(label, temp, summary, code)
    return WeatherBrief(
        city=label,
        temp_c=temp,
        humidity=humidity,
        code=code,
        summary=summary,
        care_line=care,
    )


def _care_line(city: str, temp: float, summary: str, code: int) -> str:
    rainy = code in {51, 53, 55, 61, 63, 65, 80, 81, 95}
    cold = temp < 12
    hot = temp > 30

    if rainy:
        return f"今天{city}是{summary}，大概 {temp:.0f}°C。出门的话记得带把伞，回来把鞋擦干就好。"
    if cold:
        return f"今天{city}有点凉，{summary}，大约 {temp:.0f}°C。外套多披一件，别硬扛。"
    if hot:
        return f"今天{city}挺热的，{summary}，大约 {temp:.0f}°C。记得喝点水，别一直对着屏幕。"
    return f"今天{city}{summary}，大约 {temp:.0f}°C。天气还行，不着急出门也没关系。"
