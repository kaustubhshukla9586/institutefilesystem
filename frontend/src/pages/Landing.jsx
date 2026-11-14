import { useState } from "react";
import { Link } from "react-router";
import { Redaction } from "@/components/Redaction";
import { buttonClass } from "@/components/ui";
import { cn } from "@/lib/utils";

const LEVELS = [
  { id: "public", label: "Public" },
  { id: "faculty", label: "Faculty" },
  { id: "admin", label: "Admin" },
];

/** The same faculty-only sentence, as each clearance would get it. */
function Preview({ level }) {
  if (level === "public") {
    return (
      <p className="text-text">
        <span className="font-mono text-xs uppercase tracking-wide text-dim">Answer · refused</span>
        <br />
        I can't find anything you're cleared to see about that. If you think you need access, ask an administrator.
      </p>
    );
  }
  return (
    <p className="text-text">
      <span className="font-mono text-xs uppercase tracking-wide text-dim">Source · CS probation list · faculty</span>
      <br />
      On 12 March 2025 the committee placed <Redaction tokenId="hero-a" entity="PERSON" /> (
      <Redaction tokenId="hero-b" entity="STUDENT_ID" />) on academic probation and asked for a counselling plan by 1 May.
      {level === "admin" && (
        <span className="mt-2 block text-sm text-dim">
          Admins can open the original document. Opening it is written to the audit log.
        </span>
      )}
    </p>
  );
}

const STEPS = [
  {
    n: "01",
    t: "Redact",
    d: "Names, student IDs, emails, phone numbers and places are replaced before anything is indexed or sent to the AI model. Dates stay, because questions need them. The original is kept only for audited admin viewing.",
  },
  {
    n: "02",
    t: "Filter",
    d: "Your role comes from your signed token and is checked against the database. The search only looks at documents at or below your level.",
  },
  { n: "03", t: "Audit", d: "Every question, the sources used, and whether it was answered or refused is logged for administrators." },
];

export default function Landing() {
  const [level, setLevel] = useState("faculty");
  return (
    <div className="min-h-dvh">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link to="/" className="font-display text-lg font-extrabold tracking-tight text-bone" style={{ fontStretch: "75%" }}>
          THORNWICK<span className="text-amber">/</span>ARCHIVE
        </Link>
        <Link to="/login" className={buttonClass({ variant: "outline", size: "sm" })}>
          Sign in
        </Link>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-6xl gap-10 px-4 pb-16 pt-10 md:grid-cols-[1.2fr_1fr] md:pt-20">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-amber">Privacy-aware document assistant</p>
            <h1
              className="mt-4 font-display text-[clamp(40px,7vw,88px)] font-extrabold leading-[0.95] tracking-tight"
              style={{ fontStretch: "70%" }}
            >
              Ask the archive. <span className="text-dim">See only</span> what you're cleared for.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-text">
              Answers about Thornwick University policies, minutes and reports, written by an AI model from documents
              you're allowed to read, with the sources cited under every answer.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login" className={buttonClass({ size: "lg" })}>
                Sign in to ask
              </Link>
              <Link to="/signup" className={buttonClass({ variant: "outline", size: "lg" })}>
                Create a student account
              </Link>
            </div>
          </div>

          <div className="self-center rounded-[2px] border border-line bg-ink-1 p-5">
            <p id="clr-label" className="text-xs text-dim">
              Same question, different clearance (illustration)
            </p>
            <div role="radiogroup" aria-labelledby="clr-label" className="mt-2 grid grid-cols-3 gap-1 rounded-[2px] bg-ink-0 p-1">
              {LEVELS.map((l) => (
                <button
                  key={l.id}
                  role="radio"
                  aria-checked={level === l.id}
                  onClick={() => setLevel(l.id)}
                  className={cn(
                    "min-h-10 cursor-pointer rounded-[2px] text-sm transition-colors duration-150",
                    level === l.id ? "bg-amber text-on-amber" : "text-dim hover:text-bone",
                  )}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <p className="mt-4 text-sm text-bone">"Who was put on probation in March?"</p>
            <div className="mt-3 min-h-28 border-t border-line pt-3 text-[15px] leading-relaxed" aria-live="polite">
              <Preview level={level} />
            </div>
          </div>
        </section>

        <section aria-labelledby="how" className="border-t border-line">
          <div className="mx-auto max-w-6xl px-4 py-14">
            <h2 id="how" className="font-display text-2xl font-bold">
              How it keeps data where it belongs
            </h2>
            <ol className="mt-8 grid gap-6 md:grid-cols-3">
              {STEPS.map((s) => (
                <li key={s.n} className="border-t border-line-strong pt-4">
                  <span className="font-mono text-xs text-amber">{s.n}</span>
                  <h3 className="mt-1 text-lg font-semibold">{s.t}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-text">{s.d}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>
      </main>
      <footer className="border-t border-line px-4 py-6 text-center text-xs text-dim">
        All documents and people in this demo are fictional. Thornwick University is not a real institution.
      </footer>
    </div>
  );
}
