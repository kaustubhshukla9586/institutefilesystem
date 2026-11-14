import { useCallback, useEffect, useState } from "react";
import { RedactedText } from "@/components/Redaction";
import { Button, Card, ErrorNote, Input, Label, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { cn, fmtTime } from "@/lib/utils";

const EMPTY = { role: "", user: "", q: "", result: "", event: "", from: "", to: "" };

export default function Audit() {
  const [f, setF] = useState(EMPTY);
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(null);

  const load = useCallback(async () => {
    const qs = new URLSearchParams({ page: String(page), page_size: "20" });
    Object.entries(applied).forEach(([k, v]) => v && qs.set(k, v));
    try {
      setData(await api(`/audit-log?${qs}`));
      setErr("");
    } catch (e) {
      setErr(e.message);
    }
  }, [applied, page]);
  useEffect(() => {
    load();
  }, [load]);

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <div>
      <h1 className="font-display text-3xl font-bold">Audit log</h1>
      <p className="mt-1 text-sm text-dim">Every question, original-document view and upload. Visible to administrators only.</p>

      <Card className="mt-6">
        <form
          className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-7"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setApplied(f);
          }}
        >
          <div>
            <Label htmlFor="f-role">Role</Label>
            <Select id="f-role" className="w-full" value={f.role} onChange={set("role")}>
              <option value="">Any</option>
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
              <option value="admin">Admin</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="f-result">Result</Label>
            <Select id="f-result" className="w-full" value={f.result} onChange={set("result")}>
              <option value="">Any</option>
              <option value="answered">Answered</option>
              <option value="refused">Refused</option>
              <option value="error">Error</option>
              <option value="ok">OK (reveal/upload)</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="f-event">Event</Label>
            <Select id="f-event" className="w-full" value={f.event} onChange={set("event")}>
              <option value="">Any</option>
              <option value="query">Query</option>
              <option value="reveal">Reveal</option>
              <option value="upload">Upload</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="f-user">User email</Label>
            <Input id="f-user" value={f.user} onChange={set("user")} placeholder="contains…" />
          </div>
          <div>
            <Label htmlFor="f-q">Text</Label>
            <Input id="f-q" value={f.q} onChange={set("q")} placeholder="question or answer" />
          </div>
          <div>
            <Label htmlFor="f-from">From</Label>
            <Input id="f-from" type="date" value={f.from} onChange={set("from")} />
          </div>
          <div>
            <Label htmlFor="f-to">To</Label>
            <Input id="f-to" type="date" value={f.to} onChange={set("to")} />
          </div>
          <div className="col-span-2 flex gap-2 md:col-span-4 lg:col-span-7">
            <Button type="submit">Apply filters</Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setF(EMPTY);
                setApplied(EMPTY);
                setPage(1);
              }}
            >
              Clear
            </Button>
          </div>
        </form>
      </Card>

      <div className="mt-4">
        <ErrorNote>{err}</ErrorNote>
      </div>
      {data && (
        <>
          <p className="mt-4 text-sm text-dim" aria-live="polite">
            {data.total} {data.total === 1 ? "entry" : "entries"}
          </p>
          <div className="mt-2 overflow-x-auto rounded-[2px] border border-line" tabIndex={0} role="region" aria-label="Audit entries">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-ink-1 text-xs text-dim">
                <tr>
                  <th className="px-3 py-2 font-medium">Time</th>
                  <th className="px-3 py-2 font-medium">User</th>
                  <th className="px-3 py-2 font-medium">Role</th>
                  <th className="px-3 py-2 font-medium">Event</th>
                  <th className="px-3 py-2 font-medium">Question / action</th>
                  <th className="px-3 py-2 font-medium">Sources</th>
                  <th className="px-3 py-2 font-medium">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.items.map((r) => (
                  <tr key={r.id} className="align-top">
                    <td className="whitespace-nowrap px-3 py-2 text-xs text-dim">{fmtTime(r.timestamp)}</td>
                    <td className="px-3 py-2 text-xs">{r.user_email}</td>
                    <td className="px-3 py-2 text-xs capitalize">{r.user_role}</td>
                    <td className="px-3 py-2 font-mono text-[11px] uppercase text-dim">{r.event}</td>
                    <td className="px-3 py-2">
                      <button
                        className="cursor-pointer text-left text-text hover:text-bone"
                        aria-expanded={open === r.id}
                        onClick={() => setOpen(open === r.id ? null : r.id)}
                      >
                        {r.question}
                      </button>
                      {open === r.id && r.answer && (
                        <p className="mt-2 whitespace-pre-wrap border-l-2 border-line-strong pl-3 text-xs text-dim">
                          <RedactedText text={r.answer} idPrefix={`aud${r.id}`} />
                        </p>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-dim">{r.sources.join(", ") || "—"}</td>
                    <td className={cn("px-3 py-2 font-mono text-[11px] uppercase", r.result === "refused" ? "text-amber" : r.result === "error" ? "text-alarm" : "text-text")}>
                      {r.result}
                    </td>
                  </tr>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-dim">
                      No entries match these filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </Button>
            <span className="text-xs text-dim">
              Page {data.page} of {data.pages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
