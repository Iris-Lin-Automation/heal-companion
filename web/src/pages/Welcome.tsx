type Props = {
  onEnter: () => void;
  /** 重置 session → 重新走 Greet 引导流程 */
  onReset: () => void;
  isReturning: boolean;
};

/**
 * 入场页 — 极简沉浸，绝不让文字压角色的脸。
 * 只保留 1 行副标题 + 角色名 + 进入按钮，其余留白。
 * 回访用户在底部显示「重新认识」链接。
 */
export default function Welcome({ onEnter, onReset, isReturning }: Props) {
  return (
    <section className="screen welcome-screen">
      <div className="welcome-imm">
        <p className="welcome-sub">下班后，有个人在</p>
        <h1 className="welcome-title">heal</h1>
        <button type="button" className="welcome-enter-btn" onClick={onEnter}>
          进入
        </button>
        {isReturning && (
          <button type="button" className="welcome-reset-btn" onClick={onReset}>
            重新认识
          </button>
        )}
      </div>
    </section>
  );
}
