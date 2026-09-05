/**
 * 用户当前环境上下文（免费开源，无 Key）
 *
 * 数据源：
 *  - 时间：浏览器本地时钟
 *  - 定位：Geolocation API → 失败则 ipapi.co（免费）
 *  - 逆地理：BigDataCloud reverse-geocode-client（免费、可 CORS）
 *  - 天气：Open-Meteo（免费、可 CORS）
 *
 * 采集后悄悄塞进 /api/chat，不展示给用户。
 */

export type EnvContext = {
  city: string;
  local_time: string; // "23:00"
  weather: string; // "暴雨"
  temp_c?: number;
  lat?: number;
  lon?: number;
  timezone?: string;
  source?: string; // gps | ip | fallback
};

const WMO: Record<number, string> = {
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
};

let cached: EnvContext | null = null;
let inflight: Promise<EnvContext> | null = null;

async function fetchJson(url: string, ms = 5000): Promise<any | null> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function formatLocalTime(d = new Date()): string {
  const h = d.getHours().toString().padStart(2, "0");
  const m = d.getMinutes().toString().padStart(2, "0");
  return `${h}:${m}`;
}

function getTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai";
  } catch {
    return "Asia/Shanghai";
  }
}

function getGps(): Promise<{ lat: number; lon: number } | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 6000, maximumAge: 600_000 }
    );
  });
}

async function getIpLocation(): Promise<{ lat: number; lon: number; city?: string } | null> {
  try {
    const j = await fetchJson("https://ipapi.co/json/", 5000);
    if (j?.latitude && j?.longitude) {
      return {
        lat: Number(j.latitude),
        lon: Number(j.longitude),
        city: j.city || j.region || undefined,
      };
    }
  } catch {
    /* try next */
  }
  try {
    const j = await fetchJson("https://ipapi.co/json/", 5000);
    // HTTPS-only fallback already covered; skip insecure ip-api on mixed content
    if (j?.latitude && j?.longitude) {
      return {
        lat: Number(j.latitude),
        lon: Number(j.longitude),
        city: j.city || undefined,
      };
    }
  } catch {
    /* ignore */
  }
  return null;
}

async function reverseCity(lat: number, lon: number): Promise<string | null> {
  const url =
    `https://api.bigdatacloud.net/data/reverse-geocode-client` +
    `?latitude=${lat}&longitude=${lon}&localityLanguage=zh`;
  const j = await fetchJson(url, 5000);
  if (!j) return null;
  return j.city || j.locality || j.principalSubdivision || j.countryName || null;
}

async function fetchWeather(lat: number, lon: number): Promise<{ weather: string; temp_c: number } | null> {
  const url =
    `https://api.open-meteo.com/v1/forecast` +
    `?latitude=${lat}&longitude=${lon}` +
    `&current=temperature_2m,weather_code&timezone=auto`;
  const j = await fetchJson(url, 6000);
  if (!j) return null;
  const cur = j.current || {};
  const code = Number(cur.weather_code ?? 0);
  return {
    weather: WMO[code] || "天气一般",
    temp_c: Number(cur.temperature_2m ?? 0),
  };
}

/** 采集一次环境（有缓存，10 分钟内复用坐标天气，时间每次刷新） */
export async function collectEnvContext(force = false): Promise<EnvContext> {
  const nowTime = formatLocalTime();
  const tz = getTimezone();

  if (!force && cached) {
    return { ...cached, local_time: nowTime, timezone: tz };
  }
  if (!force && inflight) {
    const base = await inflight;
    return { ...base, local_time: nowTime, timezone: tz };
  }

  inflight = (async () => {
    let lat: number | undefined;
    let lon: number | undefined;
    let city = "";
    let source: EnvContext["source"] = "fallback";

    const gps = await getGps();
    if (gps) {
      lat = gps.lat;
      lon = gps.lon;
      source = "gps";
      city = (await reverseCity(lat, lon)) || "";
    } else {
      const ip = await getIpLocation();
      if (ip) {
        lat = ip.lat;
        lon = ip.lon;
        city = ip.city || "";
        source = "ip";
        if (!city) city = (await reverseCity(lat, lon)) || "";
      }
    }

    // 最终兜底：上海
    if (lat == null || lon == null) {
      lat = 31.23;
      lon = 121.47;
      city = city || "上海";
      source = "fallback";
    }
    if (!city) city = "当前位置";

    const w = await fetchWeather(lat, lon);
    const ctx: EnvContext = {
      city,
      local_time: formatLocalTime(),
      weather: w?.weather || "未知",
      temp_c: w?.temp_c,
      lat,
      lon,
      timezone: tz,
      source,
    };
    cached = ctx;
    return ctx;
  })();

  try {
    return await inflight;
  } finally {
    inflight = null;
  }
}

export function envContextLabel(env: EnvContext): string {
  const temp = env.temp_c != null ? ` ${Math.round(env.temp_c)}°C` : "";
  return `${env.city} · ${env.local_time} · ${env.weather}${temp}`;
}
