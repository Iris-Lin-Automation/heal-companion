function sessionKey(userId: string) {
  return `heal-session:${userId}`;
}

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

export function loadSessionFor(userId: string): Session {
  try {
    const raw = localStorage.getItem(sessionKey(userId));
    if (raw) {
      const parsed = JSON.parse(raw) as Session;
      return { ...parsed, userId };
    }
  } catch {
    /* ignore */
  }
  return { userId, nickname: "", comfort: "", onboarded: false };
}

export function saveSession(session: Session) {
  if (!session.userId) return;
  localStorage.setItem(sessionKey(session.userId), JSON.stringify(session));
}

/** 只清这个账号在本机的引导进度，不删除云端记忆。 */
export function resetSession(userId: string): Session {
  const fresh: Session = { userId, nickname: "", comfort: "", onboarded: false };
  saveSession(fresh);
  return fresh;
}
