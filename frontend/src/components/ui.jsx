// shadcn/ui-style primitives (cva + tailwind-merge), adapted to the Lacuna tokens.
import { cva } from "class-variance-authority";
import { Globe, Lock, Shield } from "lucide-react";
import { cn, LEVEL_LABEL } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-[2px] px-4 text-sm font-medium transition-colors duration-150 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-amber text-on-amber hover:bg-[#ffc04d]",
        outline: "border border-line-strong text-bone hover:bg-ink-2",
        ghost: "text-text hover:bg-ink-2 hover:text-bone",
      },
      size: { md: "", sm: "px-3 text-xs", lg: "min-h-12 px-6 text-base" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export const Button = ({ className, variant, size, ...p }) => <button className={cn(buttonVariants({ variant, size }), className)} {...p} />;
export const buttonClass = (o = {}) => buttonVariants(o);

export const Input = ({ className, ...p }) => (
  <input
    className={cn(
      "min-h-10 w-full rounded-[2px] border border-line bg-ink-1 px-3 text-sm text-bone placeholder:text-dim focus-visible:border-amber",
      className,
    )}
    {...p}
  />
);

export const Select = ({ className, children, ...p }) => (
  <select className={cn("min-h-10 rounded-[2px] border border-line bg-ink-1 px-3 text-sm text-bone", className)} {...p}>
    {children}
  </select>
);

export const Label = ({ className, ...p }) => <label className={cn("mb-1 block text-xs font-medium text-dim", className)} {...p} />;

export const Card = ({ className, ...p }) => <div className={cn("rounded-[2px] border border-line bg-ink-1 p-5", className)} {...p} />;

const LEVEL_ICON = { public: Globe, faculty: Shield, admin: Lock };
const LEVEL_STYLE = {
  public: "border-line-strong text-text",
  faculty: "border-[#a86e12] text-[#e39a1a]",
  admin: "border-amber bg-amber text-on-amber",
};

export function LevelBadge({ level }) {
  const Icon = LEVEL_ICON[level] || Globe;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-[2px] border px-1.5 py-0.5 font-mono text-[11px] uppercase tracking-wide",
        LEVEL_STYLE[level],
      )}
    >
      <Icon size={11} aria-hidden="true" />
      {LEVEL_LABEL[level] || level}
    </span>
  );
}

export function Stat({ label, value, hint }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-dim">{label}</p>
      <p className="mt-1 font-display text-3xl font-bold tabular-nums text-bone">{value ?? "–"}</p>
      {hint && <p className="mt-1 text-xs text-dim">{hint}</p>}
    </Card>
  );
}

export function ErrorNote({ children }) {
  if (!children) return null;
  return (
    <p role="alert" className="rounded-[2px] border border-alarm/60 bg-alarm/10 px-3 py-2 text-sm text-[#ffb3b5]">
      {children}
    </p>
  );
}
