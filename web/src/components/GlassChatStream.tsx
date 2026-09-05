import { useEffect, useRef } from "react";

/**
 * 共享消息类型（由此文件导出，ChatRoom 和 App 通过 ChatRoom 的 re-export 引用）
 */
export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type Props = {
  messages: ChatMessage[];
  /** 为 true 时在最后一条 AI 气泡中显示打字动画 */
  busy?: boolean;
  quickReplies?: string[];
  onChipClick?: (text: string) => void;
  /** 链接失败时可点圆形重试 */
  showRetry?: boolean;
  onRetry?: () => void;
  retrying?: boolean;
};

export default function GlassChatStream({
  messages,
  busy,
  quickReplies,
  onChipClick,
  showRetry,
  onRetry,
  retrying,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, quickReplies, showRetry]);

  return (
    <>
      <div className="char-hero-spacer" />

      <div className="char-messages">
        {messages.map((m) => (
          <div key={m.id} className={`char-bubble char-bubble--${m.role}`}>
            {m.content ? (
              m.content
            ) : busy && m.role === "assistant" ? (
              <span className="char-typing" aria-label="正在输入">
                <span />
                <span />
                <span />
              </span>
            ) : null}
          </div>
        ))}

        {!busy && quickReplies && quickReplies.length > 0 && (
          <div className="chips-row">
            {quickReplies.map((chip) => (
              <button
                key={chip}
                type="button"
                className="chip-btn"
                onClick={() => onChipClick?.(chip)}
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* 连不上时：圆形刷新，让 heal 再试一次 */}
        {showRetry && !busy && (
          <div className="retry-row">
            <button
              type="button"
              className={`retry-orb ${retrying ? "spinning" : ""}`}
              onClick={onRetry}
              disabled={retrying}
              title="重新试一次"
              aria-label="重新连接"
            >
              <span className="retry-orb-icon">↻</span>
            </button>
            <span className="retry-hint">连不上了，点一下让 heal 再试</span>
          </div>
        )}

        <div ref={endRef} />
      </div>
    </>
  );
}
