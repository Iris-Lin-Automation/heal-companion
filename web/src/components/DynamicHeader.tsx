/**
 * Layer 1 — 顶部悬浮操作栏
 *
 * 三列 CSS Grid 布局，保证中央角色徽章绝对居中：
 *   [← 返回]  ·  [名字 · 状态]  ·  [问候一句 | 记忆]
 *
 * 未来可在右侧 actions 区增加"🎵 音乐"、"⚙ 设置"等按钮。
 */

type Props = {
  companionName: string;
  userNickname: string;
  /** 认识天数，显示在状态徽章右侧 */
  daysTogether?: number;
  busy?: boolean;
  notebookOpen?: boolean;
  /** TTS 自动朗读开关 */
  ttsEnabled?: boolean;
  onBack: () => void;
  onToggleNotebook: () => void;
  onMissYou: () => void;
  onToggleTTS?: () => void;
  onToggleMusic?: () => void;
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
}: Props) {
  return (
    <header className="char-topbar">
      {/* 左列：返回按钮 */}
      <button type="button" className="char-back-btn" onClick={onBack}>
        ← 返回
      </button>

      {/* 中列：角色状态徽章（居中锁定） */}
      <div className="char-tag">
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
      </div>

      {/* 右列：操作按钮组（右对齐） */}
      <div className="char-topbar-actions">
        {/* 🎵 音乐面板 */}
        {onToggleMusic && (
          <button
            type="button"
            className="char-action-btn char-action-btn--icon"
            onClick={onToggleMusic}
            title="环境音乐"
            aria-label="环境音乐"
          >
            🎵
          </button>
        )}
        {/* TTS 语音朗读开关 — 默认开启，醒目玻璃胶囊 */}
        {onToggleTTS && (
          <button
            type="button"
            className={`char-action-btn char-action-btn--icon char-tts-btn ${ttsEnabled ? "active" : ""}`}
            onClick={onToggleTTS}
            title={ttsEnabled ? "语音朗读已开（点击关闭）" : "语音朗读已关（点击开启）"}
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
        >
          {notebookOpen ? "收起" : "记忆"}
        </button>
      </div>
    </header>
  );
}
