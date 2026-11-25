import { useCallback, useEffect, useRef, useState } from "react";
import { loadSession, saveSession, resetSession, daysTogether } from "./lib/session";
import type { Session } from "./lib/session";
import { collectEnvContext } from "./lib/envContext";
import type { EnvContext } from "./lib/envContext";
import Welcome from "./pages/Welcome";
import Greet from "./pages/Greet";
import FirstMeet from "./pages/FirstMeet";
import Home from "./pages/Home";
import ChatRoom from "./pages/ChatRoom";
import type { ChatMessage, MemoryItem } from "./pages/ChatRoom";
import type { CharacterEmotion } from "./components/LiveCharacterView";
import AmbientPlayer from "./components/AmbientPlayer";
import "./styles/app.css";

type Screen = "welcome" | "greet" | "firstmeet" | "home" | "chat" | "notebook";
const DEFAULT_VOICE_TYPE = "zh_male_taocheng_uranus_bigtts";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export default function App() {
  const [session, setSession] = useState<Session>(() => loadSession());
  const [screen, setScreen] = useState<Screen>(() =>
    loadSession().onboarded ? "home" : "welcome"
  );
  const [busy, setBusy] = useState(false);
  const [missBusy, setMissBusy] = useState(false);
  const [showNotebook, setShowNotebook] = useState(false);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  // PRD: 语音直出默认开启；记住用户上次选择
  const [ttsEnabled, setTtsEnabled] = useState(() => {
    try {
      const saved = localStorage.getItem("heal-tts-enabled");
      return saved === null ? true : saved === "1";
    } catch {
      return true;
    }
  });
  const [showMusicPanel, setShowMusicPanel] = useState(false);
  const [voiceType, setVoiceType] = useState(() => {
    try {
      return localStorage.getItem("heal-voice-type") || DEFAULT_VOICE_TYPE;
    } catch {
      return DEFAULT_VOICE_TYPE;
    }
  });
  const [characterEmotion, setCharacterEmotion] = useState<CharacterEmotion>("neutral");
  const [characterSpeaking, setCharacterSpeaking] = useState(false);
  const ttsAudioRef    = useRef<HTMLAudioElement | null>(null); // 当前 TTS 音频实例
  const streamBotRef   = useRef("");  // 流式累积 bot 回复（用于 TTS，绕过 React 批处理）
  const ttsEnabledRef  = useRef(ttsEnabled); // 避免 sendMessage 闭包读到旧开关
  const voiceTypeRef   = useRef(voiceType);
  const audioUnlockedRef = useRef(false); // 浏览器 autoplay 策略：需用户手势解锁
  const envRef = useRef<EnvContext | null>(null); // 城市/时间/天气，悄悄带给后台
  const lastFailedTextRef = useRef<string | null>(null);
  /** 分句 TTS：句队列 + 播放游标，边合成边播 */
  const ttsGenRef = useRef(0);
  const ttsSpokenLenRef = useRef(0);
  const ttsQueueRef = useRef<{ text: string; blobP: Promise<Blob | null> }[]>([]);
  const ttsDrainingRef = useRef(false);
  const [showRetry, setShowRetry] = useState(false);
  const [proactiveBubble, setProactiveBubble] = useState<string | null>(null);
  const proactiveFetchedRef = useRef(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "我在。今天先不用整理好再说，想到哪儿就从哪儿开始。",
    },
  ]);

  const refreshMemories = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/memories?user_id=${encodeURIComponent(session.userId)}`
      );
      if (!res.ok) return;
      const data = await res.json();
      setMemories(data.memories || []);
    } catch {
      /* silent */
    }
  }, [session.userId]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/history?user_id=${encodeURIComponent(session.userId)}&limit=40`
      );
      if (!res.ok) return;
      const data = await res.json();
      const hist = (data.messages || []) as { role: "user" | "assistant"; content: string }[];
      if (hist.length) {
        setMessages(
          hist.map((m) => ({
            id: uid(),
            role: m.role,
            content: m.content,
          }))
        );
      }
    } catch {
      /* first visit */
    }
  }, [session.userId]);

  // 启动时静默采集环境（定位可能弹权限；拒绝则用 IP）
  useEffect(() => {
    void collectEnvContext().then((env) => {
      envRef.current = env;
      console.info("[env]", env.city, env.local_time, env.weather, env.source);
    });
  }, []);

  useEffect(() => {
    saveSession(session);
  }, [session]);

  // 启动时：自动恢复账号 + 拉回聊天记录（防止刷新丢对话）
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        // 1) 当前 userId 是否已有历史？
        const histRes = await fetch(
          `/api/history?user_id=${encodeURIComponent(session.userId)}&limit=40`
        );
        let hist: { role: "user" | "assistant"; content: string }[] = [];
        if (histRes.ok) {
          const data = await histRes.json();
          hist = data.messages || [];
        }

        // 2) 没有历史 → 尝试从磁盘恢复最近活跃账号（或按昵称匹配）
        if (!hist.length) {
          const q = session.nickname
            ? `?nickname=${encodeURIComponent(session.nickname)}`
            : "";
          const recRes = await fetch(`/api/recover${q}`);
          if (recRes.ok) {
            const rec = await recRes.json();
            if (rec.found && rec.user?.user_id && rec.user.user_id !== session.userId) {
              if (cancelled) return;
              const restored = {
                ...session,
                userId: rec.user.user_id as string,
                nickname: (rec.user.nickname as string) || session.nickname,
                comfort: (rec.user.comfort as string) || session.comfort,
                onboarded: true,
                metAt: session.metAt ?? new Date().toISOString(),
              };
              setSession(restored);
              saveSession(restored);
              setScreen((s) => (s === "welcome" || s === "greet" ? "home" : s));
              // 用恢复后的 id 再拉历史
              const h2 = await fetch(
                `/api/history?user_id=${encodeURIComponent(restored.userId)}&limit=40`
              );
              if (h2.ok) {
                const d2 = await h2.json();
                hist = d2.messages || [];
              }
            }
          }
        }

        if (cancelled) return;
        if (hist.length) {
          setMessages(
            hist.map((m) => ({
              id: uid(),
              role: m.role,
              content: m.content,
            }))
          );
        }
        if (session.onboarded || hist.length) {
          void refreshMemories();
        }
      } catch {
        /* offline / first visit */
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
    // 仅启动时跑一次；后续靠 enterChat / sendMessage
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    ttsEnabledRef.current = ttsEnabled;
    try {
      localStorage.setItem("heal-tts-enabled", ttsEnabled ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [ttsEnabled]);

  useEffect(() => {
    voiceTypeRef.current = voiceType;
    try {
      localStorage.setItem("heal-voice-type", voiceType);
    } catch {
      /* ignore */
    }
  }, [voiceType]);

  useEffect(() => {
    if (session.onboarded) {
      void refreshMemories();
    }
  }, [session.onboarded, refreshMemories]);

  async function persistProfile(nickname: string, comfort: string) {
    try {
      await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.userId,
          display_name: nickname,
          preferred_address: nickname,
          comfort_notes: comfort,
        }),
      });
    } catch {
      /* offline ok */
    }
  }

  async function finishGreet(nickname: string, comfort: string) {
    const next = {
      ...session,
      nickname,
      comfort,
      onboarded: true,
      metAt: session.metAt ?? new Date().toISOString(), // 仅首次设置
    };
    setSession(next);
    saveSession(next);
    await persistProfile(nickname, comfort);
    setMessages([
      {
        id: uid(),
        role: "assistant",
        content: `${nickname}，我记住了。以后你不用把话说得很完整，我会慢慢认识你，也会记得那些真正重要的事。`,
      },
    ]);
    // 先进初遇场景，再从那里跳 Home
    setScreen("firstmeet");
    void refreshMemories();
  }

  /** 浏览器 autoplay 策略：必须在用户点击瞬间解锁音频通道 */
  function unlockAudioPlayback() {
    if (audioUnlockedRef.current) return;
    try {
      const silent = new Audio(
        "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"
      );
      silent.volume = 0.01;
      void silent.play().then(() => {
        silent.pause();
        audioUnlockedRef.current = true;
      }).catch(() => { /* 忽略 */ });
    } catch {
      /* ignore */
    }
  }

  /** 去掉动作描写；保留句首 [情绪] 标签给后端解析 */
  function cleanForSpeech(raw: string): string {
    return raw
      .replace(/[（(][^）)]*[）)]/g, " ")
      .replace(/\*[^*]+\*/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  /** UI 展示：去掉句首情绪标签，避免破坏沉浸 */
  function stripEmotionTag(raw: string): string {
    return raw.replace(/^\s*[\[【(（][^\]】)）]+[\]】)）]\s*/, "").trim();
  }

  /** 从尚未朗读的文本里切出已完整的句子 */
  function takeReadySentences(fullSpeech: string, from: number): { sentences: string[]; next: number } {
    const unread = fullSpeech.slice(from);
    if (!unread) return { sentences: [], next: from };
    const re = /[^。！？…!?\n]+[。！？…!?\n]+/g;
    const sentences: string[] = [];
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(unread)) !== null) {
      const s = m[0].replace(/\s+/g, " ").trim();
      if (s.length >= 2) sentences.push(s);
      last = m.index + m[0].length;
    }
    return { sentences, next: from + last };
  }

  function emotionToCharacter(emotion = ""): CharacterEmotion {
    const normalized = emotion.toLowerCase();
    // 受伤流泪（更重）优先于委屈倔强
    if (
      normalized.includes("受伤") ||
      normalized.includes("流泪") ||
      normalized.includes("眼泪") ||
      normalized.includes("哭") ||
      normalized.includes("心疼") ||
      normalized.includes("hurt") ||
      normalized.includes("tear")
    ) {
      return "hurt";
    }
    if (
      normalized.includes("委屈") ||
      normalized.includes("倔强") ||
      normalized.includes("aggrieved") ||
      normalized.includes("sad")
    ) {
      return "aggrieved";
    }
    if (
      normalized.includes("非常生气") ||
      normalized.includes("大怒") ||
      normalized.includes("furious") ||
      normalized.includes("angry") ||
      normalized.includes("生气")
    ) {
      return "angry";
    }
    if (normalized.includes("认真") || normalized.includes("serious") || normalized.includes("冷漠") || normalized.includes("一点生气")) return "serious";
    if (normalized.includes("害羞") || normalized.includes("shy") || normalized.includes("脸红")) return "shy";
    if (normalized.includes("happy") || normalized.includes("明亮") || normalized.includes("开心") || normalized.includes("微笑") || normalized.includes("smile")) return "bright";
    if (normalized.includes("热烈")) return "hot";
    if (normalized.includes("gentle") || normalized.includes("warm") || normalized.includes("温柔")) return "warm";
    if (normalized.includes("撒娇") || normalized.includes("playful")) return "playful";
    return "neutral";
  }

  /** 用户话里触及委屈/受伤等词时，先切立绘（不必等 AI 标签） */
  function emotionFromUserText(text: string): CharacterEmotion | null {
    const t = text.toLowerCase();
    if (/受伤|流泪|眼泪|哭了|想哭|心疼|心痛|难过得/.test(t)) return "hurt";
    if (/委屈|倔强|被骂|被伤|难受|心里空|被忽略|不想理你/.test(t)) return "aggrieved";
    if (/给我滚|闭嘴|滚啊|废物|滚出/.test(t)) return "angry";
    if (/听话|命令|至于吗|别那么敏感|马上道歉/.test(t)) return "serious";
    if (/害羞|脸红|好可爱|想亲/.test(t)) return "shy";
    return null;
  }

  async function sendMessage(text: string, opts?: { isRetry?: boolean }) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    if (ttsEnabledRef.current) unlockAudioPlayback();
    setBusy(true);
    setQuickReplies([]);
    setShowRetry(false);
    streamBotRef.current = "";
    resetTtsPipeline();
    const streamGen = ttsGenRef.current;
    let replyEmotion = "";

    const fromUser = emotionFromUserText(trimmed);
    if (fromUser) setCharacterEmotion(fromUser);

    const pumpSpeech = (flush = false) => {
      if (!ttsEnabledRef.current || streamGen !== ttsGenRef.current) return;
      const tagMatch = streamBotRef.current.match(/^\s*[\[【(（]([^\]】)）]+)[\]】)）]/);
      const cnTag = tagMatch?.[1]?.trim();
      const speech = cleanForSpeech(stripEmotionTag(streamBotRef.current));
      const { sentences, next } = takeReadySentences(speech, ttsSpokenLenRef.current);
      const wrap = (s: string) => (cnTag ? `[${cnTag}]${s}` : s);
      for (const s of sentences) {
        enqueueSentence(wrap(s), {
          emotion: replyEmotion || undefined,
          userText: trimmed,
          gen: streamGen,
        });
      }
      ttsSpokenLenRef.current = next;
      if (flush) {
        const rest = speech.slice(ttsSpokenLenRef.current).trim();
        if (rest.length >= 2) {
          enqueueSentence(wrap(rest), {
            emotion: replyEmotion || undefined,
            userText: trimmed,
            gen: streamGen,
          });
        }
        ttsSpokenLenRef.current = speech.length;
      }
    };

    if (opts?.isRetry) {
      setMessages((prev) => {
        const next = [...prev];
        if (next[next.length - 1]?.role === "assistant") next.pop();
        next.push({ id: uid(), role: "assistant", content: "" });
        return next;
      });
    } else {
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "user", content: trimmed },
        { id: uid(), role: "assistant", content: "" },
      ]);
    }

    let replyFinished = false;
    try {
      // 用缓存环境立刻开聊，避免每次等定位/天气
      const env = envRef.current ?? (await collectEnvContext());
      envRef.current = env;
      void collectEnvContext().then((fresh) => {
        envRef.current = fresh;
      });

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          user_id: session.userId,
          stream: true,
          env_context: env,
        }),
      });
      if (!res.ok || !res.body) throw new Error("fail");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          let payload: Record<string, unknown>;
          try {
            payload = JSON.parse(line.slice(5).trim()) as Record<string, unknown>;
          } catch {
            // 半包 / 代理掐断时可能出现残缺 JSON，忽略即可
            continue;
          }
          // 正文已完成后的 chips/尾包错误，不当整轮失败
          if (payload.error) {
            if (replyFinished || streamBotRef.current.trim()) break;
            throw new Error("fail");
          }
          if (typeof payload.token === "string") {
            streamBotRef.current += payload.token;
            setMessages((prev) => {
              const idx = [...prev].reverse().findIndex((m) => m.role === "assistant");
              if (idx < 0) return prev;
              const realIdx = prev.length - 1 - idx;
              return prev.map((m, i) =>
                i === realIdx
                  ? { ...m, content: stripEmotionTag(streamBotRef.current) }
                  : m
              );
            });
            pumpSpeech(false);
          }
          if (Array.isArray(payload.quick_replies)) {
            setQuickReplies(payload.quick_replies as string[]);
          }
          if (typeof payload.emotion === "string" && payload.emotion) {
            replyEmotion = payload.emotion;
            const fromTag = emotionToCharacter(streamBotRef.current);
            setCharacterEmotion(
              fromTag !== "neutral" ? fromTag : emotionToCharacter(payload.emotion)
            );
          }
          if (payload.done) {
            const fromTag = emotionToCharacter(streamBotRef.current);
            if (fromTag !== "neutral") setCharacterEmotion(fromTag);
            pumpSpeech(true);
            if (!replyFinished) {
              replyFinished = true;
              setBusy(false); // 正文结束立刻解除「正在想」，不等快捷回复
            }
          }
        }
      }
      lastFailedTextRef.current = null;
      setShowRetry(false);
      if (!replyFinished) {
        // 流提前结束但已有正文：当成功，别弹「连不上」
        if (streamBotRef.current.trim()) {
          replyFinished = true;
          pumpSpeech(true);
        }
        setBusy(false);
      }
      void refreshMemories();
    } catch {
      const kept = stripEmotionTag(streamBotRef.current).trim();
      if (replyFinished || kept) {
        // 说完后网络/快捷回复抖动：保留原话，不盖成断线文案
        lastFailedTextRef.current = null;
        setShowRetry(false);
        setMessages((prev) => {
          const idx = [...prev].reverse().findIndex((m) => m.role === "assistant");
          if (idx < 0) return prev;
          const realIdx = prev.length - 1 - idx;
          return prev.map((m, i) =>
            i === realIdx ? { ...m, content: kept || m.content } : m
          );
        });
      } else {
        lastFailedTextRef.current = trimmed;
        setShowRetry(true);
        setMessages((prev) => {
          const idx = [...prev].reverse().findIndex((m) => m.role === "assistant");
          if (idx < 0) return prev;
          const realIdx = prev.length - 1 - idx;
          return prev.map((m, i) =>
            i === realIdx
              ? {
                  ...m,
                  content: "刚才断了一下。点下面的圆圈，我重新听你说。",
                }
              : m
          );
        });
      }
    } finally {
      setBusy(false);
    }
  }

  function handleRetry() {
    const text = lastFailedTextRef.current;
    if (!text || busy) return;
    void sendMessage(text, { isRetry: true });
  }

  async function playTtsSample(sample: { text: string }) {
    unlockAudioPlayback();
    await speakEdgeTts(sample.text);
  }

  async function fetchTtsBlob(
    text: string,
    opts?: { emotion?: string; userText?: string }
  ): Promise<Blob | null> {
    const spoken = cleanForSpeech(text);
    if (!spoken) return null;
    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: spoken,
          emotion: opts?.emotion || undefined,
          user_text: opts?.userText || undefined,
          voice_type: voiceTypeRef.current || undefined,
        }),
      });
      if (!res.ok) {
        console.warn("[TTS] 后端返回错误:", res.status, await res.text().catch(() => ""));
        return null;
      }
      const usedEmotion = res.headers.get("X-Heal-Emotion");
      if (usedEmotion) {
        console.info("[TTS] 实际语气:", usedEmotion);
        setCharacterEmotion(emotionToCharacter(usedEmotion));
      }
      const blob = await res.blob();
      return blob.size ? blob : null;
    } catch (err) {
      console.warn("[TTS] 请求失败:", err);
      return null;
    }
  }

  function enqueueSentence(
    text: string,
    opts: { emotion?: string; userText?: string; gen: number }
  ) {
    if (!ttsEnabledRef.current || opts.gen !== ttsGenRef.current) return;
    const spoken = cleanForSpeech(text);
    if (!spoken) return;
    const blobP = fetchTtsBlob(spoken, {
      emotion: opts.emotion,
      userText: opts.userText,
    }).then((blob) => (opts.gen === ttsGenRef.current ? blob : null));
    ttsQueueRef.current.push({ text: spoken, blobP });
    void drainTtsQueue(opts.gen);
  }

  async function drainTtsQueue(gen: number) {
    if (ttsDrainingRef.current) return;
    ttsDrainingRef.current = true;
    try {
      while (ttsQueueRef.current.length && gen === ttsGenRef.current && ttsEnabledRef.current) {
        const clip = ttsQueueRef.current.shift();
        if (!clip) break;
        const blob = await clip.blobP;
        if (!blob || gen !== ttsGenRef.current || !ttsEnabledRef.current) continue;
        await playTtsBlob(blob, gen);
      }
    } finally {
      ttsDrainingRef.current = false;
      if (!ttsQueueRef.current.length || gen !== ttsGenRef.current) {
        setCharacterSpeaking(false);
      } else if (ttsEnabledRef.current) {
        void drainTtsQueue(gen);
      }
    }
  }

  function playTtsBlob(blob: Blob, gen: number): Promise<void> {
    return new Promise((resolve) => {
      if (gen !== ttsGenRef.current || !ttsEnabledRef.current) {
        resolve();
        return;
      }
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      ttsAudioRef.current = audio;
      setCharacterSpeaking(true);
      const finish = () => {
        URL.revokeObjectURL(url);
        if (ttsAudioRef.current === audio) ttsAudioRef.current = null;
        resolve();
      };
      audio.onended = finish;
      audio.onerror = () => {
        console.warn("[TTS] 播放失败");
        finish();
      };
      void audio.play().catch((err: unknown) => {
        console.warn("[TTS] autoplay blocked — 请点一次顶部 🔊 再试:", err);
        finish();
      });
    });
  }

  /** 整段朗读（调音板 / 问候一句）；会打断当前分句队列 */
  async function speakEdgeTts(
    text: string,
    opts?: { emotion?: string; userText?: string }
  ) {
    const spoken = cleanForSpeech(text);
    if (!spoken) return;
    resetTtsPipeline();
    const gen = ttsGenRef.current;
    enqueueSentence(spoken, {
      emotion: opts?.emotion,
      userText: opts?.userText,
      gen,
    });
  }

  function resetTtsPipeline() {
    ttsGenRef.current += 1;
    ttsSpokenLenRef.current = 0;
    ttsQueueRef.current = [];
    ttsDrainingRef.current = false;
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current.src = "";
      ttsAudioRef.current = null;
    }
    setCharacterSpeaking(false);
  }

  function stopTtsAudio() {
    resetTtsPipeline();
  }

  function handleToggleTTS() {
    setTtsEnabled((v) => {
      if (v) {
        stopTtsAudio();
        return false;
      }
      // 开启瞬间解锁 autoplay（用户点击手势）
      unlockAudioPlayback();
      return true;
    });
  }

  function proactiveCooldownOk() {
    try {
      const raw = localStorage.getItem("heal-last-proactive");
      if (!raw) return true;
      const last = Number(raw);
      if (!Number.isFinite(last)) return true;
      // 低密度：约 90 分钟内不重复主动找你
      return Date.now() - last > 90 * 60 * 1000;
    } catch {
      return true;
    }
  }

  function markProactiveSent() {
    try {
      localStorage.setItem("heal-last-proactive", String(Date.now()));
    } catch {
      /* ignore */
    }
  }

  /** 根据过往记忆/对话主动来一句；stayOnHome=true 时只在首页浮云展示 */
  async function onMissYou(goChat = true, opts?: { softBubble?: boolean }) {
    if (missBusy || busy) return;
    setMissBusy(true);
    try {
      const env = await collectEnvContext();
      envRef.current = env;
      const res = await fetch("/api/ping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: session.userId, env_context: env }),
      });
      if (!res.ok) throw new Error("fail");
      const data = await res.json();
      const text = stripEmotionTag(String(data.message || ""));
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "assistant", content: text },
      ]);
      markProactiveSent();
      if (opts?.softBubble && text) {
        setProactiveBubble(text);
      }
      if (ttsEnabledRef.current && data.message && goChat) {
        unlockAudioPlayback();
        void speakEdgeTts(String(data.message));
      }
      if (goChat) {
        setProactiveBubble(null);
        setScreen("chat");
        setShowNotebook(false);
      }
    } catch {
      const fallback = "我刚想过来看看你，但这会儿没连稳。等一下，我再试着找你。";
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "assistant", content: fallback },
      ]);
      if (opts?.softBubble) setProactiveBubble(fallback);
      if (goChat) {
        setProactiveBubble(null);
        setScreen("chat");
      }
    } finally {
      setMissBusy(false);
    }
  }

  // 账号切换后允许重新主动问候
  useEffect(() => {
    proactiveFetchedRef.current = false;
    setProactiveBubble(null);
  }, [session.userId]);

  // 回到 Home：低密度根据过往聊天主动冒一句浮云
  useEffect(() => {
    if (screen !== "home" || !session.onboarded) return;
    if (proactiveFetchedRef.current) return;
    if (!proactiveCooldownOk()) return;
    proactiveFetchedRef.current = true;
    const t = window.setTimeout(() => {
      void onMissYou(false, { softBubble: true });
    }, 1600);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, session.onboarded, session.userId]);

  async function enterChat(withNotebook = false) {
    await loadHistory();
    setShowNotebook(withNotebook);
    setScreen("chat");
  }

  return (
    <div className="app-shell">
    <div className="world">
      {/* 全局立绘背景 — ChatRoom 会用自己的 absolute 层覆盖 */}
      <div className="world-bg" aria-hidden>
        <img src="/images/heal-character-main.jpg" alt="" draggable={false} />

        {/* 角色身后梦幻紫光晕 */}
        <div className="world-char-glow" />
        <div className="world-bg-overlay" />
      </div>
      <div className="glow glow-a" aria-hidden />
      <div className="glow glow-b" aria-hidden />

      {screen === "welcome" && (
        <Welcome
          onEnter={() => setScreen(session.onboarded ? "home" : "greet")}
          onReset={() => {
            const fresh = resetSession();
            setSession(fresh);
            setMessages([{
              id: "welcome",
              role: "assistant",
              content: "我在。今天先不用整理好再说，想到哪儿就从哪儿开始。",
            }]);
            setScreen("greet");
          }}
          isReturning={session.onboarded}
        />
      )}

      {screen === "greet" && (
        <Greet initialName={session.nickname} onDone={finishGreet} />
      )}

      {screen === "firstmeet" && (
        <FirstMeet
          nickname={session.nickname || "你"}
          onContinue={() => setScreen("home")}
        />
      )}

      {screen === "home" && (
        <Home
          nickname={session.nickname || "你"}
          memories={memories}
          missBusy={missBusy}
          proactiveBubble={proactiveBubble}
          onChat={() => {
            setProactiveBubble(null);
            void enterChat(false);
          }}
          onNotebook={() => {
            setProactiveBubble(null);
            void enterChat(true);
          }}
          onMissYou={() => void onMissYou(true)}
          onOpenProactive={() => {
            setProactiveBubble(null);
            void enterChat(false);
          }}
          onDismissProactive={() => setProactiveBubble(null)}
          onToggleMusic={() => setShowMusicPanel((v) => !v)}
          onLeave={() => setScreen("welcome")}
        />
      )}

      {screen === "chat" && (
        <ChatRoom
          nickname={session.nickname || "你"}
          daysTogether={daysTogether(session)}
          messages={messages}
          memories={memories}
          busy={busy || missBusy}
          showNotebook={showNotebook}
          quickReplies={quickReplies}
          ttsEnabled={ttsEnabled}
          voiceType={voiceType}
          characterEmotion={characterEmotion}
          characterSpeaking={characterSpeaking}
          showRetry={showRetry}
          onRetry={handleRetry}
          onVoiceTypeChange={setVoiceType}
          onToggleMusic={() => setShowMusicPanel((v) => !v)}
          onToggleTTS={handleToggleTTS}
          onToggleNotebook={() => {
            setShowNotebook((v) => !v);
            void refreshMemories();
          }}
          onSend={(t) => void sendMessage(t)}
          onPlayTtsSample={(s) => void playTtsSample(s)}
          onPreviewEmotion={setCharacterEmotion}
          onMissYou={() => void onMissYou(false)}
          onBack={() => {
            setShowNotebook(false);
            setScreen("home");
            void refreshMemories();
          }}
        />
      )}
      {/* ── 全局音乐播放器（不随 screen 切换而卸载）── */}
      <AmbientPlayer
        panelOpen={showMusicPanel}
        onClose={() => setShowMusicPanel(false)}
      />
    </div>
    </div>
  );
}
