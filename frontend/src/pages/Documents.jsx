import { Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { RedactedText } from "@/components/Redaction";
import { Card, ErrorNote, Input, LevelBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [filter, setFilter] = useState("");
  const [sel, setSel] = useState(null);
  const [view, setView] = useState("redacted");
  const [doc, setDoc] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/documents").then(setDocs, (e) => setErr(e.message));
  }, []);
  useEffect(() => {
    if (!sel) return;
    setDoc(null);
    api(`/documents/${sel}?view=${view}`).then(setDoc, (e) => setErr(e.message));
  }, [sel, view]);

  const shown = docs.filter((d) => (d.doc_id + d.title).toLowerCase().includes(filter.toLowerCase()));

  return (
    <div>
      <h1 className="font-display text-3xl font-bold">Documents</h1>
      <p className="mt-1 text-sm text-dim">
        Compare what is stored (redacted) with the original. Opening an original is recorded in the audit log.
      </p>
      <div className="mt-4">
        <ErrorNote>{err}</ErrorNote>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-[320px_1fr]">
        <Card className="p-3">
          <label htmlFor="doc-filter" className="sr-only">
            Filter documents
          </label>
          <Input id="doc-filter" placeholder="Filter by title or ID" value={filter} onChange={(e) => setFilter(e.target.value)} />
          <ul className="mt-3 max-h-[60vh] overflow-y-auto">
            {shown.map((d) => (
              <li key={d.doc_id}>
                <button
                  onClick={() => {
                    setSel(d.doc_id);
                    setView("redacted");
                  }}
                  aria-current={sel === d.doc_id}
                  className={cn(
                    "flex min-h-10 w-full cursor-pointer items-center justify-between gap-2 rounded-[2px] px-2 py-1.5 text-left text-sm transition-colors",
                    sel === d.doc_id ? "bg-ink-2 text-bone" : "text-text hover:bg-ink-2",
                  )}
                >
                  <span className="min-w-0">
                    <span className="block truncate">{d.title}</span>
                    <span className="font-mono text-[11px] text-dim">
                      {d.doc_id} · {d.chunks} chunks
                    </span>
                  </span>
                  <LevelBadge level={d.access_level} />
                </button>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          {!sel && <p className="text-sm text-dim">Pick a document to view it.</p>}
          {sel && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{doc?.title || "Loading…"}</h2>
                  {doc && (
                    <p className="mt-1 text-xs text-dim">
                      {Object.entries(doc.placeholders)
                        .map(([k, v]) => `${v} ${k}`)
                        .join(" · ") || "No placeholders"}
                    </p>
                  )}
                </div>
                <div role="radiogroup" aria-label="Document view" className="flex gap-1 rounded-[2px] bg-ink-0 p-1">
                  {[
                    ["redacted", "As stored", EyeOff],
                    ["raw", "Original (logged)", Eye],
                  ].map(([v, label, Icon]) => (
                    <button
                      key={v}
                      role="radio"
                      aria-checked={view === v}
                      onClick={() => setView(v)}
                      className={cn(
                        "inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-[2px] px-3 text-sm transition-colors",
                        view === v ? "bg-amber text-on-amber" : "text-dim hover:text-bone",
                      )}
                    >
                      <Icon size={14} aria-hidden="true" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              {view === "raw" && (
                <p className="mt-3 rounded-[2px] border border-amber/50 bg-amber/10 px-3 py-2 text-xs text-amber" role="status">
                  You are viewing the original. This view has been written to the audit log.
                </p>
              )}
              <div className="mt-4 max-h-[60vh] overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-text">
                {doc ? view === "redacted" ? <RedactedText text={doc.text} idPrefix={`doc-${sel}`} /> : doc.text : <div className="skeleton h-40" />}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
