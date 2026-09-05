import { useEffect, useState } from "react";

type Props = {
  nickname: string;
  onContinue: () => void;
};

/**
 * 初遇场景 — 现实系初识感，Greet 完成后触发一次
 *
 * 立绘从 world-bg 透出，覆盖一块居中的冰块毛玻璃场景卡片。
 * 卡片淡入 → 用户点"进入" → 跳 Home。
 */
export default function FirstMeet({ nickname, onContinue }: Props) {
  const [visible, setVisible] = useState(false);

  const today = new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 120);
    return () => clearTimeout(t);
  }, []);

  return (
    <section className="screen fm-screen">
      <div className={`fm-card ${visible ? "fm-card--in" : ""}`}>

        {/* 日期戳 */}
        <span className="fm-date">{today}</span>

        {/* 装饰线 + 初遇标题 */}
        <div className="fm-eyebrow">· 初遇 ·</div>

        {/* 认识第 1 天 */}
        <p className="fm-day-count">认识第 <strong>1</strong> 天</p>

        {/* 场景描写（现实系初识感） */}
        <p className="fm-scene">
          （heal 把手机放到一边，<br />
          抬眼认真看向你）
        </p>

        {/* 台词 */}
        <blockquote className="fm-quote">
          "第一次见面，不用急着把自己讲清楚。<br />
          从今天开始，我慢慢认识你。"
        </blockquote>

        {/* 玩家名字 */}
        <p className="fm-nickname">— {nickname}</p>

        {/* 进入按钮 */}
        <button
          type="button"
          className="welcome-enter-btn fm-btn"
          onClick={onContinue}
        >
          进入
        </button>
      </div>
    </section>
  );
}
