import { useRef } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  /** 父层调用：清空 input 值、调用 API */
  onSend: () => void;
  busy?: boolean;
  placeholder?: string;
};

/**
 * Layer 1 — 底部输入栏
 *
 * 从左到右：[🎤 语音按钮（占位）] [textarea 自适应高度] [发送按钮]
 *
 * 语音按钮当前为 disabled 占位，待接入 Web Speech API 后启用：
 *   const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
 */
export default function VoiceInputBar({
  value,
  onChange,
  onSend,
  busy,
  placeholder = "说点什么…",
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    onChange(e.target.value);
    // textarea 随内容自动伸缩，上限 120px
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSend() {
    if (!value.trim() || busy) return;
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    onSend();
  }

  return (
    <div className="char-input-bar">
      {/* 🎤 语音输入占位按钮（待接入 Web Speech API） */}
      <button
        type="button"
        className="char-voice-btn"
        title="语音输入（即将开放）"
        aria-label="语音输入"
        disabled
      >
        🎤
      </button>

      {/* 文字输入框 */}
      <textarea
        ref={textareaRef}
        className="char-input"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={busy}
        rows={1}
      />

      {/* 发送按钮 */}
      <button
        type="button"
        className="char-send-btn"
        disabled={busy || !value.trim()}
        onClick={handleSend}
      >
        发送
      </button>
    </div>
  );
}
