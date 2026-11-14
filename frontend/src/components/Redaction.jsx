import { quantiseInlineCh } from "@/lib/quantise";

const CATEGORY = {
  PERSON: "person name",
  STUDENT_ID: "student ID",
  EMAIL_ADDRESS: "email address",
  PHONE_NUMBER: "phone number",
  LOCATION: "location",
};

/** Inline cut-out for a placeholder such as [PERSON]. Width is hash-quantised from tokenId. */
export function Redaction({ tokenId, entity = "REDACTED", focusable = false, variant }) {
  const label = CATEGORY[entity] || "withheld text";
  return (
    <span data-focusable={focusable || undefined} tabIndex={focusable ? 0 : undefined} title={focusable ? `Redacted ${label}` : undefined}>
      <span className="rd" data-variant={variant} style={{ width: `${quantiseInlineCh(tokenId)}ch` }} aria-hidden="true" />
      <span className="sr-only">[redacted {label}]</span>
    </span>
  );
}

const PH = /(\[(?:PERSON|STUDENT_ID|EMAIL_ADDRESS|PHONE_NUMBER|LOCATION|REDACTED)\])/g;

/** Splits plain text and swaps placeholders for cut-outs. */
export function RedactedText({ text, idPrefix = "t" }) {
  return String(text)
    .split(PH)
    .map((part, i) => {
      const m = /^\[([A-Z_]+)\]$/.exec(part);
      return m ? <Redaction key={i} tokenId={`${idPrefix}-${i}`} entity={m[1]} /> : part;
    });
}
