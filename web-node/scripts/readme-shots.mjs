// Product screenshots for the README (docs/screenshots/). $0: no model calls. Public pages are shot as they are;
// the chat page is shown with an example conversation written here (the live router data, prices and
// "why this model?" scores come from the running gateway). No user data, no Khayyam question text.
//   node scripts/readme-shots.mjs            (site on :3001, gateway on :8000)
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SITE = process.env.SITE ?? "http://127.0.0.1:3001";
const OUT = process.env.OUT ?? new URL("../../docs/screenshots/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", ["--headless=new", "--remote-debugging-port=9342",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-shots-"))}`, "--no-first-run", "--use-mock-keychain", "--password-store=basic", "--hide-scrollbars",
  "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try { const p = await (await fetch("http://127.0.0.1:9342/json/new?about:blank", { method: "PUT" })).json();
    ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((r) => ws.addEventListener("open", r, { once: true })); } catch { ws = undefined; await sleep(200); }
}
const cdp = (method, params = {}) => new Promise((res, rej) => { const n = ++id; const tm = setTimeout(() => rej(new Error("timeout " + method)), 30000);
  pend.set(n, (m) => { clearTimeout(tm); m.error ? rej(new Error(m.error.message)) : res(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data);
  if (m.method === "Fetch.requestPaused") cdp("Fetch.failRequest", { requestId: m.params.requestId, errorReason: "Aborted" });
  if (pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const ev = async (expression) => { const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description?.slice(0, 300) ?? "eval error"); return r.result.value; };
const view = (width, height, dark = false, mobile = false) => Promise.all([
  cdp("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 2, mobile }),
  cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: dark ? "dark" : "light" }] })]);
const go = async (path, wait = 2200) => { await cdp("Page.navigate", { url: SITE + path }); await sleep(wait); await ev("document.fonts.ready.then(() => 1)"); };
const shot = async (name) => { writeFileSync(join(OUT, name + ".png"), Buffer.from((await cdp("Page.captureScreenshot", { format: "png" })).data, "base64")); console.log("saved", name); };

// The chat page needs a signed-in user: the /login redirect is blocked and an example user is set in the page.
const CHAT = (lang, convs) => `(async () => {
  me = {id: 0, name: "Sara", email: "sara@example.com", role: "user", prefs: {}}; TR.me = me; TR.apply();
  try { health = await TR.api("/health"); } catch { health = null; }
  router = await TR.api("/v1/router");
  const s = new Set([0, router.default_lambda, 3, ...router.breakpoints.filter((b) => b < 20)]);
  stops = [...s].map((x) => +(+x).toFixed(4)).sort((a, b) => a - b); $("lam").max = stops.length - 1;
  convs = ${JSON.stringify(convs)}; current = convs[0].id; for (const c of convs) { seen[c.id] = c.messages.length; } shownId = current;
  setMode("bal"); fillForce(); renderAll(); renderStatus(); refreshCredit = () => {}; $("credit").textContent = "$0.482";
  return 1; })()`;
const now = Date.now(), day = 86400000;
const FA = [
  {id: "a", ts: now, title: "برنامه سفر سه روزه به شیراز", messages: [
    {role: "user", content: "یک برنامه سه روزه برای سفر به شیراز پیشنهاد بده"},
    {role: "assistant", content: "**روز اول:** صبح به حافظیه بروید و عصر در باغ ارم قدم بزنید. شب را به بازار وکیل و سرای مشیر اختصاص دهید.\n\n**روز دوم:** صبح زود راهی تخت جمشید (حدود ۶۰ کیلومتر) شوید و سر راه نقش رستم را هم ببینید.\n\n**روز سوم:** مسجد نصیرالملک را صبح ببینید، وقتی نور از شیشه‌های رنگی می‌تابد. بعد از ظهر سعدیه و دروازه قرآن.\n\n- بهترین فصل: فروردین و اردیبهشت\n- هزینه‌ی بلیت تخت جمشید را از قبل بررسی کنید.",
     meta: {model: "gpt-5.6-luna", cluster: 6, cost: 0.00041, premium: 0.0068, saved: 0.94, seconds: 3.1, cache: "miss", tried: ["gpt-5.6-luna"]}}]},
  {id: "b", ts: now - day * 1.1, title: "تابع عدد اول در پایتون", messages: [{role: "user", content: "x"}]},
  {id: "c", ts: now - day * 3, title: "پیگیری سفارش و بازگشت پول", messages: [{role: "user", content: "x"}]},
  {id: "d", ts: now - day * 20, title: "توضیح بیت حافظ", messages: [{role: "user", content: "x"}]},
];
const EN = [
  {id: "e", ts: now, title: "Prime check in Python", messages: [
    {role: "user", content: "Write a Python function that checks whether a number is prime"},
    {role: "assistant", content: "Trial division up to the square root is enough:\n\n```python\ndef is_prime(n: int) -> bool:\n    if n < 2:\n        return False\n    for d in range(2, int(n ** 0.5) + 1):\n        if n % d == 0:\n            return False\n    return True\n```\n\nIt runs in O(√n) time. For many numbers at once, a sieve of Eratosthenes is faster.",
     meta: {model: "deepseek-v4-flash", cluster: 4, cost: 0.00018, premium: 0.0049, saved: 0.96, seconds: 2.4, cache: "miss", tried: ["deepseek-v4-flash"]}}]},
  {id: "f", ts: now - day * 1.2, title: "Weather vs climate", messages: [{role: "user", content: "x"}]},
  {id: "g", ts: now - day * 5, title: "Refund for a failed order", messages: [{role: "user", content: "x"}]},
];

try {
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Fetch.enable", { patterns: [{ urlPattern: "*/login?next*" }] });

  await view(1440, 900); await go("/?lang=en"); await shot("home-en");
  await go("/?lang=fa"); await shot("home-fa");

  await go("/chat?lang=fa", 2500); await ev(CHAT("fa", FA));
  await sleep(300); await ev(`document.querySelector(".meta button.chip").click(), 1`); await sleep(400);
  await ev(`document.querySelector("#scroll").scrollTop = 0, 1`); await sleep(200); await shot("chat-fa");

  await view(1440, 900, true); await go("/chat?lang=en", 2500); await ev(CHAT("en", EN)); await sleep(500); await shot("chat-en-dark");
  await ev(`(() => { current = null; renderAll(); return 1; })()`); await sleep(600); await shot("new-chat-en-dark");

  await view(1440, 900); await go("/how?lang=en"); await shot("how-en");
  await go("/results"); await shot("results-fa");
  await go("/pricing?lang=en"); await shot("pricing-en");

  await view(390, 844, false, true); await go("/chat?lang=fa", 2500); await ev(CHAT("fa", FA)); await sleep(400);
  await ev(`document.querySelector("#scroll").scrollTop = 0, 1`); await sleep(200); await shot("phone-chat-fa");
} catch (e) { console.log("FAIL  " + e.message); process.exitCode = 1; }
finally { chrome.kill(); }
