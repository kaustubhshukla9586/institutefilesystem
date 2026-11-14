// Thin client for the FastAPI backend. No mocks: every call goes to the real API.
const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const KEY = "tw_session";

export function getSession() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || "null");
    if (s && s.exp > Date.now()) return s;
  } catch {
    /* storage unavailable */
  }
  return null;
}

export function setSession(tok) {
  const s = { token: tok.access_token, role: tok.role, email: tok.email, exp: Date.now() + (tok.expires_in || 3600) * 1000 };
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    /* ignore */
  }
  return s;
}

export function clearSession() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function detailText(d) {
  if (!d) return null;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    const first = d[0];
    if (first?.loc?.includes("password")) return "Password must be at least 8 characters.";
    if (first?.loc?.includes("email")) return "Enter a valid email address.";
    return first?.msg || "Please check the form.";
  }
  return null;
}

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const s = getSession();
  if (s) headers.Authorization = `Bearer ${s.token}`;
  if (body) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: form || (body ? JSON.stringify(body) : undefined) });
  } catch {
    throw new ApiError(0, "Can't reach the server. Is the backend running?");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && s) {
      clearSession();
      window.dispatchEvent(new Event("tw-logout"));
    }
    throw new ApiError(res.status, detailText(data?.detail) || `Request failed (${res.status}).`);
  }
  return data;
}
