import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";
import "./index.css";
import { AuthProvider } from "./lib/auth";
import Landing from "./pages/Landing";

// Everything behind login is split out so the landing page ships only what it needs.
const Shell = lazy(() => import("./components/Shell"));
const AuthPage = lazy(() => import("./pages/AuthPage"));
const Chat = lazy(() => import("./pages/Chat"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Audit = lazy(() => import("./pages/Audit"));
const Documents = lazy(() => import("./pages/Documents"));
const Upload = lazy(() => import("./pages/Upload"));

const wait = <div className="p-8 text-sm text-dim">Loading…</div>;
const S = (el) => <Suspense fallback={wait}>{el}</Suspense>;

const router = createBrowserRouter([
  { path: "/", element: <Landing /> },
  { path: "/login", element: S(<AuthPage mode="login" />) },
  { path: "/signup", element: S(<AuthPage mode="signup" />) },
  {
    element: S(<Shell />),
    children: [
      { path: "/dashboard", element: S(<Dashboard />) },
      { path: "/chat", element: S(<Chat />) },
      { path: "/admin/audit", element: S(<Audit />), handle: { roles: ["admin"] } },
      { path: "/admin/documents", element: S(<Documents />), handle: { roles: ["admin"] } },
      { path: "/upload", element: S(<Upload />), handle: { roles: ["faculty", "admin"] } },
    ],
  },
  { path: "*", element: <Landing /> },
]);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
);
