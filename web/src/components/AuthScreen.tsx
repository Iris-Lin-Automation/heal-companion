import { useState } from "react";
import { authRedirectTo, supabase, supabaseConfigured } from "../lib/supabaseClient";

type Mode = "login" | "signup";

export default function AuthScreen() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  async function submit() {
    if (!supabase || busy) return;
    setBusy(true);
    setError("");
    setInfo("");
    try {
      const redirectTo = authRedirectTo();
      if (mode === "signup") {
        const { data, error: signError } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: redirectTo },
        });
        if (signError) throw signError;
        if (!data.session) {
          setInfo(`确认信已发出。请在同一台设备打开邮件里的链接（会回到 ${redirectTo}），再回来登录。`);
        }
      } else {
        const { error: signError } = await supabase.auth.signInWithPassword({ email, password });
        if (signError) throw signError;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录没有成功");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-gate">
      <div className="char-sheet api-key-sheet" role="dialog" aria-modal="true">
        <h2>{mode === "login" ? "登录" : "注册"}</h2>
        {supabaseConfigured() ? (
          <p>这段陪伴只属于登录的这个人。换一个账号，就是另一段记忆。</p>
        ) : (
          <p>
            登录还没接上。在项目根目录的 .env 填入 VITE_SUPABASE_URL、VITE_SUPABASE_ANON_KEY、SUPABASE_URL、SUPABASE_SERVICE_ROLE_KEY、SUPABASE_JWT_SECRET，并在 Supabase 里执行 supabase/migrations/001_identity_and_memory.sql。
          </p>
        )}
        {supabaseConfigured() && (
          <>
            <label className="api-key-field">
              <span>邮箱</span>
              <input
                type="email"
                value={email}
                autoComplete="email"
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label className="api-key-field">
              <span>密码</span>
              <input
                type="password"
                value={password}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            {error && <p className="auth-note">{error}</p>}
            {info && <p className="auth-note">{info}</p>}
            <button
              type="button"
              className="char-sheet-close"
              disabled={busy || !email || password.length < 6}
              onClick={() => void submit()}
            >
              {busy ? "请稍等" : mode === "login" ? "登录" : "注册"}
            </button>
            <button
              type="button"
              className="welcome-key-btn"
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError("");
                setInfo("");
              }}
            >
              {mode === "login" ? "还没有账号，去注册" : "已有账号，去登录"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
