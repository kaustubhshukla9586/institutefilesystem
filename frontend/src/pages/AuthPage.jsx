import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { Button, Card, ErrorNote, Input, Label } from "@/components/ui";
import { useAuth } from "@/lib/auth";

const DEMO = [
  ["Student", "student@demo.com"],
  ["Faculty", "faculty@demo.com"],
  ["Admin", "admin@demo.com"],
];

export default function AuthPage({ mode }) {
  const isLogin = mode === "login";
  const { session, login, signup } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  if (session) return <Navigate to={loc.state?.from || "/dashboard"} replace />;

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (!isLogin && password.length < 8) return setErr("Password must be at least 8 characters.");
    setBusy(true);
    try {
      await (isLogin ? login(email, password) : signup(email, password));
      nav(loc.state?.from || "/dashboard", { replace: true });
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main id="main" className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-4 py-10">
      <Link to="/" className="mb-8 font-display text-lg font-extrabold tracking-tight text-bone" style={{ fontStretch: "75%" }}>
        THORNWICK<span className="text-amber">/</span>ARCHIVE
      </Link>
      <Card>
        <h1 className="font-display text-2xl font-bold">{isLogin ? "Sign in" : "Create a student account"}</h1>
        <p className="mt-1 text-sm text-dim">
          {isLogin
            ? "Use your university email."
            : "Self sign-up creates student accounts only. Faculty and admin access is granted by the university."}
        </p>
        <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              required
              minLength={isLogin ? undefined : 8}
              aria-describedby={isLogin ? undefined : "pw-hint"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {!isLogin && (
              <p id="pw-hint" className="mt-1 text-xs text-dim">
                At least 8 characters.
              </p>
            )}
          </div>
          <ErrorNote>{err}</ErrorNote>
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
          </Button>
        </form>
        <p className="mt-4 text-sm text-dim">
          {isLogin ? (
            <>
              New here?{" "}
              <Link to="/signup" className="text-amber underline">
                Create a student account
              </Link>
            </>
          ) : (
            <>
              Already registered?{" "}
              <Link to="/login" className="text-amber underline">
                Sign in
              </Link>
            </>
          )}
        </p>
      </Card>
      {isLogin && (
        <Card className="mt-4 p-4">
          <p className="text-xs font-medium text-bone">Demo accounts (password: demo1234)</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {DEMO.map(([r, e]) => (
              <button
                key={e}
                type="button"
                onClick={() => {
                  setEmail(e);
                  setPassword("demo1234");
                }}
                className="min-h-10 cursor-pointer rounded-[2px] border border-line px-3 text-xs text-text hover:border-amber"
              >
                {r} · <span className="font-mono">{e}</span>
              </button>
            ))}
          </div>
        </Card>
      )}
    </main>
  );
}
