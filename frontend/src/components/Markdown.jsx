import { Children } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { RedactedText } from "./Redaction";

// react-markdown never renders raw HTML here (no rehype-raw, skipHtml on), so answers can't inject markup.
const deco = (children) =>
  Children.map(children, (c, i) => (typeof c === "string" ? <RedactedText text={c} idPrefix={`md${i}`} /> : c));

export default function Markdown({ text }) {
  return (
    <div className="md text-[15px] leading-relaxed text-text">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          p: ({ children }) => <p>{deco(children)}</p>,
          li: ({ children }) => <li>{deco(children)}</li>,
          td: ({ children }) => <td>{deco(children)}</td>,
          table: ({ children }) => (
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable table">
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
