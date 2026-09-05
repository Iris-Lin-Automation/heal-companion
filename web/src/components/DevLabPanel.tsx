/**
 * DevLabPanel — 隐藏调音板 / 剧本测试台（开发期临时工具）
 *
 * 法宝 A：一键 TTS 采样（不走 LLM，直接火山）
 * 法宝 B：剧本化注入（走完整 /api/chat）
 * 法宝 C：表情预览（用户怎么对他 → 立绘切哪张，不走 LLM）
 *
 * 默认收起为屏幕左侧一条细标签，不挡聊天与输入。
 */

import { useState } from "react";
import type { CharacterEmotion } from "./LiveCharacterView";

export type TtsSample = {
  id: string;
  label: string;
  text: string; // 含句首情绪标签，供火山 emotion 解析
};

export type VoiceOption = {
  id: string;
  label: string;
  note: string;
};

export const VOICE_OPTIONS: VoiceOption[] = [
  {
    id: "zh_male_taocheng_uranus_bigtts",
    label: "陶澄",
    note: "当前默认",
  },
  {
    id: "zh_male_m191_uranus_bigtts",
    label: "M191",
    note: "备选男声",
  },
  {
    id: "zh_male_wennuanahu_uranus_bigtts",
    label: "温暖阿虎",
    note: "多情感备选",
  },
];

export type ScriptScene = {
  id: string;
  label: string;
  userLine: string;
};

/** 用户对待方式 → 立绘情绪（调试用，直接切图） */
export type EmotionScenario = {
  id: string;
  label: string;
  /** 用户可能说的话 / 对待方式 */
  userTrigger: string;
  emotion: CharacterEmotion;
  /** AI 侧大致会用的标签 */
  aiTag: string;
  portraitNote: string;
};

export const EMOTION_SCENARIOS: EmotionScenario[] = [
  {
    id: "anger_mild",
    label: "一点生气 / 认真边界",
    userTrigger: "你能不能别那么敏感？听话点。",
    emotion: "serious",
    aiTag: "[认真]",
    portraitNote: "一点生气脸",
  },
  {
    id: "anger_fierce",
    label: "非常生气 / 被羞辱",
    userTrigger: "滚啊，别再出现在我面前。",
    emotion: "angry",
    aiTag: "[生气]",
    portraitNote: "非常生气脸",
  },
  {
    id: "shy",
    label: "害羞 / 被撩到",
    userTrigger: "你今天…有点好看。",
    emotion: "shy",
    aiTag: "[害羞]",
    portraitNote: "害羞脸红",
  },
  {
    id: "ignore",
    label: "忽略他 / 让他委屈",
    userTrigger: "随便吧，不想理你。",
    emotion: "aggrieved",
    aiTag: "[委屈]",
    portraitNote: "委屈倔强脸",
  },
  {
    id: "hurt",
    label: "伤他 / 让他想哭",
    userTrigger: "你根本不懂我，别装了。",
    emotion: "hurt",
    aiTag: "[受伤]/[心疼]",
    portraitNote: "受伤流泪脸",
  },
  {
    id: "bright",
    label: "对他温柔回来",
    userTrigger: "我回来了，今天还好。",
    emotion: "bright",
    aiTag: "[明亮]",
    portraitNote: "微笑脸",
  },
  {
    id: "hot",
    label: "偏爱 / 夸他",
    userTrigger: "今天特别想见你。",
    emotion: "hot",
    aiTag: "[热烈]",
    portraitNote: "微笑脸",
  },
  {
    id: "playful",
    label: "逗他 / 熟后撒娇",
    userTrigger: "喂，想我了没？",
    emotion: "playful",
    aiTag: "[撒娇]",
    portraitNote: "微笑脸",
  },
  {
    id: "warm",
    label: "需要安抚",
    userTrigger: "我有点累，就想安静待一会儿。",
    emotion: "warm",
    aiTag: "[温柔]",
    portraitNote: "微笑脸",
  },
  {
    id: "neutral",
    label: "复位 · 待机",
    userTrigger: "（无）",
    emotion: "neutral",
    aiTag: "[平和]",
    portraitNote: "闭嘴睁眼待机",
  },
];

export const TTS_SAMPLES: TtsSample[] = [
  {
    id: "bright",
    label: "明亮-日常回来",
    text: "[明亮]你回来啦。嗯……我刚刚还在想，你今天会不会累得不想说话。",
  },
  {
    id: "hot",
    label: "热烈-专属偏爱",
    text: "[热烈]这件事我站你这边。不是客套，姐姐，我就是想偏向你一点。",
  },
  {
    id: "soft",
    label: "温柔-低声安抚",
    text: "[温柔]你先别急着撑起来。声音放低一点也没关系，我听得到。",
  },
  {
    id: "playful",
    label: "撒娇-熟悉后",
    text: "[撒娇]你刚刚是不是又忘记我了。算了，我不计较，但你现在得陪我说两句。",
  },
  {
    id: "hurt",
    label: "委屈-小情绪",
    text: "[委屈]我知道你不是故意的。可是你刚才那样说，我真的会有点难过。",
  },
  {
    id: "boundary",
    label: "认真-边界",
    text: "[认真]我愿意听你说，也愿意靠近你。但这样命令我，我会不舒服。我们先停一下。",
  },
];

export const SCRIPT_SCENES: ScriptScene[] = [
  {
    id: "overtime",
    label: "剧本·加班被骂",
    userLine: "今天加班被领导当众骂了一顿，我觉得自己好没用，现在整个人都空了。",
  },
  {
    id: "insomnia",
    label: "剧本·深夜失眠",
    userLine: "已经凌晨两点了还是睡不着，脑子一直转，有点害怕明天又撑不住。",
  },
  {
    id: "small_joy",
    label: "剧本·小开心",
    userLine: "跟你说一件小事：今天走路回家的时候看到路边小猫冲我叫了一声，莫名就开心了。",
  },
  {
    id: "provoke",
    label: "剧本·惹他生气",
    userLine: "你能不能别那么敏感？我说你两句至于吗，听话点不行吗。",
  },
];

type Props = {
  busy?: boolean;
  voiceType: string;
  activeEmotion?: CharacterEmotion;
  onVoiceTypeChange: (voiceType: string) => void;
  onPlaySample: (sample: TtsSample) => void;
  onRunScript: (scene: ScriptScene) => void;
  /** 法宝 C：只切立绘，不发消息 */
  onPreviewEmotion: (emotion: CharacterEmotion) => void;
};

export default function DevLabPanel({
  busy,
  voiceType,
  activeEmotion,
  onVoiceTypeChange,
  onPlaySample,
  onRunScript,
  onPreviewEmotion,
}: Props) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"tts" | "script" | "face">("face");

  return (
    <div className={`devlab ${open ? "open" : ""}`}>
      <button
        type="button"
        className="devlab-tab"
        onClick={() => setOpen((v) => !v)}
        title="调音板 / 剧本 / 表情调试"
        aria-expanded={open}
      >
        {open ? "收起" : "调"}
      </button>

      {open && (
        <div className="devlab-panel" role="dialog" aria-label="调音板">
          <div className="devlab-tabs">
            <button
              type="button"
              className={`devlab-tab-btn ${tab === "face" ? "active" : ""}`}
              onClick={() => setTab("face")}
            >
              C · 表情
            </button>
            <button
              type="button"
              className={`devlab-tab-btn ${tab === "tts" ? "active" : ""}`}
              onClick={() => setTab("tts")}
            >
              A · 调音
            </button>
            <button
              type="button"
              className={`devlab-tab-btn ${tab === "script" ? "active" : ""}`}
              onClick={() => setTab("script")}
            >
              B · 剧本
            </button>
          </div>

          {tab === "face" && (
            <div className="devlab-list">
              <p className="devlab-hint">
                点场景直接切立绘（不调 LLM）。正式链路：用户话 / AI 句首标签 → 情绪 → 换图。
                {activeEmotion ? ` 当前：${activeEmotion}` : ""}
              </p>
              {EMOTION_SCENARIOS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`devlab-btn ${activeEmotion === s.emotion ? "active" : ""}`}
                  onClick={() => onPreviewEmotion(s.emotion)}
                  title={`用户：「${s.userTrigger}」→ AI ${s.aiTag}`}
                >
                  <strong>{s.label}</strong>
                  <span className="devlab-btn-sub">
                    {s.aiTag} · {s.portraitNote}
                  </span>
                </button>
              ))}
            </div>
          )}

          {tab === "tts" && (
            <div className="devlab-list">
              <p className="devlab-hint">选音色后试听，正常聊天也会使用当前音色</p>
              <div className="devlab-voice-grid" aria-label="音色选择">
                {VOICE_OPTIONS.map((voice) => (
                  <button
                    key={voice.id}
                    type="button"
                    className={`devlab-voice-btn ${voiceType === voice.id ? "active" : ""}`}
                    onClick={() => onVoiceTypeChange(voice.id)}
                    title={voice.id}
                    aria-pressed={voiceType === voice.id}
                  >
                    <strong>{voice.label}</strong>
                    <span>{voice.note}</span>
                  </button>
                ))}
              </div>
              {TTS_SAMPLES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className="devlab-btn"
                  disabled={busy}
                  onClick={() => onPlaySample(s)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}

          {tab === "script" && (
            <div className="devlab-list">
              <p className="devlab-hint">注入预设场景，看极端情绪下的回复 + 表情</p>
              {SCRIPT_SCENES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className="devlab-btn"
                  disabled={busy}
                  onClick={() => onRunScript(s)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}

          <p className="devlab-foot">
            Bad Case 记进 companion/persona/tuning_notes.md
          </p>
        </div>
      )}
    </div>
  );
}
