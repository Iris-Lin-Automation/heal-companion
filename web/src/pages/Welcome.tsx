type Props = {
  onEnter: () => void;
  /** 重置 session → 重新走 Greet 引导流程 */
  onReset: () => void;
  isReturning: boolean;
  hasApiKey?: boolean;
  onOpenApiKey?: () => void;
};

/**
 * 入场页 — 极简沉浸，绝不让文字压角色的脸。
 * 参照 1v1 陪伴竞品：大立绘 + 底部短文案 + 一个主按钮。
 */
export default function Welcome({
  onEnter,
  onReset,
  isReturning,
  hasApiKey,
  onOpenApiKey,
}: Props) {
  return (
    <section className="screen welcome-screen">
      <div className="welcome-imm">
        <p className="welcome-sub">下班后，有个人在</p>
        <h1 className="welcome-title">heal</h1>
        <button type="button" className="welcome-enter-btn" onClick={onEnter}>
          进入
        </button>
        {onOpenApiKey && (
          <button type="button" className="welcome-key-btn" onClick={onOpenApiKey}>
            {hasApiKey ? "已保存 DeepSeek Key · 点击更换" : "免费玩：填入你的 DeepSeek Key"}
          </button>
        )}
        {isReturning && (
          <button type="button" className="welcome-reset-btn" onClick={onReset}>
            重新认识
          </button>
        )}
      </div>
    </section>
  );
}
