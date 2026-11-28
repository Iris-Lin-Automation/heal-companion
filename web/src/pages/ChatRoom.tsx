import { useState } from "react";
import LiveCharacterView, { type CharacterEmotion } from "../components/LiveCharacterView";
import DynamicHeader from "../components/DynamicHeader";
import GlassChatStream, { type ChatMessage } from "../components/GlassChatStream";
import VoiceInputBar from "../components/VoiceInputBar";
import MemoryNotebook, { type MemoryItem } from "../components/MemoryNotebook";

/** Re-export so App.tsx 的 import 路径无需改动 */
export type { ChatMessage, MemoryItem };

const COMPANION = "heal";

type Props = {
  nickname: string;
  daysTogether: number;
  messages: ChatMessage[];
  memories: MemoryItem[];
  onMemoriesChanged?: () => void;
  busy: boolean;
  showNotebook: boolean;
  quickReplies?: string[];
  ttsEnabled?: boolean;
  characterEmotion: CharacterEmotion;
  characterSpeaking: boolean;
  showRetry?: boolean;
  onRetry?: () => void;
  onToggleNotebook: () => void;
  onToggleTTS?: () => void;
  onToggleMusic?: () => void;
  onOpenApiKey?: () => void;
  onLogout?: () => void;
  onSend: (text: string) => void;
  onMissYou: () => void;
  onBack: () => void;
};

export default function ChatRoom({
  nickname,
  daysTogether,
  messages,
  memories,
  onMemoriesChanged,
  busy,
  showNotebook,
  quickReplies,
  ttsEnabled,
  characterEmotion,
  characterSpeaking,
  showRetry,
  onRetry,
  onToggleNotebook,
  onToggleTTS,
  onToggleMusic,
  onOpenApiKey,
  onLogout,
  onSend,
  onMissYou,
  onBack,
}: Props) {
  const [input, setInput] = useState("");
  const [daysOpen, setDaysOpen] = useState(false);

  function handleSend() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    onSend(text);
  }

  return (
    <div className="char-room">
      <LiveCharacterView
        src="/images/heal-character-idle.png"
        emotion={characterEmotion}
        speaking={characterSpeaking}
        modelSrc="/live2d/heal/heal.model3.json"
      />

      <DynamicHeader
        companionName={COMPANION}
        userNickname={nickname}
        daysTogether={daysTogether}
        busy={busy}
        notebookOpen={showNotebook}
        ttsEnabled={ttsEnabled}
        onBack={onBack}
        onToggleNotebook={onToggleNotebook}
        onMissYou={onMissYou}
        onToggleTTS={onToggleTTS}
        onToggleMusic={onToggleMusic}
        onOpenDays={() => setDaysOpen(true)}
        onOpenApiKey={onOpenApiKey}
        onLogout={onLogout}
      />

      <div className="char-overlay">
        <GlassChatStream
          messages={messages}
          busy={busy}
          quickReplies={quickReplies}
          onChipClick={(text) => {
            onSend(text);
          }}
          showRetry={showRetry}
          onRetry={onRetry}
          retrying={busy}
        />
        <VoiceInputBar
          value={input}
          onChange={setInput}
          onSend={handleSend}
          busy={busy}
          placeholder={`跟${COMPANION}说点什么…`}
        />
      </div>

      <MemoryNotebook
        open={showNotebook}
        memories={memories}
        onChanged={onMemoriesChanged}
      />

      {daysOpen && (
        <div
          className="char-sheet-backdrop"
          role="dialog"
          aria-modal="true"
          onClick={() => setDaysOpen(false)}
        >
          <div className="char-sheet" onClick={(e) => e.stopPropagation()}>
            <h2>认识第 {daysTogether || 1} 天</h2>
            <p>
              {nickname}，我还在这儿。不用一次把心事说完，想到哪儿就从哪儿开始。
            </p>
            <button
              type="button"
              className="char-sheet-close"
              onClick={() => setDaysOpen(false)}
            >
              好
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
