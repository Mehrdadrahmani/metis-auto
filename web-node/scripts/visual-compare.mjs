// Pixel comparison, Python site (:8000) vs Node.js site (:3001), every page in Persian and English, plus the
// RTL cases on the real chat page. Headless Chrome via the DevTools protocol, no extra packages. $0, no model calls.
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const OLD = process.env.OLD ?? "http://127.0.0.1:8000";
const NEW = process.env.NEW ?? "http://127.0.0.1:3001";
const CHROME = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT = new URL("../screenshots/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const PAGES = Object.keys(Object.fromEntries([...readFileSync(new URL("../src/pages.ts", import.meta.url), "utf8")
  .matchAll(/"([^"]+)":\s*"[^"]+\.html"/g)].map((m) => [m[1], 1])));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9336", `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-node-"))}`,
  "--no-first-run", "--use-mock-keychain", "--password-store=basic", "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const page = await (await fetch("http://127.0.0.1:9336/json/new?about:blank", { method: "PUT" })).json();
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
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description?.slice(0, 200) ?? "eval error"); return r.result.value; };

let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => { if (cond) pass++; else fail++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  " + extra : ""}`); };

async function shoot(url) {
  await cdp("Page.navigate", { url }); await sleep(2600);
  await ev("document.fonts ? document.fonts.ready.then(() => true) : true"); await sleep(300);
  return (await cdp("Page.captureScreenshot", { format: "png" })).data;
}
// Compare two PNGs inside Chrome (canvas), count pixels that differ by more than a small tolerance.
async function diff(a, b) {
  return ev(`(async () => {
    const load = (s) => new Promise((r) => { const i = new Image(); i.onload = () => r(i); i.src = "data:image/png;base64," + s; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a)}), load(${JSON.stringify(b)})]);
    const W = Math.min(x.width, y.width), H = Math.min(x.height, y.height);
    const px = (img) => { const c = new OffscreenCanvas(W, H); const g = c.getContext("2d"); g.drawImage(img, 0, 0); return g.getImageData(0, 0, W, H).data; };
    const p = px(x), q = px(y); let n = 0;
    for (let i = 0; i < p.length; i += 4) if (Math.abs(p[i]-q[i]) + Math.abs(p[i+1]-q[i+1]) + Math.abs(p[i+2]-q[i+2]) > 24) n++;
    return n / (W * H);
  })()`);
}

try {
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const lang of ["fa", "en"]) {
    for (const p of PAGES) {
      const q = (p.includes("?") ? "&" : "?") + "lang=" + lang;
      const a = await shoot(OLD + p + q), b = await shoot(NEW + p + q);
      const d = await diff(a, b);
      const name = (p === "/" ? "home" : p.slice(1).replace("/", "-")) + "-" + lang;
      writeFileSync(join(OUT, `${name}-python.png`), Buffer.from(a, "base64"));
      writeFileSync(join(OUT, `${name}-node.png`), Buffer.from(b, "base64"));
      // Khayyam shows a random sample question, so its pages can differ by that text alone.
      const limit = p.startsWith("/khayyam") ? 0.05 : 0.005;
      ok(`${lang} ${p.padEnd(14)} looks the same`, d <= limit, `${(d * 100).toFixed(2)}% pixels differ`);
    }
  }

  // RTL cases on the real chat page, with the page's own rendering functions (md, userMsg, el) and CSS.
  // The page sends signed-out visitors to /login; that one navigation is blocked here so the chat page stays.
  const PROBE = `
    window.__charX = (root, needle, k) => { const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let n, acc = "";
      const nodes = []; while ((n = w.nextNode())) nodes.push(n); const full = nodes.map(x => x.nodeValue).join(""); const at = full.indexOf(needle);
      if (at < 0) return null; let i = at + k; for (const x of nodes) { if (i < x.nodeValue.length) { const r = document.createRange(); r.setStart(x, i); r.setEnd(x, i + 1); return r.getBoundingClientRect().left; } i -= x.nodeValue.length; } return null; };`;
  const cases = async (base) => {
    await cdp("Fetch.enable", { patterns: [{ urlPattern: "*/login*", requestStage: "Request" }] });
    const onPause = (e) => { const m = JSON.parse(e.data); if (m.method === "Fetch.requestPaused") ws.send(JSON.stringify({ id: ++id, method: "Fetch.failRequest", params: { requestId: m.params.requestId, errorReason: "Aborted" } })); };
    ws.addEventListener("message", onPause);
    await cdp("Page.navigate", { url: base + "/chat?lang=fa" }); await sleep(2600);
    await cdp("Fetch.disable"); ws.removeEventListener("message", onPause);
    await ev(PROBE);
    return ev(`(async () => {
      const th = document.getElementById("thread"); document.getElementById("empty")?.classList.add("hide");
      const add = (cls, html) => { const m = el("div", "msg bot"); const b = el("div", "body"); b.append(el("div", cls, html)); m.append(b); th.append(m); return m; };
      const u = userMsg({ content: "Hello, how are you?" }); th.append(u);
      const en = add("answer", md("Sure. Here is the answer you asked for!"));
      const fa = add("answer", md("مدل DeepSeek V4 Flash با هزینه‌ی $0.0007 انتخاب شد."));
      await new Promise((r) => setTimeout(r, 300));   // let the add-on (if any) process new nodes
      const q = __charX(u, "Hello, how are you?", 18), h = __charX(u, "Hello, how are you?", 0);
      const ex = __charX(en, "for!", 3), s = __charX(en, "Sure", 0);
      const d = __charX(fa, "$0.0007", 0), seven = __charX(fa, "$0.0007", 6);
      return { englishMessage: q > h, englishAnswer: ex > s, price: d < seven };
    })()`);
  };
  const before = await cases(OLD);
  const after = await cases(NEW);
  const { data } = await cdp("Page.captureScreenshot", { format: "png" }); writeFileSync(join(OUT, "chat-rtl-cases-node.png"), Buffer.from(data, "base64"));
  console.log("\nRTL cases on the chat page (Persian interface):  Python site -> Node site");
  for (const [k, label] of [["englishMessage", "English message: '?' at the end"], ["englishAnswer", "English answer: '!' at the end"], ["price", "Price inside Persian: '$0.0007' in order"]]) {
    console.log(`  ${label.padEnd(42)} ${before[k] ? "ok " : "BAD"} -> ${after[k] ? "ok" : "BAD"}`);
    ok(`Node site: ${label}`, after[k] === true);
  }
} finally {
  ws?.close(); chrome.kill();
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
