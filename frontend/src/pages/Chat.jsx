import { AlertTriangle, ArrowUp, Lock } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import Markdown from "@/components/Markdown";
import { RedactedText } from "@/components/Redaction";
import { Button, LevelBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const EXAMPLES = {
  student: [
    "What is the late fee for paying tuition between August 16 and September 4?",
    "How long may a guest stay in the IT computer labs per session?",
    "What minimum cumulative GPA is required to be eligible for a scholarship?",
  ],
  faculty: [
    "How many students fell below the 75% attendance threshold in the attendance shortfall report?",
    "What did the Faculty Senate decide about the academic calendar at its March 2025 meeting?",
    "When does the fall semester of the 2025-26 academic year start and end?",
  ],
  admin: [
    "What is the total departmental budget sanctioned for 2025-26?",
    "What salary increase is proposed for tenure-track faculty in 2025?",
    "How many students fell below the 75% attendance threshold in the attendance shortfall report?",
  ],
};

function Sources({ sources, msgId }) {
  return (
    <div className="mt-4 border-t border-line pt-3">
      <p className="text-xs text-dim">
        {sources.length} {sources.length === 1 ? "source" : "sources"}
      </p>
      <ul className="mt-2 grid gap-2 sm:grid-cols-2">
        {sources.map((s) => (
          <li key={s.doc_id} className="rounded-[2px] border border-line bg-ink-0 p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-bone">{s.title}</p>
              <LevelBadge level={s.access_level} />
            </div>
            <p className="mt-1 font-mono text-[11px] text-dim">{s.doc_id}</p>
            <p className="mt-2 text-xs leading-relaxed text-text">
              <RedactedText text={s.snippet} idPrefix={`${msgId}-${s.doc_id}`} />
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Message({ m }) {
  if (m.role === "user") {
    return (
      <div className="fade-in ml-auto max-w-[85%] rounded-[2px] bg-ink-2 px-4 py-3 text-bone">
        <span className="sr-only">You asked: </span>
        {m.text}
      </div>
    );
  }
  if (m.pending) {
    return (
      <div className="space-y-2 rounded-[2px] border border-line bg-ink-1 p-4" aria-busy="true" aria-label="Writing an answer">
        <div className="skeleton h-3 w-3/4" />
        <div className="skeleton h-3 w-2/3" />
        <div className="skeleton h-3 w-1/2" />
      </div>
    );
  }
  if (m.error) {
    return (
      <div role="alert" className="fade-in flex gap-3 rounded-[2px] border border-alarm/60 bg-alarm/10 p-4 text-sm text-[#ffb3b5]">
        <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
        <p>{m.error}</p>
      </div>
    );
  }
  if (m.refused) {
    return (
      <div className="fade-in flex gap-3 rounded-[2px] border border-line-strong bg-ink-1 p-4">
        <Lock size={18} className="mt-0.5 shrink-0 text-amber" aria-hidden="true" />
        <div>
          <p className="text-sm font-medium text-bone">Nothing you're cleared to see</p>
          <p className="mt-1 text-sm text-text">{m.text}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="fade-in rounded-[2px] border border-line bg-ink-1 p-4">
      <Markdown text={m.text} />
      {m.sources?.length > 0 && <Sources sources={m.sources} msgId={m.id} />}
    </div>
  );
}

export default function Chat() {
  const { session } = useAuth();
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // braces matter: newer Chromium returns a Promise from scrollIntoView, which must not be the effect's return value
    endRef.current?.scrollIntoView({ block: "end" });
  }, [msgs]);

  async function ask(text) {
    const question = text.trim();
    if (!question || busy) return;
    const id = Date.now();
    setQ("");
    setBusy(true);
    setMsgs((m) => [...m, { id: `u${id}`, role: "user", text: question }, { id: `a${id}`, role: "assistant", pending: true }]);
    let reply;
    try {
      const r = await api("/query", { method: "POST", body: { question } });
      reply = { id: `a${id}`, role: "assistant", text: r.answer, refused: r.refused, sources: r.sources };
    } catch (e) {
      reply = { id: `a${id}`, role: "assistant", error: e.message };
    }
    setMsgs((m) => m.map((x) => (x.id === `a${id}` ? reply : x)));
    setBusy(false);
    inputRef.current?.focus();
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <h1 className="font-display text-2xl font-bold">Ask the archive</h1>
      <p className="mt-1 text-sm text-dim">Answers use only documents your role can read. Personal details stay redacted.</p>

      <div className="mt-6 space-y-4" aria-live="polite">
        {msgs.length === 0 && (
          <div className="rounded-[2px] border border-dashed border-line p-5">
            <p className="text-sm text-bone">Try one of these:</p>
            <ul className="mt-3 space-y-2">
              {(EXAMPLES[session.role] || EXAMPLES.student).map((e) => (
                <li key={e}>
                  <button
                    onClick={() => ask(e)}
                    className="min-h-10 w-full cursor-pointer rounded-[2px] border border-line px-3 py-2 text-left text-sm text-text transition-colors hover:border-amber hover:text-bone"
                  >
                    {e}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {msgs.map((m) => (
          <Message key={m.id} m={m} />
        ))}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(q);
        }}
        className="sticky bottom-0 mt-6 flex gap-2 border-t border-line bg-ink-0 py-4"
      >
        <label htmlFor="q" className="sr-only">
          Your question
        </label>
        <textarea
          id="q"
          ref={inputRef}
          rows={1}
          value={q}
          maxLength={1000}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask(q);
            }
          }}
          placeholder="Ask about a policy, meeting or report…"
          className="min-h-12 flex-1 resize-none rounded-[2px] border border-line bg-ink-1 px-3 py-3 text-sm text-bone placeholder:text-dim focus-visible:border-amber"
        />
        <Button type="submit" disabled={busy || !q.trim()} className="min-h-12 w-12 px-0" aria-label="Send question">
          <ArrowUp size={18} aria-hidden="true" />
        </Button>
      </form>
    </div>
  );
}
