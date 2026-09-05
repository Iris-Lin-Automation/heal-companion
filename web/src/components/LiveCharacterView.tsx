/**
 * Layer 0 — 全屏角色立绘底层
 *
 * 立绘三态（同角色）：
 *   idle  = 闭嘴睁眼
 *   blink = 闭嘴闭眼（随机眨眼）
 *   speak = 张嘴（TTS 播放时假口型）
 *
 * 委屈/流泪等情绪图暂无配套口型，说话时不硬切张嘴。
 */

import { useEffect, useState } from "react";

export type CharacterEmotion =
  | "neutral"
  | "bright"
  | "warm"
  | "hurt"
  | "aggrieved"
  | "serious" // 一点生气
  | "angry" // 非常生气
  | "shy"
  | "playful"
  | "hot";

const IDLE = "/images/heal-character-idle.png";
const BLINK = "/images/heal-character-blink.png";
const SPEAK = "/images/heal-character-speak.png";
const SMILE = "/images/heal-character-smile.png";
const ANGRY_MILD = "/images/heal-character-angry.png";
const ANGRY_FIERCE = "/images/heal-character-angry-fierce.png";
const SHY = "/images/heal-character-shy.png";

/** 情绪 → 立绘 */
const EMOTION_PORTRAIT: Partial<Record<CharacterEmotion, string>> = {
  aggrieved: "/images/heal-character-aggrieved.png",
  hurt: "/images/heal-character-hurt-tears.png",
  serious: ANGRY_MILD, // 一点生气
  angry: ANGRY_FIERCE, // 非常生气
  shy: SHY,
  bright: SMILE,
  warm: SMILE,
  playful: SMILE,
  hot: SMILE,
};

/** 有专属立绘的情绪：不做眨眼/张嘴切换，避免串图 */
function isLockedEmotion(emotion: CharacterEmotion) {
  return emotion in EMOTION_PORTRAIT;
}

type Props = {
  src?: string;
  alt?: string;
  emotion?: CharacterEmotion;
  speaking?: boolean;
  modelSrc?: string;
};

export default function LiveCharacterView({
  src = IDLE,
  alt = "",
  emotion = "neutral",
  speaking = false,
  modelSrc,
}: Props) {
  const [blinking, setBlinking] = useState(false);
  const [mouthOpen, setMouthOpen] = useState(false);

  // 随机眨眼（说话时不眨，避免和口型抢）
  useEffect(() => {
    if (speaking || isLockedEmotion(emotion)) {
      setBlinking(false);
      return;
    }
    let cancelled = false;
    let blinkTimer = 0;
    let waitTimer = 0;

    const schedule = () => {
      const wait = 2200 + Math.random() * 4200;
      waitTimer = window.setTimeout(() => {
        if (cancelled) return;
        setBlinking(true);
        blinkTimer = window.setTimeout(() => {
          if (cancelled) return;
          setBlinking(false);
          schedule();
        }, 120 + Math.random() * 80);
      }, wait);
    };

    schedule();
    return () => {
      cancelled = true;
      window.clearTimeout(waitTimer);
      window.clearTimeout(blinkTimer);
    };
  }, [speaking, emotion]);

  // TTS 播放时：不规则开合，更像活人
  useEffect(() => {
    if (!speaking || isLockedEmotion(emotion)) {
      setMouthOpen(false);
      return;
    }
    let cancelled = false;
    let timer = 0;
    let open = true;
    setMouthOpen(true);

    const tick = () => {
      if (cancelled) return;
      open = !open;
      setMouthOpen(open);
      const delay = open
        ? 90 + Math.random() * 110
        : 140 + Math.random() * 220;
      timer = window.setTimeout(tick, delay);
    };

    timer = window.setTimeout(tick, 120);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      setMouthOpen(false);
    };
  }, [speaking, emotion]);

  // 预加载，减少切图闪白
  useEffect(() => {
    [
      IDLE,
      BLINK,
      SPEAK,
      SMILE,
      ANGRY_MILD,
      ANGRY_FIERCE,
      SHY,
      "/images/heal-character-aggrieved.png",
      "/images/heal-character-hurt-tears.png",
    ].forEach((href) => {
      const img = new Image();
      img.src = href;
    });
  }, []);

  const base = EMOTION_PORTRAIT[emotion] ?? src;
  let portraitSrc = base;
  if (!isLockedEmotion(emotion)) {
    if (speaking && mouthOpen) portraitSrc = SPEAK;
    else if (blinking) portraitSrc = BLINK;
    else portraitSrc = IDLE;
  }

  return (
    <div
      className={`char-bg emotion-${emotion} ${speaking ? "is-speaking" : ""}`}
      data-live2d-model={modelSrc || ""}
      aria-hidden
    >
      <div className="char-aura" />
      <img
        src={portraitSrc}
        alt={alt}
        className="char-portrait"
        draggable={false}
      />
      <div className="char-eye-light" />
      <div className="char-speech-pulse" />
      <div className="char-gradient" />
    </div>
  );
}
