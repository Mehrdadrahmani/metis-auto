// $0 check: every text box takes its direction from what is typed (Persian -> rtl, English -> ltr, empty -> page),
// on every page, in both languages; the cursor stays at the end of the text while typing.
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SITE = process.env.SITE ?? "http://127.0.0.1:3001";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", ["--headless=new", "--remote-debugging-port=9341",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-dir-"))}`, "--no-first-run", "--use-mock-keychain", "--password-store=basic", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try { const p = await (await fetch("http://127.0.0.1:9341/json/new?about:blank", { method: "PUT" })).json();
    ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((r) => ws.addEventListener("open", r, { once: true })); } catch { ws = undefined; await sleep(200); }
}
const cdp = (method, params = {}) => new Promise((res, rej) => { const n = ++id; const tm = setTimeout(() => rej(new Error("timeout " + method)), 30000);
  pend.set(n, (m) => { clearTimeout(tm); m.error ? rej(new Error(m.error.message)) : res(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data);
  if (m.method === "Fetch.requestPaused") cdp("Fetch.failRequest", { requestId: m.params.requestId, errorReason: "Aborted" });
  if (pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const ev = async (expression) => { const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description?.slice(0, 200) ?? "eval error"); return r.result.value; };
let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => { cond ? pass++ : fail++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  " + extra : ""}`); };

// pages with text boxes (signed-out pages that redirect to /login are kept with the redirect blocked)
const PAGES = [["/chat", "#input"], ["/chat", "#search"], ["/login", 'input[type="email"]'], ["/account", "#name"], ["/khayyam/chat", "textarea, input[type=text]"], ["/compare", "textarea"], ["/models", "input[type=text], input:not([type])"]];
try {
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Fetch.enable", { patterns: [{ urlPattern: "*/login?next*" }] });
  for (const lang of ["fa", "en"]) {
    for (const [path, sel] of PAGES) {
      await cdp("Page.navigate", { url: `${SITE}${path}?lang=${lang}` }); await sleep(1600);
      const has = await ev(`!!document.querySelector(${JSON.stringify(sel)})`);
      if (!has) { console.log(`skip  ${lang} ${path} ${sel} (not on this page)`); continue; }
      await ev(`(() => { const f = document.querySelector(${JSON.stringify(sel)}); f.value = ""; f.focus(); f.dispatchEvent(new Event("input", {bubbles: true})); return 1; })()`);
      const pageDir = lang === "fa" ? "rtl" : "ltr";
      if (await ev(`document.querySelector(${JSON.stringify(sel)}).classList.contains("ltr")`)) {  // emails, model ids: always ltr
        await cdp("Input.insertText", { text: "سلام" });
        ok(`${lang} ${path.padEnd(13)} ${sel.slice(0, 22).padEnd(22)} stays left-to-right (marked .ltr)`,
          await ev(`getComputedStyle(document.querySelector(${JSON.stringify(sel)})).direction === "ltr"`));
        continue;
      }
      const empty = await ev(`document.querySelector(${JSON.stringify(sel)}).getAttribute("dir")`);
      await cdp("Input.insertText", { text: "سلام دوست من" });
      const fa = await ev(`(() => { const f = document.querySelector(${JSON.stringify(sel)}); return [f.getAttribute("dir"), getComputedStyle(f).direction, f.selectionStart === f.value.length, getComputedStyle(f).unicodeBidi]; })()`);
      await ev(`(() => { const f = document.querySelector(${JSON.stringify(sel)}); f.value = ""; f.dispatchEvent(new Event("input", {bubbles: true})); return 1; })()`);
      await cdp("Input.insertText", { text: "hello friend" });
      const en = await ev(`(() => { const f = document.querySelector(${JSON.stringify(sel)}); return [f.getAttribute("dir"), f.selectionStart === f.value.length]; })()`);
      ok(`${lang} ${path.padEnd(13)} ${sel.slice(0, 22).padEnd(22)} empty=${empty} fa=${fa[0]} en=${en[0]}`,
        empty === pageDir && fa[0] === "rtl" && fa[1] === "rtl" && fa[2] && fa[3] !== "plaintext" && en[0] === "ltr" && en[1]);
    }
  }
} catch (e) { fail++; console.log("FAIL  " + e.message); }
finally { chrome.kill(); }
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
