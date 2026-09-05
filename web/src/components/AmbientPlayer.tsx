/**
 * AmbientPlayer — 全局脑波声学调理（浮动面板版）
 *
 * 架构：
 *   - 挂在 App.tsx 顶层，整个应用生命周期内不卸载（音频持续）
 *   - panelOpen=false → 完全隐形，不占任何布局空间
 *   - panelOpen=true  → 从底部弹出一个浮动毛玻璃面板（Popover），
 *                        点击面板外部/关闭按钮收起，音频继续
 *
 * 绝对不渲染任何固定底栏（mini-bar）。
 * 主界面按钮、Dock 完全不受影响。
 */

import { useEffect, useRef, useState } from "react";

// ── 数据结构 ─────────────────────────────────────────────────────────────────

interface Track {
  id: string;
  icon: string;
  label: string;
}

interface Mode {
  id: string;
  wave: string;
  hz: string;
  name: string;
  desc: string;
  carrierFreq: number;
  beatFreq: number;
  brownGain: number;
  tracks: Track[];
}

const MODES: Mode[] = [
  {
    id: "theta",
    wave: "θ 波",
    hz: "6 Hz",
    name: "🌙 深眠降频",
    desc: "切断躺下后的脑内杂念，引导自然入眠",
    carrierFreq: 200,
    beatFreq: 6,
    brownGain: 0.15,
    tracks: [
      { id: "theta_synth", icon: "🎵", label: "双耳差频合成" },
      { id: "theta_rain",  icon: "🌧", label: "树荫下的雨声" },
    ],
  },
  {
    id: "alpha",
    wave: "α 波",
    hz: "10 Hz",
    name: "🌿 躯体松弛",
    desc: "缓解肌肉与神经紧绷，适合工作后放空",
    carrierFreq: 220,
    beatFreq: 10,
    brownGain: 0.08,
    tracks: [
      { id: "alpha_synth",  icon: "🎵", label: "双耳差频合成" },
      { id: "alpha_forest", icon: "🌲", label: "热带雨林雨声" },
    ],
  },
  {
    id: "hrv",
    wave: "HRV",
    hz: "0.1 Hz",
    name: "🌊 呼吸共振",
    desc: "副交感神经修复，6 次/分钟心率共振",
    carrierFreq: 150,
    beatFreq: 0.1,
    brownGain: 0.25,
    tracks: [
      { id: "hrv_synth",     icon: "🎵", label: "双耳差频合成" },
      { id: "hrv_bowl",      icon: "🔔", label: "颂钵击声（循环）" },
      { id: "hrv_rain_bowl", icon: "🌧🔔", label: "雨声 + 颂钵叠层" },
    ],
  },
];

const TRACK_FILE: Record<string, string> = {
  theta_rain:    "/sounds/rain_undertree.mp3",
  alpha_forest:  "/sounds/rain_forest.mp3",
  hrv_bowl:      "/sounds/bowl_struck.wav",
  hrv_rain_bowl: "/sounds/rain_undertree.mp3",
};

// ── Web Audio 工具 ────────────────────────────────────────────────────────────

function makeBrownNoise(ctx: AudioContext, dst: AudioNode, weight: number) {
  const len = ctx.sampleRate * 5;
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  let last = 0;
  for (let i = 0; i < len; i++) {
    const w = Math.random() * 2 - 1;
    d[i] = (last + 0.02 * w) / 1.02;
    last = d[i];
    d[i] *= 3.5;
  }
  const src = ctx.createBufferSource();
  src.buffer = buf;
  src.loop = true;
  const g = ctx.createGain();
  g.gain.value = weight;
  src.connect(g);
  g.connect(dst);
  src.start();
  return src;
}

function makeBinaural(ctx: AudioContext, dst: AudioNode, carrier: number, beat: number, gainVal: number) {
  const merger = ctx.createChannelMerger(2);
  const L = ctx.createOscillator(); L.type = "sine"; L.frequency.value = carrier;
  const R = ctx.createOscillator(); R.type = "sine"; R.frequency.value = carrier + beat;
  L.connect(merger, 0, 0);
  R.connect(merger, 0, 1);
  const g = ctx.createGain(); g.gain.value = gainVal;
  merger.connect(g); g.connect(dst);
  L.start(); R.start();
  return { L, R };
}

// ── Component ────────────────────────────────────────────────────────────────

type Props = {
  panelOpen: boolean;
  onClose: () => void;
};

export default function AmbientPlayer({ panelOpen, onClose }: Props) {
  const [playingTrack, setPlayingTrack] = useState<string | null>(null);
  const [volume, setVolume]             = useState(0.35);
  const [expandedMode, setExpandedMode] = useState<string | null>("theta");

  const ctxRef       = useRef<AudioContext | null>(null);
  const masterRef    = useRef<GainNode | null>(null);
  const oscLRef      = useRef<OscillatorNode | null>(null);
  const oscRRef      = useRef<OscillatorNode | null>(null);
  const noiseRef     = useRef<AudioBufferSourceNode | null>(null);
  const audioRef     = useRef<HTMLAudioElement | null>(null);
  const bowlTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 应用生命周期结束时才销毁
  useEffect(() => () => { stopAll(); }, []);

  // 音量实时同步
  useEffect(() => {
    if (masterRef.current) masterRef.current.gain.value = volume;
    if (audioRef.current)  audioRef.current.volume = volume;
  }, [volume]);

  function stopAll() {
    try { oscLRef.current?.stop(); oscRRef.current?.stop(); } catch {/**/}
    try { noiseRef.current?.stop(); } catch {/**/}
    ctxRef.current?.close().catch(() => {/**/});
    ctxRef.current = masterRef.current = oscLRef.current = oscRRef.current = noiseRef.current = null;
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if (bowlTimerRef.current) { clearInterval(bowlTimerRef.current); bowlTimerRef.current = null; }
    setPlayingTrack(null);
  }

  function findMode(trackId: string) {
    return MODES.find((m) => m.tracks.some((t) => t.id === trackId));
  }

  function playTrack(trackId: string) {
    if (playingTrack === trackId) { stopAll(); return; }
    stopAll();

    const mode = findMode(trackId);
    if (!mode) return;

    const ctx = new AudioContext();
    ctxRef.current = ctx;

    const master = ctx.createGain();
    master.gain.value = volume;
    master.connect(ctx.destination);
    masterRef.current = master;

    const isSynth   = !TRACK_FILE[trackId];
    const binGain   = isSynth ? 0.08 : 0.035;
    const noiseW    = (isSynth ? mode.brownGain : mode.brownGain * 0.25);

    const { L, R } = makeBinaural(ctx, master, mode.carrierFreq, mode.beatFreq, binGain);
    oscLRef.current = L; oscRRef.current = R;
    if (noiseW > 0) noiseRef.current = makeBrownNoise(ctx, master, noiseW);

    if (TRACK_FILE[trackId]) {
      const audio = new Audio(TRACK_FILE[trackId]);
      audio.volume = volume;
      audioRef.current = audio;

      if (trackId === "hrv_bowl") {
        const ring = () => { const b = new Audio("/sounds/bowl_struck.wav"); b.volume = Math.min(volume * 1.3, 1); b.play().catch(() => {/**/}); };
        ring();
        bowlTimerRef.current = setInterval(ring, 9000);
      } else {
        audio.loop = true;
        audio.play().catch(() => {/**/});
        if (trackId === "hrv_rain_bowl") {
          const ring = () => { const b = new Audio("/sounds/bowl_struck.wav"); b.volume = Math.min(volume * 0.65, 1); b.play().catch(() => {/**/}); };
          ring();
          bowlTimerRef.current = setInterval(ring, 9000);
        }
      }
    }

    setPlayingTrack(trackId);
  }

  // ── 完全不渲染时 (panelOpen=false)，零 DOM 输出 ───────────────────────────
  if (!panelOpen) return null;

  // ── 浮动面板 ──────────────────────────────────────────────────────────────
  return (
    <>
      {/* 背景遮罩（透明，点击即关闭面板） */}
      <div className="ap-backdrop" onClick={onClose} aria-hidden />

      {/* 浮动毛玻璃面板 */}
      <div className="ap-panel" role="dialog" aria-label="脑波声学调理">

        {/* 标题 + 关闭 */}
        <div className="ap-header">
          <span className="ap-title">🧠 脑波声学调理</span>
          <button type="button" className="ap-close" onClick={onClose} aria-label="关闭">✕</button>
        </div>

        {/* 模式列表 */}
        {MODES.map((mode) => {
          const expanded   = expandedMode === mode.id;
          const modeActive = mode.tracks.some((t) => t.id === playingTrack);
          return (
            <div key={mode.id} className={`ap-mode ${modeActive ? "active" : ""}`}>
              <button
                type="button"
                className="ap-mode-row"
                onClick={() => setExpandedMode(expanded ? null : mode.id)}
              >
                <span className="ap-badges">
                  <span className="ap-badge">{mode.wave}</span>
                  <span className="ap-badge ap-badge-hz">{mode.hz}</span>
                </span>
                <span className="ap-mode-info">
                  <span className="ap-mode-name">{mode.name}</span>
                  <span className="ap-mode-desc">{mode.desc}</span>
                </span>
                <span className="ap-chevron">{expanded ? "▾" : "▸"}</span>
              </button>

              {expanded && (
                <div className="ap-tracks">
                  {mode.tracks.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      className={`ap-track ${playingTrack === t.id ? "playing" : ""}`}
                      onClick={() => playTrack(t.id)}
                    >
                      <span className="ap-track-icon">{t.icon}</span>
                      <span className="ap-track-name">{t.label}</span>
                      {playingTrack === t.id && <span className="ap-playing-dot" />}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* 音量 */}
        <div className="ap-vol">
          <span className="ap-vol-ico">🔈</span>
          <input
            type="range" min={0.02} max={0.9} step={0.01}
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="ap-slider"
            aria-label="音量"
          />
          <span className="ap-vol-ico">🔊</span>
          <span className="ap-vol-num">{Math.round(volume * 100)}%</span>
        </div>

        {/* 正在播放提示 */}
        {playingTrack && (
          <div className="ap-now">
            <span className="ap-now-dot" />
            <span className="ap-now-label">
              正在播放：{MODES.flatMap((m) => m.tracks).find((t) => t.id === playingTrack)?.label}
            </span>
            <button type="button" className="ap-stop-btn" onClick={stopAll}>■ 停止</button>
          </div>
        )}
      </div>
    </>
  );
}
