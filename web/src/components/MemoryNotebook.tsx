import { useState } from "react";
import { apiFetch } from "../lib/api";

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
  identity: "关于你",
  preference: "你喜欢的方式",
  person: "身边的人",
  event: "一起经历的事",
  commitment: "想去做的事",
  emotion_pattern: "心里的感受",
  win: "你做到的事",
  boundary: "想被小心对待的地方",
};

type Props = {
  open: boolean;
  memories: MemoryItem[];
  onChanged?: () => void;
};

/**
 * 右侧记忆抽屉：可查看、修改、删除——共同经历由用户自己经营。
 */
export default function MemoryNotebook({ open, memories, onChanged }: Props) {
  const sorted = memories.slice().sort((a, b) => b.importance - a.importance);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  function startEdit(m: MemoryItem) {
    setEditingId(m.id);
    setDraft(m.summary);
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft("");
  }

  async function saveEdit(id: string) {
    const summary = draft.trim();
    if (!summary || busyId) return;
    setBusyId(id);
    try {
      const res = await apiFetch(`/api/memories/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary }),
      });
      if (!res.ok) throw new Error("patch failed");
      cancelEdit();
      onChanged?.();
    } catch {
      /* keep draft for retry */
    } finally {
      setBusyId(null);
    }
  }

  async function remove(id: string) {
    if (busyId) return;
    if (!window.confirm("删掉这条记忆？之后对话里就不会再提起。")) return;
    setBusyId(id);
    try {
      const res = await apiFetch(`/api/memories/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("delete failed");
      if (editingId === id) cancelEdit();
      onChanged?.();
    } catch {
      /* ignore */
    } finally {
      setBusyId(null);
    }
  }

  return (
    <aside className={`char-drawer ${open ? "open" : ""}`}>
      <div className="notebook">
        <h2>你们一起记得的事</h2>
        <p className="notebook-lead">
          共同经历会留在这里。可以查看、改写或删除——这段关系由你经营。
        </p>

        {sorted.length === 0 ? (
          <p className="notebook-empty">
            还空着。等你愿意说，有用的部分会慢慢留下来。
          </p>
        ) : (
          <ul className="notebook-list">
            {sorted.map((m) => (
              <li key={m.id} className="notebook-item">
                <span className="chip">{KIND_LABEL[m.kind] ?? "记得的事"}</span>
                {editingId === m.id ? (
                  <div className="notebook-edit">
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      rows={3}
                      maxLength={200}
                      disabled={busyId === m.id}
                    />
                    <div className="notebook-edit-actions">
                      <button
                        type="button"
                        className="notebook-btn notebook-btn--primary"
                        disabled={busyId === m.id || !draft.trim()}
                        onClick={() => void saveEdit(m.id)}
                      >
                        保存
                      </button>
                      <button
                        type="button"
                        className="notebook-btn"
                        disabled={busyId === m.id}
                        onClick={cancelEdit}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <strong>{m.summary}</strong>
                    {m.people && m.people.length > 0 && (
                      <em>{m.people.join("、")}</em>
                    )}
                    <div className="notebook-edit-actions">
                      <button
                        type="button"
                        className="notebook-btn"
                        disabled={busyId === m.id}
                        onClick={() => startEdit(m)}
                      >
                        改
                      </button>
                      <button
                        type="button"
                        className="notebook-btn notebook-btn--danger"
                        disabled={busyId === m.id}
                        onClick={() => void remove(m.id)}
                      >
                        删
                      </button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
