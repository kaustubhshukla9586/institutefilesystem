import { useRef, useState } from "react";
import { RedactedText } from "@/components/Redaction";
import { Button, Card, ErrorNote, Input, Label, LevelBadge, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const LEVELS_FOR = { faculty: ["public", "faculty"], admin: ["public", "faculty", "admin"] };
const cap = (l) => l[0].toUpperCase() + l.slice(1);

function SuggestionPanel({ sug }) {
  const note = "This is a suggestion from a model trained on our sample documents; you decide the level.";
  if (sug.state === "loading")
    return (
      <div className="rounded-[2px] border border-line bg-ink-0 p-3 text-sm text-dim" role="status">
        Reading the file to suggest a level…
      </div>
    );
  if (sug.state === "error")
    return (
      <div className="rounded-[2px] border border-line bg-ink-0 p-3 text-sm text-dim" role="status" data-testid="suggest-panel">
        {sug.unavailable ? "Level suggestion is unavailable right now." : `No suggestion: ${sug.message}`} Choose the level yourself.
      </div>
    );
  const d = sug.data;
  const pct = Math.round(d.probabilities[d.suggested_level] * 100);
  return (
    <div className="rounded-[2px] border border-line bg-ink-0 p-3" role="status" data-testid="suggest-panel">
      <p className="text-sm text-text">
        Suggested level: <strong>{cap(d.suggested_level)}</strong> ({pct}% sure)
      </p>
      {!d.confident && (
        <p className="mt-1 text-sm text-text">Not sure, defaulted to the more restrictive level; please check.</p>
      )}
      {!d.allowed && (
        <p className="mt-1 text-sm text-text">
          That is above your own level, so {cap(d.capped_level)} is selected. Ask an administrator if it needs a higher level.
        </p>
      )}
      <div className="mt-2 grid gap-1">
        {Object.entries(d.probabilities).map(([l, p]) => (
          <div key={l} className="flex items-center gap-2 text-xs text-dim">
            <span className="w-14">{cap(l)}</span>
            <div className="h-1 flex-1 rounded-[2px] bg-ink-3">
              <div className="h-1 rounded-[2px] bg-bone" style={{ width: `${Math.round(p * 100)}%` }} />
            </div>
            <span className="w-9 text-right font-mono">{Math.round(p * 100)}%</span>
          </div>
        ))}
      </div>
      {d.top_terms?.length > 0 && <p className="mt-2 text-xs text-dim">Why? {d.top_terms.join(", ")}</p>}
      <p className="mt-2 text-xs text-dim">{note}</p>
    </div>
  );
}

export default function Upload() {
  const { session } = useAuth();
  const levels = LEVELS_FOR[session.role] || [];
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [level, setLevel] = useState(levels.at(-1));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);
  const [sug, setSug] = useState(null); // { state: "loading" | "ok" | "error", data?, message? }
  const pickSeq = useRef(0);

  async function pick(f) {
    setFile(f);
    setRes(null);
    if (!f) return setSug(null);
    const seq = ++pickSeq.current;
    setSug({ state: "loading" });
    const form = new FormData();
    form.append("file", f);
    try {
      const data = await api("/documents/suggest-level", { method: "POST", form });
      if (seq !== pickSeq.current) return;
      setSug({ state: "ok", data });
      setLevel(data.allowed ? data.suggested_level : data.capped_level);
    } catch (ex) {
      if (seq !== pickSeq.current) return;
      setSug({ state: "error", unavailable: ex.status === 503, message: ex.message });
    }
  }

  async function submit(e) {
    e.preventDefault();
    if (!file) return setErr("Choose a .txt, .md or .pdf file first.");
    setErr("");
    setRes(null);
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    form.append("access_level", level);
    form.append("title", title);
    if (sug?.state === "ok") form.append("suggested_level", sug.data.suggested_level);
    try {
      setRes(await api("/documents/upload", { method: "POST", form }));
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="font-display text-3xl font-bold">Upload a document</h1>
      <p className="mt-1 text-sm text-dim">
        The file is redacted, split into chunks and indexed with the access level you choose. You can't tag above your own level.
      </p>
      <Card className="mt-6">
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <Label htmlFor="up-file">File (.txt, .md or .pdf, up to 2 MB)</Label>
            <input
              id="up-file"
              type="file"
              accept=".txt,.md,.pdf"
              onChange={(e) => pick(e.target.files?.[0] || null)}
              className="block min-h-10 w-full text-sm text-text file:mr-3 file:min-h-10 file:cursor-pointer file:rounded-[2px] file:border-0 file:bg-ink-3 file:px-4 file:text-bone"
            />
          </div>
          {sug && (
            <div className="md:col-span-2">
              <SuggestionPanel sug={sug} />
            </div>
          )}
          <div>
            <Label htmlFor="up-title">Title (optional)</Label>
            <Input id="up-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Defaults to the file name" />
          </div>
          <div>
            <Label htmlFor="up-level">Access level</Label>
            <Select id="up-level" className="w-full" value={level} onChange={(e) => setLevel(e.target.value)}>
              {levels.map((l) => (
                <option key={l} value={l}>
                  {l[0].toUpperCase() + l.slice(1)}
                </option>
              ))}
            </Select>
          </div>
          <div className="md:col-span-2">
            <ErrorNote>{err}</ErrorNote>
          </div>
          <div className="md:col-span-2">
            <Button type="submit" disabled={busy}>
              {busy ? "Redacting and indexing…" : "Upload and index"}
            </Button>
          </div>
        </form>
      </Card>

      {res && (
        <Card className="fade-in mt-6" role="status">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold">{res.title}</h2>
            <LevelBadge level={res.access_level} />
            <span className="font-mono text-xs text-dim">
              {res.doc_id} · {res.chunks} chunks
            </span>
          </div>
          <p className="mt-2 text-sm text-text">
            Redacted:{" "}
            {Object.entries(res.entities_redacted)
              .map(([k, v]) => `${v} ${k}`)
              .join(", ") || "nothing found"}
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs text-dim">Before</p>
              <p className="mt-1 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-[2px] bg-ink-0 p-3 text-xs leading-relaxed">{res.before}</p>
            </div>
            <div>
              <p className="text-xs text-dim">After (what is stored)</p>
              <p className="mt-1 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-[2px] bg-ink-0 p-3 text-xs leading-relaxed">
                <RedactedText text={res.after} idPrefix={`up-${res.doc_id}`} />
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
