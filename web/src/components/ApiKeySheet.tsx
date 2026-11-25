import { useState } from "react";
import {
  getUserApiKey,
  getUserBaseUrl,
  setUserApiKey,
  setUserBaseUrl,
} from "../lib/apiKey";

type Props = {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
};

/** 访客自带 DeepSeek Key，免费用你的站点额度 */
export default function ApiKeySheet({ open, onClose, onSaved }: Props) {
  const [key, setKey] = useState(() => getUserApiKey());
  const [base, setBase] = useState(() => getUserBaseUrl());

  if (!open) return null;

  function save() {
    setUserApiKey(key);
    setUserBaseUrl(base);
    onSaved?.();
    onClose();
  }

  return (
    <div className="char-sheet-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="char-sheet api-key-sheet" onClick={(e) => e.stopPropagation()}>
        <h2>填入你的 DeepSeek Key</h2>
        <p>
          免费体验：用你自己在 deepseek.com 创建的 API Key。Key 只存在你的浏览器里，聊天时才发给服务器去调用模型。
        </p>
        <label className="api-key-field">
          <span>API Key</span>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="sk-…"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="api-key-field">
          <span>Base URL（一般不用改）</span>
          <input
            type="url"
            value={base}
            onChange={(e) => setBase(e.target.value)}
            placeholder="https://api.deepseek.com"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <a
          className="api-key-link"
          href="https://platform.deepseek.com/api_keys"
          target="_blank"
          rel="noreferrer"
        >
          去 DeepSeek 官网创建 Key →
        </a>
        <button type="button" className="char-sheet-close" onClick={save} disabled={key.trim().length < 8}>
          保存并开始
        </button>
      </div>
    </div>
  );
}
