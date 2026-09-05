const SESSION_KEY = "heal-session";

export type Session = {
  userId: string;
  nickname: string;
  comfort: string;
  onboarded: boolean;
  /** ISO 日期字符串，第一次完成 Greet 时写入，用于计算认识天数 */
  metAt?: string;
};

/** 从 metAt 计算"认识第X天"，最少第1天 */
export function daysTogether(session: Session): number {
  if (!session.metAt) return 1;
  const diff = Date.now() - new Date(session.metAt).getTime();
  return Math.max(1, Math.floor(diff / 86_400_000) + 1);
}

function freshId() {
  return `u_${Math.random().toString(36).slice(2, 10)}`;
}

export function loadSession(): Session {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw) as Session;
  } catch {
    /* ignore */
  }
  return {
    userId: freshId(),
    nickname: "",
    comfort: "",
    onboarded: false,
  };
}

export function saveSession(session: Session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

/** 清除本地 session，下次启动会重新走 Welcome → Greet 引导流程 */
export function resetSession(): Session {
  localStorage.removeItem(SESSION_KEY);
  // 同时清除旧 key（兼容旧版本）
  localStorage.removeItem("ruanruan-session");
  const fresh: Session = { userId: freshId(), nickname: "", comfort: "", onboarded: false };
  saveSession(fresh);
  return fresh;
}
