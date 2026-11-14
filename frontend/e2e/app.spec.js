// End-to-end checks against the real backend + screenshots for the report (../screenshots).
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const SHOTS = path.resolve(import.meta.dirname, "..", "..", "screenshots");
fs.mkdirSync(SHOTS, { recursive: true });
const shot = (page, name) => page.screenshot({ path: path.join(SHOTS, `${name}.png`) });

const ALLOWED_Q = "What is the late fee for paying tuition between August 16 and September 4?";
const RESTRICTED_Q = "What is the total departmental budget sanctioned for 2025-26?";
const consoleErrors = [];
const axeSerious = {};

test.beforeEach(({ page }) => {
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(`${page.url()}: ${m.text()}`));
  page.on("pageerror", (e) => consoleErrors.push(`${page.url()}: ${e.message}`));
});

async function axe(page, label) {
  const r = await new AxeBuilder({ page }).analyze();
  const bad = r.violations.filter((v) => ["serious", "critical"].includes(v.impact));
  axeSerious[label] = bad.map((v) => `${v.id} (${v.nodes.length})`);
}

async function login(page, email) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("demo1234");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL("**/dashboard");
}

async function ask(page, q) {
  await page.getByLabel("Your question").fill(q);
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.locator("[aria-busy=true]")).toHaveCount(0, { timeout: 90_000 });
}

test("landing", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Ask the archive");
  await page.getByRole("radio", { name: "Public" }).click();
  await expect(page.getByText("Answer · refused")).toBeVisible();
  await page.getByRole("radio", { name: "Faculty" }).click();
  await axe(page, "landing");
  await shot(page, "00-landing");
});

test("login page and student-only sign-up", async ({ page }) => {
  await page.goto("/login");
  await axe(page, "login");
  await shot(page, "01-login");
  await page.getByLabel("Email").fill("student@demo.com");
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Wrong email or password");
  await page.goto("/signup");
  await expect(page.getByText("Self sign-up creates student accounts only")).toBeVisible();
  await axe(page, "signup");
});

test("student: dashboard, citations, refusal, 403", async ({ page }) => {
  await login(page, "student@demo.com");
  await expect(page.getByText("Student dashboard")).toBeVisible();
  await expect(page.getByRole("link", { name: "Audit log" })).toHaveCount(0);
  await page.getByRole("link", { name: "Ask", exact: true }).click();
  await ask(page, ALLOWED_Q);
  await expect(page.getByText(/1 source|\d sources/)).toBeVisible();
  await expect(page.getByText("PUB008")).toBeVisible();
  await axe(page, "chat");
  await shot(page, "03-student-chat-citations");
  await ask(page, RESTRICTED_Q);
  await expect(page.getByText("Nothing you're cleared to see")).toBeVisible();
  await page.locator("main").getByText("Nothing you're cleared to see").scrollIntoViewIfNeeded();
  await shot(page, "04-student-refusal");
  await page.goto("/dashboard");
  await expect(page.getByText("Your questions, all time")).toBeVisible();
  await page.waitForTimeout(400);
  await axe(page, "student-dashboard");
  await shot(page, "02-student-dashboard");
  await page.goto("/admin/audit");
  await expect(page.getByText("You're not cleared for this page")).toBeVisible();
  await shot(page, "13-student-403");
});

test("faculty dashboard", async ({ page }) => {
  await login(page, "faculty@demo.com");
  await expect(page.getByText("Faculty dashboard")).toBeVisible();
  await expect(page.getByRole("link", { name: "Upload a document" })).toBeVisible();
  await page.waitForTimeout(400);
  await shot(page, "06-faculty-dashboard");
});

test("admin: answer, dashboard, audit, redacted view, upload", async ({ page }) => {
  await login(page, "admin@demo.com");
  await page.getByRole("link", { name: "Ask", exact: true }).click();
  await ask(page, RESTRICTED_Q);
  await expect(page.getByText("ADM004")).toBeVisible();
  await shot(page, "05-admin-same-question-answered");

  await page.goto("/dashboard");
  await expect(page.getByText("Admin dashboard")).toBeVisible();
  await expect(page.getByText("Latest audit entries")).toBeVisible();
  await page.waitForTimeout(400);
  await axe(page, "admin-dashboard");
  await shot(page, "07-admin-dashboard");

  await page.goto("/admin/audit");
  await expect(page.getByText(/\d+ entr/)).toBeVisible();
  await axe(page, "audit");
  await shot(page, "08-audit-log");
  await page.getByLabel("Result").selectOption("refused");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.locator("tbody td:last-child").first()).toHaveText(/refused/i);
  await shot(page, "09-audit-log-refused");

  await page.goto("/admin/documents");
  await page.getByRole("button", { name: /Research Committee Meeting/ }).click();
  await expect(page.getByText(/STUDENT_ID/).first()).toBeVisible();
  await axe(page, "documents");
  await shot(page, "10-redacted-view");
  await page.getByRole("radio", { name: "Original (logged)" }).click();
  await expect(page.getByText("This view has been written to the audit log")).toBeVisible();
  await shot(page, "10b-original-view-logged");

  await page.goto("/upload");
  await page.getByLabel(/File/).setInputFiles({
    name: "lab-safety-note.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Chemistry Lab Safety Note, effective 1 December 2026. Report spills to Dr. Meera Iyer (meera.iyer@thornwick.example, +91 98123 45678). Goggles are mandatory in Lab 2B.",
    ),
  });
  await page.getByLabel("Title (optional)").fill("Chemistry lab safety note");
  await page.getByLabel("Access level").selectOption("faculty");
  await page.getByRole("button", { name: "Upload and index" }).click();
  await expect(page.getByText("After (what is stored)")).toBeVisible({ timeout: 60_000 });
  await axe(page, "upload");
  await shot(page, "11-upload-with-access-tag");
});

test("mobile chat at 375px", async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 375, height: 812 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await login(page, "student@demo.com");
  await page.goto("/chat");
  await ask(page, ALLOWED_Q);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
  await shot(page, "12-mobile-chat-375");
  await ctx.close();
});

test.afterAll(() => {
  fs.writeFileSync(path.join(SHOTS, "_checks.json"), JSON.stringify({ consoleErrors, axeSerious }, null, 2));
  console.log("CONSOLE ERRORS:", consoleErrors.length ? consoleErrors : "none");
  console.log("AXE serious/critical:", JSON.stringify(axeSerious));
});
