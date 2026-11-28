import { useEffect, useRef, useState } from "react";

/**
 * 顶部默认收起，只留两个小圆点按钮，不挡立绘脸。
 * 点「···」才展开返回 / 天数 / 音乐 / 语音 / 问候 / 记忆。
 */

type Props = {
  companionName: string;
  userNickname: string;
  daysTogether?: number;
  busy?: boolean;
  notebookOpen?: boolean;
  ttsEnabled?: boolean;
  onBack: () => void;
  onToggleNotebook: () => void;
  onMissYou: () => void;
  onToggleTTS?: () => void;
  onToggleMusic?: () => void;
  onOpenDays?: () => void;
  onOpenApiKey?: () => void;
  onLogout?: () => void;
};

export default function DynamicHeader({
  companionName,
  userNickname,
  daysTogether,
  busy,
  notebookOpen,
  ttsEnabled,
  onBack,
  onToggleNotebook,
  onMissYou,
  onToggleTTS,
  onToggleMusic,
  onOpenDays,
  onOpenApiKey,
  onLogout,
}: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const t = window.setTimeout(() => setOpen(false), 8000);
    return () => window.clearTimeout(t);
  }, [open]);

  return (
    <header ref={rootRef} className={`char-topbar ${open ? "is-open" : "is-collapsed"}`}>
      {!open ? (
        <div className="char-topbar-peek">
          <button
            type="button"
            className="char-peek-btn"
            onClick={onBack}
            title="返回"
            aria-label="返回"
          >
            ←
          </button>
          <button
            type="button"
            className="char-peek-btn"
            onClick={() => setOpen(true)}
            title="打开菜单"
            aria-label="打开菜单"
            aria-expanded={false}
          >
            ···
          </button>
        </div>
      ) : (
        <>
          <button type="button" className="char-back-btn" onClick={onBack} title="回主页">
            ← 返回
          </button>

          <button
            type="button"
            className="char-tag"
            onClick={() => {
              onOpenDays?.();
              setOpen(false);
            }}
            title="认识天数"
            aria-label="打开认识天数"
          >
            <span className="char-status-dot" />
            <span className="char-tag-name">{companionName}</span>
            <span className="char-tag-divider">·</span>
            <span className="char-tag-status">
              {busy
                ? "正在想…"
                : daysTogether
                  ? `第 ${daysTogether} 天`
                  : `在陪${userNickname}`}
            </span>
          </button>

          <div className="char-topbar-actions">
            {onToggleMusic && (
              <button
                type="button"
                className="char-action-btn char-action-btn--icon"
                onClick={() => {
                  onToggleMusic();
                  setOpen(false);
                }}
                title="环境音乐"
                aria-label="环境音乐"
              >
                🎵
              </button>
            )}
            {onToggleTTS && (
              <button
                type="button"
                className={`char-action-btn char-action-btn--icon char-tts-btn ${ttsEnabled ? "active" : ""}`}
                onClick={onToggleTTS}
                title={ttsEnabled ? "语音朗读已开" : "语音朗读已关"}
                aria-label="语音朗读"
                aria-pressed={!!ttsEnabled}
              >
                {ttsEnabled ? "🔊" : "🔇"}
              </button>
            )}
            <button
              type="button"
              className="char-action-btn"
              disabled={busy}
              onClick={() => {
                onMissYou();
                setOpen(false);
              }}
            >
              问候一句
            </button>
            <button
              type="button"
              className={`char-action-btn ${notebookOpen ? "active" : ""}`}
              onClick={() => {
                onToggleNotebook();
                setOpen(false);
              }}
              title="记忆本"
            >
              {notebookOpen ? "收起" : "记忆"}
            </button>
            {onOpenApiKey && (
              <button
                type="button"
                className="char-action-btn"
                onClick={() => {
                  onOpenApiKey();
                  setOpen(false);
                }}
                title="DeepSeek API Key"
              >
                Key
              </button>
            )}
            {onLogout && (
              <button
                type="button"
                className="char-action-btn"
                onClick={() => {
                  onLogout();
                  setOpen(false);
                }}
              >
                退出
              </button>
            )}
            <button
              type="button"
              className="char-action-btn char-action-btn--icon"
              onClick={() => setOpen(false)}
              title="收起菜单"
              aria-label="收起菜单"
            >
              ✕
            </button>
          </div>
        </>
      )}
    </header>
  );
}
