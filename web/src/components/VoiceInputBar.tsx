import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  busy?: boolean;
  placeholder?: string;
};

type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

function getSpeechRecognition(): (new () => SpeechRec) | null {
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRec;
    webkitSpeechRecognition?: new () => SpeechRec;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

/**
 * 底部纤细输入条：麦克风 + 单行输入 + 箭头发送
 * 默认收成一条浮线，点一下再展开，少挡立绘脸。
 */
export default function VoiceInputBar({
  value,
  onChange,
  onSend,
  busy,
  placeholder = "说点什么…",
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recRef = useRef<SpeechRec | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [listening, setListening] = useState(false);
  const [micSupported, setMicSupported] = useState(true);

  useEffect(() => {
    setMicSupported(!!getSpeechRecognition());
    return () => {
      try {
        recRef.current?.stop();
      } catch {
        /* ignore */
      }
    };
  }, []);

  function resize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 88) + "px";
  }

  function handleChange(e: ChangeEvent<HTMLTextAreaElement>) {
    onChange(e.target.value);
    resize();
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSend() {
    if (!value.trim() || busy) return;
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    onSend();
    setExpanded(false);
  }

  function openComposer() {
    setExpanded(true);
    requestAnimationFrame(() => textareaRef.current?.focus());
  }

  function toggleMic() {
    const Ctor = getSpeechRecognition();
    if (!Ctor || busy) return;

    if (listening && recRef.current) {
      try {
        recRef.current.stop();
      } catch {
        /* ignore */
      }
      setListening(false);
      return;
    }

    const rec = new Ctor();
    rec.lang = "zh-CN";
    rec.continuous = false;
    rec.interimResults = true;
    rec.onresult = (ev) => {
      const piece = Array.from(ev.results)
        .map((r) => r[0]?.transcript || "")
        .join("");
      if (piece) {
        onChange(piece);
        setExpanded(true);
        requestAnimationFrame(resize);
      }
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
      setExpanded(true);
    } catch {
      setListening(false);
    }
  }

  return (
    <div className={`char-input-dock ${expanded || value ? "is-open" : ""}`}>
      <div className="char-input-bar">
        <button
          type="button"
          className={`char-voice-btn ${listening ? "is-listening" : ""}`}
          title={micSupported ? (listening ? "停止语音输入" : "语音输入") : "当前浏览器不支持语音输入"}
          aria-label="语音输入"
          aria-pressed={listening}
          disabled={busy || !micSupported}
          onClick={toggleMic}
        >
          <span aria-hidden>🎤</span>
        </button>

        {!expanded && !value ? (
          <button type="button" className="char-input-ghost" onClick={openComposer}>
            {placeholder}
          </button>
        ) : (
          <textarea
            ref={textareaRef}
            className="char-input"
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              if (!value.trim() && !listening) setExpanded(false);
            }}
            placeholder={placeholder}
            disabled={busy}
            rows={1}
          />
        )}

        <button
          type="button"
          className="char-send-btn"
          disabled={busy || !value.trim()}
          onClick={handleSend}
          aria-label="发送"
          title="发送"
        >
          <span className="char-send-arrow" aria-hidden>
            ↑
          </span>
        </button>
      </div>
    </div>
  );
}
