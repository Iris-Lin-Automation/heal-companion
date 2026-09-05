import { useState } from "react";
import type { FormEvent } from "react";

const COMFORTS = [
  {
    id: "hold",
    title: "先听我说完",
    note: "难过时，先接住我的话，不急着分析",
  },
  {
    id: "listen",
    title: "安静待一会儿",
    note: "有时候我只想有人在，不必马上解决",
  },
  {
    id: "help",
    title: "陪我理一下",
    note: "等我缓过来，再给一个现实可行的小步骤",
  },
] as const;

type Props = {
  initialName?: string;
  onDone: (nickname: string, comfort: string) => void;
};

export default function Greet({ initialName = "", onDone }: Props) {
  const [name, setName] = useState(initialName);
  const [comfortId, setComfortId] = useState<(typeof COMFORTS)[number]["id"]>("hold");

  function submit(e: FormEvent) {
    e.preventDefault();
    const nickname = name.trim() || "你";
    const comfort = COMFORTS.find((c) => c.id === comfortId)?.note || COMFORTS[0].note;
    onDone(nickname, comfort);
  }

  return (
    <section className="screen greet-screen">
      <form className="greet-card" onSubmit={submit}>
        <div className="card-eyebrow" aria-hidden>· · ·</div>
        <h1>你好</h1>
        <p className="greet-lead">第一次见面。先告诉我，怎么叫你最自然？</p>

        <label className="field">
          <span>想被这样叫</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：小周、阿月…"
            maxLength={20}
            autoFocus
          />
        </label>

        <div className="comfort-block">
          <p className="field-label">当你有点撑不住时，更希望 heal 怎样回应？</p>
          <div className="comfort-grid">
            {COMFORTS.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`comfort-card ${comfortId === c.id ? "selected" : ""}`}
                onClick={() => setComfortId(c.id)}
              >
                <strong>{c.title}</strong>
                <span>{c.note}</span>
              </button>
            ))}
          </div>
        </div>

        <button type="submit" className="primary-pill">
          好，记住我
        </button>
      </form>
    </section>
  );
}
