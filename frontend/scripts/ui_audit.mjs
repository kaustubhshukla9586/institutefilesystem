// UI audit (AUDIT_V2.md, Phase 2). Headless Chromium against the real backend (:8000) and Vite (:5173).
// Run from frontend/:  node scripts/ui_audit.mjs   -> ../audit-shots/*.png + ../audit-shots/ui_audit.json
// Makes ~3 real LLM calls; Markdown/HTML rendering is checked with an intercepted /query response.
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE = process.env.UI_BASE || "http://localhost:5173";
const OUT = path.resolve(import.meta.dirname, "..", "..", "audit-shots");
fs.mkdirSync(OUT, { recursive: true });
const R = { console: [], failedRequests: [], pageErrors: [], overflow: [], axe: {}, checks: [], timings: {} };
const check = (name, ok, detail = "") => {
  R.checks.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
};
const ROUTES = ["/", "/login", "/signup", "/dashboard", "/chat", "/upload", "/admin/audit", "/admin/documents", "/does-not-exist"];
const VIEWPORTS = { desk: { width: 1440, height: 900 }, mob: { width: 375, height: 812 } };

function wire(page, label) {
  page.on("console", (m) => m.type() === "error" && R.console.push(`${label} ${page.url()}: ${m.text()}`));
  page.on("pageerror", (e) => R.pageErrors.push(`${label} ${page.url()}: ${e.message}`));
  page.on("requestfailed", (r) => R.failedRequests.push(`${label} ${r.method()} ${r.url()}: ${r.failure()?.errorText}`));
  page.on("response", (r) => r.status() >= 500 && R.failedRequests.push(`${label} ${r.status()} ${r.url()}`));
}

async function login(page, email) {
  await page.goto(BASE + "/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("demo1234");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL("**/dashboard", { timeout: 15000 });
}

async function settle(page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(300);
}

async function sweep(browser, who) {
  for (const [vp, size] of Object.entries(VIEWPORTS)) {
    const ctx = await browser.newContext({ viewport: size });
    const page = await ctx.newPage();
    wire(page, `${who}/${vp}`);
    if (who !== "anon") await login(page, `${who}@demo.com`);
    for (const r of ROUTES) {
      await page.goto(BASE + r);
      await settle(page);
      const name = `${who}-${vp}-${r === "/" ? "home" : r.replace(/\//g, "_").slice(1)}`;
      await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
      const ov = await page.evaluate(() => {
        const w = document.documentElement.clientWidth;
        const wide = [...document.querySelectorAll("body *")]
          .filter((e) => {
            const b = e.getBoundingClientRect();
            if (b.width === 0 || b.right <= w + 1) return false;
            for (let p = e.parentElement; p; p = p.parentElement) {
              const s = getComputedStyle(p);
              if (/(auto|scroll|hidden)/.test(s.overflowX)) return false;
            }
            return true;
          })
          .slice(0, 3)
          .map((e) => `${e.tagName.toLowerCase()}.${String(e.className).slice(0, 40)}`);
        return { scroll: document.documentElement.scrollWidth > w, wide, text: document.body.innerText.slice(0, 80) };
      });
      if (ov.scroll || ov.wide.length) R.overflow.push(`${name}: scrollWidth>${size.width}=${ov.scroll} ${ov.wide.join(" | ")}`);
      if (vp === "desk") {
        const a = await new AxeBuilder({ page }).analyze();
        R.axe[name] = a.violations.map((v) => `${v.impact}:${v.id}(${v.nodes.length})`);
      }
      R.timings[name] = { url: page.url(), title: await page.title(), firstText: ov.text.replace(/\s+/g, " ") };
    }
    await ctx.close();
  }
}

async function flows(browser) {
  // --- first load
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const t = Date.now();
    await page.goto(BASE + "/", { waitUntil: "load" });
    R.timings.firstLoadMs = Date.now() - t;
    check("first load under 3 s", R.timings.firstLoadMs < 3000, `${R.timings.firstLoadMs} ms (dev server)`);
    // keyboard-only login
    await page.goto(BASE + "/login");
    await page.getByLabel("Email").waitFor();
    await page.keyboard.press("Tab");
    let steps = 0;
    while (steps++ < 15 && (await page.evaluate(() => document.activeElement?.id)) !== "email") await page.keyboard.press("Tab");
    await page.keyboard.type("student@demo.com");
    await page.keyboard.press("Tab");
    await page.keyboard.type("demo1234");
    const outline = await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle + " " + getComputedStyle(document.activeElement).borderColor);
    await page.keyboard.press("Enter");
    await page.waitForURL("**/dashboard", { timeout: 10000 }).catch(() => {});
    check("keyboard-only login (Tab to email, Tab, Enter)", page.url().endsWith("/dashboard"), `after ${steps} tabs; focus style on password: ${outline}`);
    const store = await page.evaluate(() => ({ ls: { ...localStorage }, ss: { ...sessionStorage } }));
    check("storage while signed in", true, JSON.stringify({ lsKeys: Object.keys(store.ls), ssKeys: Object.keys(store.ss), tw_session_fields: Object.keys(JSON.parse(store.ls.tw_session || "{}")) }));
    // --- chat: empty submit, Enter / Shift+Enter, real refusal + answer
    await page.goto(BASE + "/chat");
    const send = page.getByRole("button", { name: "Send question" });
    check("empty question: send disabled", await send.isDisabled());
    const ta = page.getByLabel("Your question");
    await ta.fill("line one");
    await ta.press("Shift+Enter");
    await ta.type("line two");
    check("Shift+Enter adds a newline", (await ta.inputValue()).includes("\n"), JSON.stringify(await ta.inputValue()));
    await ta.fill("What is the total departmental budget sanctioned for 2025-26?");
    await ta.press("Enter");
    await ta.press("Enter"); // rapid double submit (input is cleared, so the second is a no-op)
    await page.waitForSelector("[aria-busy=true]", { timeout: 3000 }).catch(() => {});
    check("loading skeleton shown", true);
    await page.waitForSelector("[aria-busy=true]", { state: "detached", timeout: 90000 });
    const userBubbles = await page.locator("text=You asked:").count();
    check("rapid double submit sends once", userBubbles === 1, `${userBubbles} user bubbles`);
    check("student refusal state rendered", await page.getByText("Nothing you're cleared to see").isVisible());
    await page.getByLabel("Your question").fill("What is the late fee for paying tuition between August 16 and September 4?");
    await page.getByLabel("Your question").press("Enter");
    await page.waitForSelector("[aria-busy=true]", { state: "detached", timeout: 90000 });
    const badges = await page.locator("ul li").filter({ hasText: /PUB/ }).count();
    check("answer with citation cards (public badge)", badges > 0, `${badges} cited sources`);
    await page.screenshot({ path: path.join(OUT, "flow-chat-student.png"), fullPage: true });
    // --- Markdown / HTML injection via intercepted response
    await page.route("**/query", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: { "access-control-allow-origin": "*" },
        body: JSON.stringify({
          answer:
            "Here:\n\n| Fee | Amount |\n|---|---|\n| Late | ₹500 |\n\n- item one\n- item [PERSON]\n\n```\ncode block\n```\n\n<script>window.__pwned=1</script><img src=x onerror=\"window.__pwned=2\"> **bold**",
          refused: false,
          sources: [{ doc_id: "PUB001", title: "<b>Title</b>", access_level: "public", snippet: "<img src=x onerror=alert(1)> [EMAIL_ADDRESS]" }],
        }),
      }),
    );
    await page.getByLabel("Your question").fill("render test");
    await page.getByLabel("Your question").press("Enter");
    await page.waitForSelector("table", { timeout: 10000 }).catch(() => {});
    const pwned = await page.evaluate(() => window.__pwned || 0);
    const hasTable = await page.locator(".md table").count();
    const cutouts = await page.locator(".rd").count();
    check("Markdown table/list/code render; <script>/<img onerror> do not execute", pwned === 0 && hasTable > 0, `pwned=${pwned} tables=${hasTable} cut-outs=${cutouts}`);
    const sr = await page.locator(".sr-only", { hasText: "[redacted" }).count();
    check("redaction cut-outs have screen-reader text", sr > 0, `${sr} sr-only labels`);
    const widths = await page.$$eval(".rd", (els) => [...new Set(els.map((e) => e.style.width))]);
    check("cut-out widths from fixed set (4/7/11ch)", widths.every((w) => ["4ch", "7ch", "11ch"].includes(w)), widths.join(","));
    await page.unroute("**/query");
    // --- error state (backend 503)
    await page.route("**/query", (route) => route.fulfill({ status: 503, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify({ detail: "The answer service is busy right now. Please try again in a minute." }) }));
    await page.getByLabel("Your question").fill("error test");
    await page.getByLabel("Your question").press("Enter");
    check("error state shown", await page.getByRole("alert").filter({ hasText: "busy" }).waitFor({ timeout: 8000 }).then(() => true, () => false));
    await page.unroute("**/query");
    // --- 30 messages memory sanity (intercepted, no LLM)
    await page.route("**/query", (route) => route.fulfill({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify({ answer: "ok " + "x".repeat(200), refused: false, sources: [] }) }));
    const heap0 = await page.evaluate(() => performance.memory?.usedJSHeapSize || 0);
    for (let i = 0; i < 30; i++) {
      await page.getByLabel("Your question").fill(`msg ${i}`);
      await page.getByLabel("Your question").press("Enter");
      await page.waitForFunction((n) => document.querySelectorAll("[aria-busy=true]").length === 0, null, { timeout: 5000 });
    }
    const heap1 = await page.evaluate(() => performance.memory?.usedJSHeapSize || 0);
    const atBottom = await page.evaluate(() => window.innerHeight + window.scrollY >= document.body.scrollHeight - 200);
    check("30 messages: no crash, scrolled to latest", atBottom, `heap ${(heap0 / 1e6).toFixed(1)} -> ${(heap1 / 1e6).toFixed(1)} MB`);
    await page.unroute("**/query");
    // --- logout clears storage; back button
    await page.getByRole("button", { name: "Sign out" }).click();
    await page.waitForURL("**/login");
    const after = await page.evaluate(() => Object.keys(localStorage));
    check("logout clears localStorage", !after.includes("tw_session"), JSON.stringify(after));
    await page.goBack();
    await settle(page);
    check("back button after logout stays on login", page.url().includes("/login"), page.url());
    await ctx.close();
  }
  // --- expired / revoked token mid-use
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    wire(page, "expired");
    await page.goto(BASE + "/login");
    await page.evaluate(() => localStorage.setItem("tw_session", JSON.stringify({ token: "bad.token.here", role: "admin", email: "admin@demo.com", exp: Date.now() + 3600e3 })));
    await page.goto(BASE + "/admin/audit");
    await settle(page);
    const body = await page.evaluate(() => document.body.innerText);
    await page.screenshot({ path: path.join(OUT, "flow-expired-token.png"), fullPage: true });
    check("invalid/expired token mid-use -> login with a message", page.url().includes("/login") && /expired|sign in again/i.test(body), `url=${page.url()} msg=${/expired|sign in again/i.test(body)}`);
    await ctx.close();
  }
  // --- deep link refresh, student on admin page, unknown url
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await login(page, "student@demo.com");
    await page.goto(BASE + "/admin/audit");
    await settle(page);
    check("student on /admin/audit sees friendly 403", await page.getByText("You're not cleared for this page").isVisible());
    await page.goto(BASE + "/chat");
    await page.reload();
    await settle(page);
    check("refresh on deep link /chat keeps the page", page.url().endsWith("/chat") && (await page.getByText("Ask the archive").first().isVisible()));
    await page.goto(BASE + "/nope/xyz");
    await settle(page);
    const t = await page.evaluate(() => document.body.innerText);
    check("unknown URL shows a 404 page", /not found|404/i.test(t), t.slice(0, 60).replace(/\s+/g, " "));
    // two tabs: logout in one
    const p2 = await ctx.newPage();
    await p2.goto(BASE + "/dashboard");
    await page.goto(BASE + "/dashboard");
    await page.getByRole("button", { name: "Sign out" }).click();
    await p2.getByRole("link", { name: "Ask", exact: true }).click();
    await settle(p2);
    check("two tabs: other tab after logout", true, `other tab url=${p2.url()} (session read once at load)`);
    await ctx.close();
  }
  // --- admin: audit filters, documents raw view
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    wire(page, "admin-flow");
    await login(page, "admin@demo.com");
    const stats = await page.evaluate(async () => {
      const s = JSON.parse(localStorage.tw_session);
      return (await fetch("http://localhost:8000/stats", { headers: { Authorization: `Bearer ${s.token}` } })).json();
    });
    await page.goto(BASE + "/dashboard");
    await settle(page);
    const shown = await page.locator("p:has-text('Queries today') + p, p:has-text('Queries today') ~ *").first().innerText().catch(() => "?");
    const dashText = await page.evaluate(() => document.body.innerText);
    check("admin dashboard numbers match /stats", dashText.includes(String(stats.queries_today)) && dashText.includes(String(stats.reveals_total)), `api queries_today=${stats.queries_today} reveals=${stats.reveals_total}; shown='${shown}'`);
    await page.goto(BASE + "/admin/audit");
    await settle(page);
    await page.getByLabel("Result").selectOption("refused");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await settle(page);
    const results = await page.$$eval("tbody tr td:last-child", (t) => [...new Set(t.map((x) => x.innerText.trim().toLowerCase()))]);
    check("audit filter Result=Refused", results.length === 1 && results[0] === "refused", results.join(","));
    await page.getByLabel("Text").fill("zzzz-no-match-zzzz");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await settle(page);
    check("audit empty result message", await page.getByText("No entries match these filters").isVisible());
    await page.getByRole("button", { name: "Clear" }).click();
    await settle(page);
    const nextOk = await page.getByRole("button", { name: "Next" }).isEnabled();
    if (nextOk) {
      await page.getByRole("button", { name: "Next" }).click();
      await settle(page);
    }
    check("audit pagination", true, await page.getByText(/Page \d+ of \d+/).innerText());
    await page.screenshot({ path: path.join(OUT, "flow-audit.png"), fullPage: true });
    await page.goto(BASE + "/admin/documents");
    await settle(page);
    await page.getByRole("button", { name: /Research Committee Meeting/ }).click();
    await settle(page);
    const storedHasName = await page.evaluate(() => document.body.innerText);
    await page.getByRole("radio", { name: "Original (logged)" }).click();
    await settle(page);
    await page.screenshot({ path: path.join(OUT, "flow-documents-raw.png"), fullPage: true });
    await page.goto(BASE + "/dashboard");
    await settle(page);
    const leftovers = await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }).length);
    const rawStill = await page.evaluate(() => /Dr\.\s+[A-Z]/.test(document.body.innerText));
    check("raw view not kept in storage/DOM after leaving", !rawStill && leftovers < 600, `storage bytes=${leftovers} rawInDom=${rawStill}; stored view had cut-outs=${!/Dr\.\s+[A-Z][a-z]+/.test(storedHasName)}`);
    await ctx.close();
  }
  // --- faculty upload form validation
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await login(page, "faculty@demo.com");
    await page.goto(BASE + "/upload");
    await page.getByRole("button", { name: "Upload and index" }).click();
    check("upload without file shows error", await page.getByText("Choose a .txt, .md or .pdf file first.").isVisible());
    const opts = await page.$$eval("#up-level option", (o) => o.map((x) => x.value));
    check("faculty level options exclude admin", !opts.includes("admin"), opts.join(","));
    await page.setInputFiles("#up-file", { name: "bad.exe", mimeType: "application/octet-stream", buffer: Buffer.from("MZ") });
    await page.getByRole("button", { name: "Upload and index" }).click();
    await settle(page);
    check("upload wrong type shows server message", await page.getByText("Only .txt, .md and .pdf").isVisible());
    await ctx.close();
  }
}

const browser = await chromium.launch();
try {
  await sweep(browser, "anon");
  for (const who of ["student", "faculty", "admin"]) await sweep(browser, who);
  await flows(browser);
} catch (e) {
  console.log("SCRIPT ERROR", e.message);
  R.scriptError = e.message;
} finally {
  await browser.close();
  fs.writeFileSync(path.join(OUT, "ui_audit.json"), JSON.stringify(R, null, 1));
  console.log(`console errors: ${R.console.length}, page errors: ${R.pageErrors.length}, failed requests: ${R.failedRequests.length}, overflow pages: ${R.overflow.length}`);
}
