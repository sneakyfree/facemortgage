/**
 * FaceMortgage exhaustive UI v2: uncapped buttons, modal recursion,
 * multi-step flow walk, search box interactions, presentation
 * screenshots, viewport variants. Output: /tmp/fm-crawl-v2.json
 * + /tmp/fm-screenshots/*.png
 */
import { test, expect, Page, APIRequestContext } from "@playwright/test";
import fs from "fs";
import path from "path";

const baseURL = process.env.E2E_BASE_URL || "http://localhost:5849";
const apiBase = process.env.E2E_API_URL || "http://localhost:8821";
const SHOTS_DIR = "/tmp/fm-screenshots";

const PUBLIC_PAGES = [
  "/", "/how-it-works", "/for-professionals", "/faq", "/privacy", "/terms",
  "/get-matched", "/subscribe", "/checkout", "/contact",
  "/auth/login", "/auth/register", "/auth/forgot-password", "/auth/reset-password", "/auth/callback",
  "/embed/widget", "/embed/get-matched", "/partner/dashboard",
];
const AUTHED_PAGES = [
  "/dashboard", "/dashboard/analytics", "/dashboard/billing", "/dashboard/billing/bid",
  "/dashboard/billing/invoices", "/dashboard/calls", "/dashboard/leads", "/dashboard/leads/import",
  "/dashboard/partnerships", "/dashboard/settings", "/dashboard/settings/notifications",
  "/dashboard/settings/privacy", "/dashboard/settings/sms", "/dashboard/settings/nmls",
];
const ADMIN_PAGES = ["/admin", "/admin/agentic-audit", "/admin/audit", "/admin/disputes", "/admin/moderation", "/admin/users"];

interface Probe {
  label: string;
  outcome: string;
  detail?: string;
}
interface PageReport {
  url: string;
  asRole: "anonymous" | "user" | "admin";
  viewport: string;
  loadStatus: "ok" | "fail";
  loadError?: string;
  finalURL: string;
  loadMs: number;
  consoleErrors: string[];
  pageErrors: string[];
  failedRequests: { url: string; status: number; method: string }[];
  inventory: { buttons: number; links: number; forms: number; inputs: number; selects: number; tabs: number; searchBoxes: number; modals: number; images: number; brokenImages: number };
  buttonProbes: Probe[];
  linkProbes: Probe[];
  inputProbes: Probe[];
  selectProbes: Probe[];
  tabProbes: Probe[];
  modalProbes: { trigger: string; opened: boolean; modalButtons?: number; consoleErrorsInside?: number }[];
  searchProbes: { input: string; query: string; outcome: string; resultsAfterMs?: number }[];
  presentationFlags: string[];
  screenshot?: string;
}

const results: PageReport[] = [];

if (!fs.existsSync(SHOTS_DIR)) fs.mkdirSync(SHOTS_DIR, { recursive: true });

async function primeCsrf(request: APIRequestContext): Promise<string> {
  await request.get(`${apiBase}/api/v1/lookups/states`);
  const state = await request.storageState();
  return state.cookies.find(c => c.name === "csrf_token")?.value || "";
}

async function attach(page: Page, report: PageReport) {
  page.on("console", msg => { if (msg.type() === "error") report.consoleErrors.push(msg.text()); });
  page.on("pageerror", err => { report.pageErrors.push(err.message); });
  page.on("response", resp => {
    const status = resp.status();
    if (status >= 400) {
      const u = resp.url();
      if (/_next\/static|favicon|\/__nextjs|hmr|dev_assets|sockjs|webpack/.test(u)) return;
      report.failedRequests.push({ url: u, status, method: resp.request().method() });
    }
  });
}

async function checkImages(page: Page, report: PageReport) {
  const imgs = await page.locator("img").elementHandles();
  report.inventory.images = imgs.length;
  for (const i of imgs) {
    try {
      const ok = await i.evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth > 0);
      if (!ok) report.inventory.brokenImages++;
    } catch {/*ignore*/}
  }
}

async function checkPresentation(page: Page, report: PageReport) {
  // Tab navigation: ensure at least one focusable element
  try {
    const focusableCount = await page.locator("a[href], button, input, select, textarea, [tabindex]").count();
    if (focusableCount === 0) report.presentationFlags.push("no focusable elements");
  } catch {/*ignore*/}
  // Body has content
  const text = (await page.locator("body").textContent({ timeout: 1500 }).catch(() => "")) || "";
  if (text.trim().length < 50) report.presentationFlags.push("body text < 50 chars (blank page?)");
  // Check for layout overflow (horizontal scroll on desktop = bad)
  const overflow = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
  }));
  if (overflow.scrollW > overflow.clientW + 16) {
    report.presentationFlags.push(`horizontal overflow: ${overflow.scrollW}>${overflow.clientW}`);
  }
  // 404 marker
  if (/this page could not be found/i.test(text) && !/i can('|'\\u2019)t/i.test(text)) {
    if (page.url().includes("/404") || (await page.locator("h1, h2").first().textContent().catch(() => ""))?.includes("404")) {
      report.presentationFlags.push("renders 404 content");
    }
  }
}

async function probeLinks(page: Page, report: PageReport) {
  const links = page.locator("a[href]:visible");
  const count = await links.count();
  const seen = new Set<string>();
  for (let i = 0; i < count; i++) {
    const a = links.nth(i);
    let href = (await a.getAttribute("href").catch(() => "")) || "";
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("javascript:")) continue;
    let absolute: string;
    try { absolute = new URL(href, page.url()).toString(); } catch { continue; }
    if (seen.has(absolute)) continue;
    seen.add(absolute);
    if (!absolute.startsWith(baseURL)) { report.linkProbes.push({ label: href.slice(0,60), outcome: "external" }); continue; }
    try {
      const r = await page.request.get(absolute, { failOnStatusCode: false });
      const st = r.status();
      report.linkProbes.push({ label: absolute.replace(baseURL, ""), outcome: st >= 400 ? (st === 404 ? "404" : `${st}`) : "ok", detail: `${st}` });
    } catch { report.linkProbes.push({ label: absolute, outcome: "error" }); }
  }
}

async function probeSelects(page: Page, report: PageReport) {
  const selects = page.locator("select:visible");
  const count = await selects.count();
  for (let i = 0; i < count; i++) {
    const s = selects.nth(i);
    const name = (await s.getAttribute("name").catch(() => null)) || (await s.getAttribute("id").catch(() => null)) || `select[${i}]`;
    const opts = await s.locator("option").all();
    if (opts.length <= 1) { report.selectProbes.push({ label: name, outcome: "no-options", detail: `${opts.length}` }); continue; }
    try {
      const v = (await opts[1].getAttribute("value").catch(() => "")) || "";
      await s.selectOption(v, { timeout: 1500 });
      report.selectProbes.push({ label: name, outcome: "ok" });
    } catch (e: any) {
      report.selectProbes.push({ label: name, outcome: "error", detail: String(e?.message || e).slice(0, 120) });
    }
  }
}

async function probeInputs(page: Page, report: PageReport) {
  const inputs = page.locator("input:visible, textarea:visible");
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const inp = inputs.nth(i);
    const type = (await inp.getAttribute("type").catch(() => "text")) || "text";
    const name = (await inp.getAttribute("name").catch(() => null)) || (await inp.getAttribute("id").catch(() => null)) || `input[${i}]`;
    if (["checkbox", "radio", "file", "hidden", "submit", "button", "image"].includes(type)) {
      report.inputProbes.push({ label: name, outcome: "skipped-non-text", detail: type }); continue;
    }
    let payload = "stress";
    if (type === "email") payload = "stress@example.com";
    else if (type === "password") payload = "Stress12345!";
    else if (type === "number") payload = "123";
    else if (type === "tel") payload = "5555555555";
    else if (type === "url") payload = "https://example.com";
    else if (type === "date") payload = "2026-01-15";
    const errsBefore = report.pageErrors.length;
    try {
      await inp.fill(payload, { timeout: 1500 });
      await page.waitForTimeout(80);
      if (report.pageErrors.length > errsBefore) report.inputProbes.push({ label: name, outcome: "page-error", detail: report.pageErrors[report.pageErrors.length-1].slice(0,120) });
      else report.inputProbes.push({ label: name, outcome: "ok", detail: type });
    } catch (e: any) {
      report.inputProbes.push({ label: name, outcome: "rejected", detail: String(e?.message || e).slice(0, 120) });
    }
  }
}

async function probeSearchBoxes(page: Page, report: PageReport) {
  const searches = page.locator("input[type=search]:visible, input[placeholder*='Search' i]:visible, input[placeholder*='earch' i]:visible, input[name*='search' i]:visible");
  const count = await searches.count();
  for (let i = 0; i < count; i++) {
    const s = searches.nth(i);
    const name = (await s.getAttribute("name").catch(() => null)) || (await s.getAttribute("placeholder").catch(() => null)) || `search[${i}]`;
    const errBefore = report.pageErrors.length + report.consoleErrors.length;
    try {
      await s.fill("test", { timeout: 1500 });
      await page.waitForTimeout(400); // wait for debounce
      const errAfter = report.pageErrors.length + report.consoleErrors.length;
      const outcome = errAfter > errBefore ? "error-during-type" : "ok";
      report.searchProbes.push({ input: name, query: "test", outcome, resultsAfterMs: 400 });
    } catch (e: any) {
      report.searchProbes.push({ input: name, query: "test", outcome: "fill-failed" });
    }
  }
}

async function probeTabs(page: Page, report: PageReport) {
  const tabs = page.getByRole("tab");
  const count = await tabs.count();
  for (let i = 0; i < count; i++) {
    const t = tabs.nth(i);
    const label = ((await t.textContent({ timeout: 500 }).catch(() => ""))?.trim() || `tab[${i}]`).slice(0, 60);
    const errs = report.pageErrors.length + report.consoleErrors.length;
    try {
      await t.click({ timeout: 1500, noWaitAfter: true });
      await page.waitForTimeout(150);
      report.tabProbes.push({ label, outcome: (report.pageErrors.length + report.consoleErrors.length) > errs ? "error" : "ok" });
    } catch (e: any) { report.tabProbes.push({ label, outcome: "click-failed", detail: String(e?.message || e).slice(0, 80) }); }
  }
}

async function isModalOpen(page: Page): Promise<number> {
  const modalSelectors = [
    "[role=dialog]:visible",
    "[role=alertdialog]:visible",
    ".modal:visible",
    "[aria-modal=true]:visible",
  ];
  let total = 0;
  for (const s of modalSelectors) {
    try { total += await page.locator(s).count(); } catch {/*ignore*/}
  }
  return total;
}

async function probeButtons(page: Page, report: PageReport) {
  const btns = page.locator("button:visible");
  const btnCount = await btns.count();
  for (let i = 0; i < btnCount; i++) {
    const b = btns.nth(i);
    let label = `button[${i}]`;
    try { label = (await b.textContent({ timeout: 500 }))?.trim().slice(0, 60) || label; } catch {/*ignore*/}
    if (/log\s*out|sign\s*out|delete\s*account|delete\s*data|delete\s*all|confirm.*delet/i.test(label)) {
      report.buttonProbes.push({ label, outcome: "skipped-destructive" }); continue;
    }
    const errsBefore = report.consoleErrors.length + report.pageErrors.length;
    const urlBefore = page.url();
    const modalsBefore = await isModalOpen(page);
    try {
      await b.click({ timeout: 700, force: false, noWaitAfter: true });
      await page.waitForTimeout(200);
      const errsAfter = report.consoleErrors.length + report.pageErrors.length;
      const modalsAfter = await isModalOpen(page);
      if (modalsAfter > modalsBefore) {
        // Modal opened — count internal buttons
        const modalBtns = await page.locator("[role=dialog]:visible button, [role=alertdialog]:visible button, .modal:visible button, [aria-modal=true]:visible button").count();
        const modalCEs = report.consoleErrors.length - (errsBefore);
        report.modalProbes.push({ trigger: label, opened: true, modalButtons: modalBtns, consoleErrorsInside: modalCEs });
        report.buttonProbes.push({ label, outcome: "opened-modal", detail: `${modalBtns}btns` });
        // Try to close via Escape
        await page.keyboard.press("Escape").catch(() => {});
        await page.waitForTimeout(150);
      } else if (errsAfter > errsBefore) {
        report.buttonProbes.push({ label, outcome: "console-error", detail: report.consoleErrors[report.consoleErrors.length-1]?.slice(0, 100) });
      } else if (page.url() !== urlBefore) {
        report.buttonProbes.push({ label, outcome: "navigated", detail: page.url() });
        await page.goto(urlBefore, { waitUntil: "domcontentloaded", timeout: 5000 }).catch(() => {});
      } else {
        report.buttonProbes.push({ label, outcome: "ok" });
      }
    } catch (e: any) {
      report.buttonProbes.push({ label, outcome: "click-failed", detail: String(e?.message || e).slice(0, 100) });
    }
  }
}

async function probePage(page: Page, urlPath: string, role: "anonymous" | "user" | "admin", viewport: string) {
  const report: PageReport = {
    url: urlPath, asRole: role, viewport, loadStatus: "ok", finalURL: "", loadMs: 0,
    consoleErrors: [], pageErrors: [], failedRequests: [],
    inventory: { buttons: 0, links: 0, forms: 0, inputs: 0, selects: 0, tabs: 0, searchBoxes: 0, modals: 0, images: 0, brokenImages: 0 },
    buttonProbes: [], linkProbes: [], inputProbes: [], selectProbes: [], tabProbes: [],
    modalProbes: [], searchProbes: [], presentationFlags: [],
  };
  await attach(page, report);
  const t0 = Date.now();
  try {
    const resp = await page.goto(baseURL + urlPath, { waitUntil: "domcontentloaded", timeout: 20000 });
    // Dismiss cookie banner if present so it stops eating click probes.
    await page.evaluate(() => {
      try {
        localStorage.setItem("cookie_consent", "all");
        localStorage.setItem("cookie-consent", "all");
      } catch {}
    }).catch(() => {});
    const accept = page.getByRole("button", { name: /Accept All|Reject Non-Essential|Accept Cookies|I Accept/i }).first();
    await accept.click({ timeout: 600 }).catch(() => {});
    report.loadMs = Date.now() - t0;
    if (!resp || resp.status() >= 400) {
      report.loadStatus = "fail";
      report.loadError = `HTTP ${resp?.status()}`;
    }
    await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
    report.finalURL = page.url();
  } catch (e: any) {
    report.loadStatus = "fail";
    report.loadError = String(e?.message || e).slice(0, 200);
    report.finalURL = page.url();
    results.push(report);
    fs.writeFileSync("/tmp/fm-crawl-v2.json", JSON.stringify(results, null, 2));
    return;
  }
  // Inventory
  report.inventory.buttons = await page.locator("button").count();
  report.inventory.links = await page.locator("a[href]").count();
  report.inventory.forms = await page.locator("form").count();
  report.inventory.inputs = await page.locator("input").count();
  report.inventory.selects = await page.locator("select").count();
  report.inventory.tabs = await page.getByRole("tab").count();
  report.inventory.searchBoxes = await page.locator("input[type=search], input[placeholder*='earch' i], input[name*='search' i]").count();
  report.inventory.modals = await isModalOpen(page);

  await checkImages(page, report);
  await checkPresentation(page, report);
  await probeLinks(page, report);
  await probeSelects(page, report);
  await probeInputs(page, report);
  await probeSearchBoxes(page, report);
  await probeTabs(page, report);
  await probeButtons(page, report);

  // Screenshot
  const safe = urlPath.replace(/[/?&=]/g, "_") || "_root";
  const shot = path.join(SHOTS_DIR, `${role}_${viewport}_${safe}.png`);
  try { await page.screenshot({ path: shot, fullPage: false, timeout: 5000 }); report.screenshot = shot; } catch {/*ignore*/}

  results.push(report);
  fs.writeFileSync("/tmp/fm-crawl-v2.json", JSON.stringify(results, null, 2));
}

async function walkGetMatched(page: Page, role: "anonymous" | "user", viewport: string) {
  // Walk the multi-step intake form on /get-matched.
  const report: PageReport = {
    url: "/get-matched#walkthrough", asRole: role, viewport, loadStatus: "ok", finalURL: "", loadMs: 0,
    consoleErrors: [], pageErrors: [], failedRequests: [],
    inventory: { buttons: 0, links: 0, forms: 0, inputs: 0, selects: 0, tabs: 0, searchBoxes: 0, modals: 0, images: 0, brokenImages: 0 },
    buttonProbes: [], linkProbes: [], inputProbes: [], selectProbes: [], tabProbes: [],
    modalProbes: [], searchProbes: [], presentationFlags: [],
  };
  await attach(page, report);
  try {
    await page.goto(baseURL + "/get-matched", { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
  } catch (e: any) {
    report.loadStatus = "fail"; report.loadError = String(e?.message || e).slice(0, 200);
    results.push(report); fs.writeFileSync("/tmp/fm-crawl-v2.json", JSON.stringify(results, null, 2));
    return;
  }
  // Try to advance steps by clicking "Continue"/"Next"/"Submit" until we leave the form or no more buttons appear.
  for (let step = 1; step <= 10; step++) {
    // Best-effort: fill any visible inputs/selects on this step
    const inputs = page.locator("input:visible, textarea:visible");
    const inCount = await inputs.count();
    for (let i = 0; i < inCount; i++) {
      const inp = inputs.nth(i);
      const type = (await inp.getAttribute("type").catch(() => "text")) || "text";
      if (["radio", "checkbox", "file", "hidden", "submit", "button"].includes(type)) continue;
      let payload = "stress";
      if (type === "email") payload = "stress@example.com";
      else if (type === "tel") payload = "5555555555";
      else if (type === "number") payload = "300000";
      try { await inp.fill(payload, { timeout: 800 }); } catch {/*ignore*/}
    }
    const selects = page.locator("select:visible");
    const sCount = await selects.count();
    for (let i = 0; i < sCount; i++) {
      try {
        const opts = await selects.nth(i).locator("option").all();
        if (opts.length > 1) {
          const v = (await opts[1].getAttribute("value")) || "";
          await selects.nth(i).selectOption(v, { timeout: 800 });
        }
      } catch {/*ignore*/}
    }
    // Click the most likely "advance" button
    const candidates = [/^Continue$/i, /^Next$/i, /^Submit$/i, /^Find/i, /^Get Matched$/i, /^Start$/i];
    let advanced = false;
    for (const re of candidates) {
      const btn = page.getByRole("button", { name: re }).first();
      const visible = await btn.isVisible().catch(() => false);
      if (visible) {
        const errBefore = report.consoleErrors.length + report.pageErrors.length;
        try {
          await btn.click({ timeout: 2000 });
          await page.waitForTimeout(600);
          advanced = true;
          report.buttonProbes.push({ label: `step${step}:${re}`, outcome: (report.consoleErrors.length + report.pageErrors.length) > errBefore ? "console-error" : "ok" });
          break;
        } catch (e: any) {
          report.buttonProbes.push({ label: `step${step}:${re}`, outcome: "click-failed", detail: String(e?.message||e).slice(0,80) });
        }
      }
    }
    if (!advanced) break;
  }
  await checkPresentation(page, report);
  const shot = path.join(SHOTS_DIR, `${role}_${viewport}__getmatched_walk.png`);
  try { await page.screenshot({ path: shot, fullPage: true, timeout: 5000 }); report.screenshot = shot; } catch {/*ignore*/}
  report.finalURL = page.url();
  results.push(report);
  fs.writeFileSync("/tmp/fm-crawl-v2.json", JSON.stringify(results, null, 2));
}

test.describe.configure({ mode: "serial" });

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

for (const vp of VIEWPORTS) {
  test(`anonymous crawl on ${vp.name}`, async ({ browser }) => {
    test.setTimeout(900000);
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    for (const p of PUBLIC_PAGES) await probePage(page, p, "anonymous", vp.name);
    if (vp.name === "desktop") await walkGetMatched(page, "anonymous", vp.name);
    await context.close();
  });
}

test("user crawl on desktop", async ({ browser, request }) => {
  test.setTimeout(900000);
  const csrf = await primeCsrf(request);
  const headers = { "X-CSRF-Token": csrf };
  const email = `userv2_${Date.now()}@test.com`;
  const password = "StressTest12345!";
  await request.post(`${apiBase}/api/v1/auth/register`, { headers, data: { email, password, first_name: "U", last_name: "V2", user_type: "borrower" } });
  const log = await request.post(`${apiBase}/api/v1/auth/login`, { headers, data: { email, password } });
  expect(log.status(), `login: ${await log.text().catch(() => "")}`).toBeLessThan(400);
  const apiState = await request.storageState();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addCookies(apiState.cookies);
  const page = await context.newPage();
  for (const p of AUTHED_PAGES) await probePage(page, p, "user", "desktop");
  await context.close();
});

test("admin crawl on desktop", async ({ browser, request }) => {
  test.setTimeout(900000);
  const csrf = await primeCsrf(request);
  const headers = { "X-CSRF-Token": csrf };
  const email = `adminv2_${Date.now()}@test.com`;
  const password = "AdminStress12345!";
  await request.post(`${apiBase}/api/v1/auth/register`, { headers, data: { email, password, first_name: "A", last_name: "V2", user_type: "borrower" } });
  const { execSync } = require("child_process");
  execSync(`docker exec facemortgage-pg psql -U facemortgage -d facemortgage -c "UPDATE users SET is_admin=true, is_super_admin=true WHERE email='${email}'"`, { stdio: "ignore" });
  const log = await request.post(`${apiBase}/api/v1/auth/login`, { headers, data: { email, password } });
  expect(log.status(), `admin login: ${await log.text().catch(() => "")}`).toBeLessThan(400);
  const apiState = await request.storageState();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addCookies(apiState.cookies);
  const page = await context.newPage();
  for (const p of ADMIN_PAGES) await probePage(page, p, "admin", "desktop");
  await context.close();
});
