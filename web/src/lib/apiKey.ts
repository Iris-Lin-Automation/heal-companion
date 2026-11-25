const STORAGE_KEY = "heal_deepseek_api_key";
const BASE_KEY = "heal_deepseek_base_url";

const DEFAULT_BASE = "https://api.deepseek.com";

export function getUserApiKey(): string {
  try {
    return (localStorage.getItem(STORAGE_KEY) || "").trim();
  } catch {
    return "";
  }
}

export function setUserApiKey(key: string) {
  const v = key.trim();
  try {
    if (v) localStorage.setItem(STORAGE_KEY, v);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function getUserBaseUrl(): string {
  try {
    return (localStorage.getItem(BASE_KEY) || DEFAULT_BASE).trim() || DEFAULT_BASE;
  } catch {
    return DEFAULT_BASE;
  }
}

export function setUserBaseUrl(url: string) {
  const v = url.trim() || DEFAULT_BASE;
  try {
    localStorage.setItem(BASE_KEY, v);
  } catch {
    /* ignore */
  }
}

export function hasUserApiKey(): boolean {
  return getUserApiKey().length > 8;
}
