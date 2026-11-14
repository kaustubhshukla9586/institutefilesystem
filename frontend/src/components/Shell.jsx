import { LayoutDashboard, LogOut, MessageSquare, ScrollText, FileText, Upload, ShieldOff } from "lucide-react";
import { Link, Navigate, NavLink, Outlet, useLocation, useMatches } from "react-router";
import { useAuth } from "@/lib/auth";
import { cn, ROLE_LABEL } from "@/lib/utils";
import { buttonClass, LevelBadge } from "./ui";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/chat", label: "Ask", icon: MessageSquare },
  { to: "/upload", label: "Upload", icon: Upload, roles: ["faculty", "admin"] },
  { to: "/admin/audit", label: "Audit log", icon: ScrollText, roles: ["admin"] },
  { to: "/admin/documents", label: "Documents", icon: FileText, roles: ["admin"] },
];
const LEVEL_OF = { student: "public", faculty: "faculty", admin: "admin" };

export function Wordmark() {
  return (
    <Link to="/" className="font-display text-lg font-extrabold tracking-tight text-bone" style={{ fontStretch: "75%" }}>
      THORNWICK<span className="text-amber">/</span>ARCHIVE
    </Link>
  );
}

function Forbidden() {
  return (
    <div className="mx-auto max-w-md py-20 text-center">
      <ShieldOff className="mx-auto text-amber" size={32} aria-hidden="true" />
      <h1 className="mt-4 font-display text-2xl font-bold">You're not cleared for this page</h1>
      <p className="mt-2 text-sm text-dim">Your role doesn't include access here. If you think it should, ask an administrator.</p>
      <Link to="/dashboard" className={cn(buttonClass({ variant: "outline" }), "mt-6")}>
        Back to your dashboard
      </Link>
    </div>
  );
}

export default function Shell() {
  const { session, logout } = useAuth();
  const loc = useLocation();
  const matches = useMatches();
  if (!session) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  // UI guard only; the backend enforces every permission on its own.
  const need = matches.at(-1)?.handle?.roles;
  const allowed = !need || need.includes(session.role);
  const nav = NAV.filter((n) => !n.roles || n.roles.includes(session.role));
  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:bg-amber focus:px-3 focus:py-2 focus:text-on-amber">
        Skip to content
      </a>
      <header className="sticky top-0 z-10 border-b border-line bg-ink-0/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-2">
          <Wordmark />
          <nav aria-label="Main" className="ml-2 flex flex-1 gap-1 overflow-x-auto">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded-[2px] px-3 text-sm transition-colors",
                    isActive ? "bg-ink-2 text-bone" : "text-dim hover:text-bone",
                  )
                }
              >
                <Icon size={16} aria-hidden="true" />
                <span className="hidden sm:inline">{label}</span>
                <span className="sr-only sm:hidden">{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="hidden items-center gap-2 md:flex">
            <span className="text-xs text-dim">{session.email}</span>
            <LevelBadge level={LEVEL_OF[session.role]} />
          </div>
          <button onClick={logout} className={buttonClass({ variant: "ghost", size: "sm" })} aria-label="Sign out">
            <LogOut size={16} aria-hidden="true" />
          </button>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-6xl px-4 py-6">
        <p className="sr-only">Signed in as {ROLE_LABEL[session.role]}</p>
        {allowed ? <Outlet /> : <Forbidden />}
      </main>
    </div>
  );
}
