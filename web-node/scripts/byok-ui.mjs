// UI test of the Node-only additions: own Metis key on /account, its use in /chat, live typing of answers,
// the sliding mode toggle and the header that no longer overflows. Needs a MOCK gateway behind the site
// (no model calls, $0) and a test user. Usage:
//   SITE=http://127.0.0.1:3002 EMAIL=... PASSWORD=... node scripts/byok-ui.mjs
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SITE = process.env.SITE ?? "http://127.0.0.1:3002";
const { EMAIL, PASSWORD } = process.env;
const GOOD = process.env.GOOD_KEY ?? "test-own-key-000000000000000001"; // fake test values; the mock gateway refuses BAD
const BAD = process.env.BAD_KEY ?? "test-own-key-refused-0000000002";
const CHROME = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT = new URL("../screenshots/byok/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9337", `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-byok-"))}`,
  "--no-first-run", "--use-mock-keychain", "--password-store=basic", "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const page = await (await fetch("http://127.0.0.1:9337/json/new?about:blank", { method: "PUT" })).json();
    ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r) => ws.addEventListener("open", r, { once: true }));
  } catch { ws = undefined; await sleep(200); }
}
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const cdp = (method, params = {}) => new Promise((res, rej) => {
  const n = ++id; const t = setTimeout(() => rej(new Error("timeout " + method)), 30000);
  pend.set(n, (m) => { clearTimeout(t); if (m.error) rej(new Error(m.error.message)); else res(m.result); });
  ws.send(JSON.stringify({ id: n, method, params }));
});
const ev = async (expression) => { const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description?.slice(0, 300) ?? "eval error"); return r.result.value; };
let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => { if (cond) pass++; else fail++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  " + extra : ""}`); };
const shot = async (name) => writeFileSync(join(OUT, name + ".png"), Buffer.from((await cdp("Page.captureScreenshot", { format: "png" })).data, "base64"));
const go = async (path, wait = 1800) => { await cdp("Page.navigate", { url: SITE + path }); await sleep(wait); await ev("document.fonts.ready.then(() => 1)"); };
const until = async (expr, ms = 6000) => { for (let t = 0; t < ms; t += 100) { if (await ev(expr)) return true; await sleep(100); } return false; };

try {
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });

  // header, signed out, English, 1280 px: the sign-in button is inside the window
  await go("/?lang=en");
  const right = await ev(`document.querySelector("#acct").getBoundingClientRect().right`);
  ok("header fits at 1280 px (en, signed out)", right <= 1280, `account box ends at ${Math.round(right)} px`);
  await shot("header-en-1280");

  await go("/login?lang=fa", 800);
  const signed = await ev(`fetch("/auth/login", {method: "POST", headers: {"content-type": "application/json"},
    body: JSON.stringify({email: ${JSON.stringify(EMAIL)}, password: ${JSON.stringify(PASSWORD)}})}).then(r => r.status)`);
  ok("test user signs in", signed === 200, String(signed));
  await ev(`fetch("/auth/provider-key", {method: "DELETE"}).then(r => r.status)`);

  for (const lang of ["en", "fa"]) {
    await go(`/?lang=${lang}`);
    const r = await ev(`document.querySelector("#acct").getBoundingClientRect().right`);
    const l = await ev(`document.querySelector("#acct").getBoundingClientRect().left`);
    ok(`header fits at 1280 px (${lang}, signed in)`, r <= 1280 && l >= 0, `${Math.round(l)}..${Math.round(r)} px`);
  }
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1100, height: 900, deviceScaleFactor: 1, mobile: false });
  await go("/?lang=en");
  ok("menu button below 1180 px", await ev(`getComputedStyle(document.querySelector("#burger")).display !== "none"`));
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });

  // account page: the own-key section
  await go("/account?lang=fa", 2200);
  ok("own-key section is on the account page", await ev(`!!document.querySelector("#ownkey h3")?.textContent`));
  ok("shows 'no key' at first", await ev(`document.querySelector("#ownstate").textContent.length > 10 && !document.querySelector("#ownstate b")`));
  const save = async (key) => { await ev(`(() => { const i = document.querySelector("#ownval"); i.value = ${JSON.stringify(key)}; document.querySelector("#ownsave").click(); return 1; })()`);
    await until(`!document.querySelector("#ownsave").disabled && document.querySelector("#ownstate b") !== null`); await sleep(300); };
  await save("short");
  ok("too-short key refused with a message", await ev(`document.querySelector(".toast")?.textContent.includes("۱۶")`));
  await save(BAD);
  ok("refused key marked red", await ev(`!!document.querySelector("#ownstate .pillx.bad")`));
  ok("input cleared after saving", await ev(`document.querySelector("#ownval").value === ""`));
  await shot("account-own-key-refused-fa");
  await save(GOOD);
  ok("working key marked green with its last 4 characters", await ev(`!!document.querySelector("#ownstate .pillx.good") && document.querySelector("#ownstate b").textContent.includes("0001")`));
  ok("the full key is nowhere on the page", await ev(`!document.documentElement.outerHTML.includes(${JSON.stringify(GOOD)})`));
  await ev(`document.querySelector("#ownkey").scrollIntoView({block: "center"})`); await sleep(200);
  await shot("account-own-key-ok-fa");
  await go("/account?lang=en", 2200);
  await ev(`document.querySelector("#ownkey").scrollIntoView({block: "center"})`); await sleep(200);
  await shot("account-own-key-ok-en");

  // chat: badge, sliding toggle, live typing
  await go("/chat?lang=fa", 2500);
  ok("chat page uses the full screen (no site header; logo and account in the sidebar)",
    await ev(`!document.querySelector(".site-head") && !!document.querySelector("#side .side-logo")`));
  ok("chat shows 'your own key' badge", await until(`!!document.querySelector("#owntag:not(.hide)")`));
  const pillAt = `(() => { const p = document.querySelector("#modes .pill"), b = document.querySelector("#modes button.on");
    return Math.abs(p.getBoundingClientRect().left - b.getBoundingClientRect().left) < 2 && Math.abs(p.offsetWidth - b.offsetWidth) < 2; })()`;
  ok("toggle highlight sits under the chosen mode", await until(pillAt, 2000));
  await ev(`document.querySelector('#modes button[data-mode="best"]').click(), 1`);
  await sleep(120);
  ok("toggle highlight is moving (mid-slide)", !(await ev(pillAt)));
  await sleep(500);
  ok("toggle highlight arrives at the new mode", await ev(pillAt));
  await ev(`document.querySelector('#modes button[data-mode="bal"]').click(), 1`); await sleep(500);

  const creditBefore = await ev(`TR.api("/auth/me").then(r => r.credit_left_usd)`);
  await ev(`(() => { document.querySelector("#input").value = "سلام، درباره سفر به شیراز بگو"; send(); return 1; })()`);
  ok("answer starts typing live", await until(`!!document.querySelector(".answer[data-typing] .caret")`, 8000));
  ok("price inside Persian is isolated while typing", await until(`[...document.querySelectorAll(".answer[data-typing] bdi")].some(b => b.textContent.startsWith("$0.0007"))`, 3000));
  await sleep(300);
  const partial = await ev(`document.querySelector(".answer[data-typing]")?.textContent.length || 0`);
  await shot("chat-typing-fa");
  await sleep(400);
  const later = await ev(`document.querySelector(".answer[data-typing]")?.textContent.length || 99999`);
  ok("text grows while typing", later > partial, `${partial} -> ${later} chars`);
  ok("typing finishes and the answer is drawn in full", await until(`!document.querySelector("[data-typing]") && !!document.querySelector(".msg.bot .meta")`, 8000));
  ok("credit unchanged with own key", await ev(`TR.api("/auth/me").then(r => r.credit_left_usd === ${creditBefore})`), `$${creditBefore}`);
  await shot("chat-done-fa");

  // refused key in chat: clear message
  await ev(`fetch("/auth/provider-key", {method: "PUT", headers: {"content-type": "application/json"}, body: JSON.stringify({key: ${JSON.stringify(BAD)}})}).then(r => r.status)`);
  await ev(`(() => { document.querySelector("#input").value = "hello"; send(); return 1; })()`);
  ok("refused key in chat gives a clear message", await until(`[...document.querySelectorAll(".errbox")].some(e => e.textContent.includes("حساب کاربری"))`, 8000));
  await shot("chat-own-key-refused-fa");
  await ev(`fetch("/auth/provider-key", {method: "PUT", headers: {"content-type": "application/json"}, body: JSON.stringify({key: ${JSON.stringify(GOOD)}})}).then(r => r.status)`);
} catch (e) { fail++; console.log("FAIL  " + e.message); }
finally { chrome.kill(); }
console.log(`\n${pass} passed, ${fail} failed. Screenshots: ${OUT}`);
process.exit(fail ? 1 : 0);
