import { useState } from "react";
import type { MemoryItem } from "../components/MemoryNotebook";

type Panel = "chat" | "notebook" | null;

type Props = {
  nickname: string;
  memories: MemoryItem[];
  onChat: () => void;
  onNotebook: () => void;
  onMissYou: () => void;
  onToggleMusic: () => void;   // 打开全局音乐面板
  onLeave: () => void;
  missBusy?: boolean;
  /** 根据过往聊天主动冒出的一句 */
  proactiveBubble?: string | null;
  onOpenProactive?: () => void;
  onDismissProactive?: () => void;
};

/**
 * Home — 极简全屏沉浸画布
 *
 * 音乐播放器已提升到 App.tsx 全局层（跨界面持续播放）。
 * 🎵 dock 按钮直接触发 onToggleMusic 回调。
 */
export default function Home({
  nickname: _nickname,
  memories,
  onChat,
  onNotebook,
  onMissYou,
  onToggleMusic,
  onLeave,
  missBusy,
  proactiveBubble,
  onOpenProactive,
  onDismissProactive,
}: Props) {
  const [panel, setPanel] = useState<Panel>(null);

  function toggle(p: Exclude<Panel, null>) {
    setPanel((prev) => (prev === p ? null : p));
  }

  return (
    <section className="screen home-screen">

      {/* 极简离开按钮（右上角） */}
      <button type="button" className="home-leave-btn" onClick={onLeave}>
        离开
      </button>

      {/* 根据过往聊过的事主动冒出的浮云 */}
      {proactiveBubble && (
        <button
          type="button"
          className="home-proactive-bubble"
          onClick={onOpenProactive}
          aria-label="打开 heal 的主动消息"
        >
          <span className="home-proactive-text">{proactiveBubble}</span>
          <span className="home-proactive-hint">点开聊聊</span>
          <span
            className="home-proactive-dismiss"
            role="presentation"
            onClick={(e) => {
              e.stopPropagation();
              onDismissProactive?.();
            }}
          >
            ×
          </span>
        </button>
      )}

      {/* ── 弹出面板 ── */}
      {panel === "chat" && (
        <div className="dock-panel dock-panel--float" key="chat">
          <p className="dock-panel-title">把今天放下来</p>
          <button type="button" className="primary-pill wide" onClick={onChat}>
            进入对话
          </button>
          <button
            type="button"
            className="ghost-pill dock-panel-secondary"
            disabled={missBusy}
            onClick={() => { onMissYou(); setPanel(null); }}
          >
            {missBusy ? "heal 在想…" : "让 heal 问候一句"}
          </button>
        </div>
      )}

      {panel === "notebook" && (
        <div className="dock-panel dock-panel--float" key="notebook">
          <p className="dock-panel-title">heal 记得的事</p>
          {memories.length === 0 ? (
            <p className="dock-panel-empty">还空着。等你愿意说，会慢慢留下来。</p>
          ) : (
            <ul className="dock-panel-memory-list">
              {memories.slice(0, 4).map((m) => (
                <li key={m.id}>{m.summary}</li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="ghost-pill dock-panel-secondary"
            onClick={() => { onNotebook(); setPanel(null); }}
          >
            打开记忆
          </button>
        </div>
      )}

      {/* ── 底部 Dock ── */}
      <nav className="home-dock home-dock--float" aria-label="主操作栏">
        {/* 🎵 直接打开全局播放器，不再在 Home 内渲染 */}
        <button
          type="button"
          className="dock-btn"
          onClick={onToggleMusic}
          aria-label="环境音乐"
        >
          🎵
        </button>

        <button
          type="button"
          className={`dock-btn dock-btn--primary ${panel === "chat" ? "active" : ""}`}
          onClick={() => toggle("chat")}
          aria-label="开始对话"
        >
          💬
        </button>

        <button
          type="button"
          className={`dock-btn ${panel === "notebook" ? "active" : ""}`}
          onClick={() => toggle("notebook")}
          aria-label="记忆"
        >
          📝
        </button>
      </nav>
    </section>
  );
}
