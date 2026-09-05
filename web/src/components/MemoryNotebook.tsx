/**
 * 共享记忆条目类型（由此文件导出）
 */
export type MemoryItem = {
  id: string;
  kind: string;
  summary: string;
  details?: string;
  people?: string[];
  importance: number;
};

const KIND_LABEL: Record<string, string> = {
  identity:        "关于你",
  preference:      "你喜欢的方式",
  person:          "身边的人",
  event:           "一起经历的事",
  commitment:      "想去做的事",
  emotion_pattern: "心里的感受",
  win:             "你做到的事",
  boundary:        "想被小心对待的地方",
};

type Props = {
  /** true = 抽屉滑出，false = 收回 */
  open: boolean;
  memories: MemoryItem[];
};

/**
 * Layer 2 — 右侧抽屉式记忆面板
 *
 * 使用 .char-drawer / .char-drawer.open 的 CSS transition 实现 width 动画滑入。
 * 按 importance 降序排列记忆条目。
 */
export default function MemoryNotebook({ open, memories }: Props) {
  const sorted = memories.slice().sort((a, b) => b.importance - a.importance);

  return (
    <aside className={`char-drawer ${open ? "open" : ""}`}>
      <div className="notebook">
        <h2>heal 记得的事</h2>
        <p className="notebook-lead">
          你说过的现实、偏好和边界，会在这里慢慢留下来。
        </p>

        {sorted.length === 0 ? (
          <p className="notebook-empty">
            还空着。等你愿意说，我会记得有用的部分。
          </p>
        ) : (
          <ul className="notebook-list">
            {sorted.map((m) => (
              <li key={m.id}>
                <span className="chip">
                  {KIND_LABEL[m.kind] ?? "记得的事"}
                </span>
                <strong>{m.summary}</strong>
                {m.people && m.people.length > 0 && (
                  <em>{m.people.join("、")}</em>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
