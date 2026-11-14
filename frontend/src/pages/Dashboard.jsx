import { useEffect, useState } from "react";
import { Link } from "react-router";
import { RedactedText } from "@/components/Redaction";
import { buttonClass, Card, ErrorNote, LevelBadge, Stat } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn, fmtTime, ROLE_LABEL } from "@/lib/utils";

function useData(path) {
  const [state, set] = useState({ data: null, error: "" });
  useEffect(() => {
    let live = true;
    api(path).then(
      (data) => live && set({ data, error: "" }),
      (e) => live && set({ data: null, error: e.message }),
    );
    return () => {
      live = false;
    };
  }, [path]);
  return state;
}

const ResultTag = ({ r }) => (
  <span className={cn("font-mono text-[11px] uppercase", r === "refused" ? "text-amber" : r === "error" ? "text-alarm" : "text-dim")}>{r}</span>
);

function Levels({ per }) {
  return (
    <Card>
      <h2 className="text-sm font-semibold">Documents you can search</h2>
      <ul className="mt-3 space-y-2">
        {Object.entries(per || {}).map(([lvl, n]) => (
          <li key={lvl} className="flex items-center justify-between">
            <LevelBadge level={lvl} />
            <span className="font-mono text-sm text-bone tabular-nums">{n}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function AdminDash() {
  const { data, error } = useData("/stats");
  if (error) return <ErrorNote>{error}</ErrorNote>;
  return (
    <>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Queries today" value={data?.queries_today} />
        <Stat label="Refusals today" value={data?.refusals_today} />
        <Stat label="Original-document views" value={data?.reveals_total} hint="all time, audited" />
        <Stat label="Users" value={data ? Object.values(data.users_per_role).reduce((a, b) => a + b, 0) : null} />
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-[1fr_2fr]">
        <Levels per={data?.documents_per_level} />
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Latest audit entries</h2>
            <Link to="/admin/audit" className="text-xs text-amber underline">
              Open audit log
            </Link>
          </div>
          <ul className="mt-3 divide-y divide-line">
            {(data?.latest_audit || []).map((r) => (
              <li key={r.id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 py-2 text-sm">
                <ResultTag r={r.event === "query" ? r.result : r.event} />
                <span className="min-w-[8rem] flex-1 truncate text-text">
                  <RedactedText text={r.question} idPrefix={`la${r.id}`} />
                </span>
                <span className="text-xs text-dim">
                  {r.user_email} · {fmtTime(r.timestamp)}
                </span>
              </li>
            ))}
            {data && data.latest_audit.length === 0 && <li className="py-2 text-sm text-dim">No activity yet.</li>}
          </ul>
        </Card>
      </div>
    </>
  );
}

function UserDash({ role }) {
  const { data, error } = useData("/my-stats");
  if (error) return <ErrorNote>{error}</ErrorNote>;
  return (
    <>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <Stat label="Your questions today" value={data?.queries_today} />
        <Stat label="Your questions, all time" value={data?.queries_total} />
        <Stat label="Refused" value={data?.refusals_total} hint="nothing within your clearance" />
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-[1fr_2fr]">
        <Levels per={data?.documents_per_level} />
        <Card>
          <h2 className="text-sm font-semibold">Your recent questions</h2>
          <ul className="mt-3 divide-y divide-line">
            {(data?.recent_questions || []).map((r, i) => (
              <li key={i} className="flex items-baseline gap-3 py-2 text-sm">
                <ResultTag r={r.result} />
                <span className="min-w-0 flex-1 truncate text-text">{r.question}</span>
                <span className="text-xs text-dim">{fmtTime(r.timestamp)}</span>
              </li>
            ))}
            {data && data.recent_questions.length === 0 && <li className="py-2 text-sm text-dim">You haven't asked anything yet.</li>}
          </ul>
        </Card>
      </div>
      {role === "faculty" && (
        <Card className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-text">Add a document for students or colleagues. Personal details are redacted before it's indexed.</p>
          <Link to="/upload" className={buttonClass({ variant: "outline" })}>
            Upload a document
          </Link>
        </Card>
      )}
    </>
  );
}

const INTRO = {
  student: "You can search public university documents.",
  faculty: "You can search public and faculty documents, and upload documents up to faculty level.",
  admin: "You can search every document, review the audit log and open originals (each view is logged).",
};

export default function Dashboard() {
  const { session } = useAuth();
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-amber">{ROLE_LABEL[session.role]} dashboard</p>
          <h1 className="mt-1 font-display text-3xl font-bold">Welcome back</h1>
          <p className="mt-1 text-sm text-dim">{INTRO[session.role]}</p>
        </div>
        <Link to="/chat" className={buttonClass()}>
          Ask a question
        </Link>
      </div>
      {session.role === "admin" ? <AdminDash /> : <UserDash role={session.role} />}
    </div>
  );
}
