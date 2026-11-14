import { defineConfig } from "@playwright/test";

// Expects the backend on :8000 and `npm run build && npx vite preview --port 5173` running.
export default defineConfig({
  testDir: "e2e",
  timeout: 120_000,
  workers: 1,
  reporter: "list",
  use: { baseURL: "http://localhost:5173", viewport: { width: 1440, height: 900 } },
});
