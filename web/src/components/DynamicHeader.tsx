/**
 * 顶部悬浮栏：返回 / 第几天 / 音乐·语音·问候·记忆
 * 这些不是「跳路由」，而是点开轻量半页（抽屉/面板）——海外陪伴 App 常见做法。
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
  /** 点「第 X 天」打开认识天数面板 */
  onOpenDays?: () => void;
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
}: Props) {
  return (
    <header className="char-topbar">
      <button type="button" className="char-back-btn" onClick={onBack} title="回主页">
        ← 返回
      </button>

      <button
        type="button"
        className="char-tag"
        onClick={onOpenDays}
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
            onClick={onToggleMusic}
            title="环境音乐（点开面板）"
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
          onClick={onMissYou}
        >
          问候一句
        </button>
        <button
          type="button"
          className={`char-action-btn ${notebookOpen ? "active" : ""}`}
          onClick={onToggleNotebook}
          title="记忆本（侧页）"
        >
          {notebookOpen ? "收起" : "记忆"}
        </button>
      </div>
    </header>
  );
}
