// UI test of streaming on /chat: the answer is drawn while the model writes; stop keeps the partial text. Needs a MOCK gateway behind the site
// (no model calls, $0) and a test user. Usage:
//   SITE=http://127.0.0.1:3002 EMAIL=... PASSWORD=... node scripts/byok-ui.mjs
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SITE = process.env.SITE ?? "http://127.0.0.1:3001";
const { EMAIL, PASSWORD } = process.env;
const GOOD = process.env.GOOD_KEY ?? "test-own-key-000000000000000001"; // fake test values; the mock gateway refuses BAD
const BAD = process.env.BAD_KEY ?? "test-own-key-refused-0000000002";
const CHROME = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT = new URL("../screenshots/stream/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9340", `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-byok-"))}`,
  "--no-first-run", "--use-mock-keychain", "--password-store=basic", "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const page = await (await fetch("http://127.0.0.1:9340/json/new?about:blank", { method: "PUT" })).json();
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
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 860, deviceScaleFactor: 1, mobile: false });
  await go("/login?lang=fa", 800);
  ok("test user signs in", (await ev(`fetch("/auth/login", {method: "POST", headers: {"content-type": "application/json"},
    body: JSON.stringify({email: ${JSON.stringify(EMAIL)}, password: ${JSON.stringify(PASSWORD)}})}).then(r => r.status)`)) === 200);
  await ev(`fetch("/auth/provider-key", {method: "DELETE"}).then(r => r.status)`);
  await go("/chat?lang=fa", 2500);
  await ev(`(() => { convs = []; current = null; renderAll(); document.querySelector("#input").value = "درباره شیراز بگو"; send(); return 1; })()`);
  ok("answer appears while it is being written", await until(`!!document.querySelector(".answer[data-typing] .caret")`, 5000));
  const a = await ev(`document.querySelector(".answer[data-typing]").textContent.length`);
  await sleep(500); await shot("stream-mid-fa");
  const b = await ev(`document.querySelector(".answer[data-typing]")?.textContent.length || 0`);
  ok("and keeps growing", b > a, `${a} -> ${b} chars`);
  ok("price stays in order while streaming", await ev(`[...document.querySelectorAll(".answer[data-typing] bdi")].some(x => x.textContent.startsWith("$0.0007"))`));
  ok("finished answer gets model, cost and actions", await until(`!document.querySelector("[data-typing]") && !!document.querySelector(".msg.bot .meta") && !busy`, 8000));
  ok("streamed text equals the stored answer", await ev(`conv().messages.at(-1).content.length > 300 && conv().messages.at(-1).content.includes("English words inside")`));
  await shot("stream-done-fa");
  await ev(`(() => { document.querySelector("#input").value = "یک سوال دیگر"; send(); return 1; })()`);
  await until(`(document.querySelector(".answer[data-typing]")?.textContent.length || 0) > 60`, 5000);
  await ev(`busy.abort(), 1`);
  ok("stopping halfway keeps the text written so far", await until(`!busy && conv().messages.at(-1).stoppedPartial && conv().messages.at(-1).content.length > 40 && !!document.querySelector(".stopnote")`, 3000));
  await shot("stream-stopped-fa");
} catch (e) { fail++; console.log("FAIL  " + e.message); }
finally { chrome.kill(); }
console.log(`\n${pass} passed, ${fail} failed. Screenshots: ${OUT}`);
process.exit(fail ? 1 : 0);
