import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, clearSession, getSession, setSession } from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [session, setS] = useState(getSession);
  useEffect(() => {
    const out = () => setS(null);
    window.addEventListener("tw-logout", out);
    return () => window.removeEventListener("tw-logout", out);
  }, []);
  const login = useCallback(async (email, password) => {
    const tok = await api("/auth/login", { method: "POST", body: { email, password } });
    setS(setSession(tok));
  }, []);
  const signup = useCallback(async (email, password) => {
    const tok = await api("/auth/signup", { method: "POST", body: { email, password } });
    setS(setSession(tok));
  }, []);
  const logout = useCallback(() => {
    clearSession();
    setS(null);
  }, []);
  return <AuthCtx.Provider value={{ session, login, signup, logout }}>{children}</AuthCtx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthCtx);
