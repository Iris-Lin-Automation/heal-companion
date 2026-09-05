import { useState } from "react";
import LiveCharacterView, { type CharacterEmotion } from "../components/LiveCharacterView";
import DynamicHeader from "../components/DynamicHeader";
import GlassChatStream, { type ChatMessage } from "../components/GlassChatStream";
import VoiceInputBar from "../components/VoiceInputBar";
import MemoryNotebook, { type MemoryItem } from "../components/MemoryNotebook";
import DevLabPanel, { type ScriptScene, type TtsSample } from "../components/DevLabPanel";

/** Re-export so App.tsx 的 import 路径无需改动 */
export type { ChatMessage, MemoryItem };

const COMPANION = "heal";

type Props = {
  nickname: string;
  daysTogether: number;
  messages: ChatMessage[];
  memories: MemoryItem[];
  busy: boolean;
  showNotebook: boolean;
  quickReplies?: string[];
  ttsEnabled?: boolean;
  voiceType: string;
  characterEmotion: CharacterEmotion;
  characterSpeaking: boolean;
  showRetry?: boolean;
  onRetry?: () => void;
  onVoiceTypeChange: (voiceType: string) => void;
  onToggleNotebook: () => void;
  onToggleTTS?: () => void;
  onToggleMusic?: () => void;
  onSend: (text: string) => void;
  onPlayTtsSample: (sample: TtsSample) => void;
  onPreviewEmotion: (emotion: CharacterEmotion) => void;
  onMissYou: () => void;
  onBack: () => void;
};

export default function ChatRoom({
  nickname,
  daysTogether,
  messages,
  memories,
  busy,
  showNotebook,
  quickReplies,
  ttsEnabled,
  voiceType,
  characterEmotion,
  characterSpeaking,
  showRetry,
  onRetry,
  onVoiceTypeChange,
  onToggleNotebook,
  onToggleTTS,
  onToggleMusic,
  onSend,
  onPlayTtsSample,
  onPreviewEmotion,
  onMissYou,
  onBack,
}: Props) {
  const [input, setInput] = useState("");

  function handleSend() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    onSend(text);
  }

  function handleScript(scene: ScriptScene) {
    onSend(scene.userLine);
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
      />

      <div className="char-overlay">
        <GlassChatStream
          messages={messages}
          busy={busy}
          quickReplies={quickReplies}
          onChipClick={(text) => { onSend(text); }}
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

      <MemoryNotebook open={showNotebook} memories={memories} />

      {/* 左侧隐藏调音板 / 剧本台 */}
      <DevLabPanel
        busy={busy}
        voiceType={voiceType}
        activeEmotion={characterEmotion}
        onVoiceTypeChange={onVoiceTypeChange}
        onPlaySample={onPlayTtsSample}
        onRunScript={handleScript}
        onPreviewEmotion={onPreviewEmotion}
      />
    </div>
  );
}
