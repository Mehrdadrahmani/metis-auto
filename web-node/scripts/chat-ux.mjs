// $0 test of the friendlier chat page (ideas from ChatGPT / Claude). No sign-in and no model calls:
// the /login redirect is blocked and the page's fetch of /v1/chat/completions is answered by a stub.
//   node scripts/chat-ux.mjs            (site on :3001)
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SITE = process.env.SITE ?? "http://127.0.0.1:3001";
const OUT = new URL("../screenshots/chat-ux/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", ["--headless=new", "--remote-debugging-port=9339",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "tr-ux-"))}`, "--no-first-run", "--use-mock-keychain", "--password-store=basic", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try { const p = await (await fetch("http://127.0.0.1:9339/json/new?about:blank", { method: "PUT" })).json();
    ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((r) => ws.addEventListener("open", r, { once: true })); } catch { ws = undefined; await sleep(200); }
}
const cdp = (method, params = {}) => new Promise((res, rej) => { const n = ++id; const tm = setTimeout(() => rej(new Error("timeout " + method)), 30000);
  pend.set(n, (m) => { clearTimeout(tm); m.error ? rej(new Error(m.error.message)) : res(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data);
  if (m.method === "Fetch.requestPaused") cdp("Fetch.failRequest", { requestId: m.params.requestId, errorReason: "Aborted" });
  if (pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const ev = async (expression) => { const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description?.slice(0, 300) ?? "eval error"); return r.result.value; };
const until = async (expr, ms = 6000) => { for (let t = 0; t < ms; t += 100) { if (await ev(expr)) return true; await sleep(100); } return false; };
let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => { cond ? pass++ : fail++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  " + extra : ""}`); };
const shot = async (name) => writeFileSync(join(OUT, name + ".png"), Buffer.from((await cdp("Page.captureScreenshot", { format: "png" })).data, "base64"));
const key = async (k, code, mods = 0) => { for (const type of ["keyDown", "keyUp"]) await cdp("Input.dispatchKeyEvent", { type, key: k, code, modifiers: mods, windowsVirtualKeyCode: { ArrowUp: 38, Escape: 27, Enter: 13, o: 79 }[k] }); };

// a fake answer with markdown and a code block; DELAY makes "stop" testable
const STUB = `(() => { window.__delay = 300; const real = window.fetch;
  window.fetch = (url, opts = {}) => {
    if (String(url).includes("/v1/chat/completions")) return new Promise((res, rej) => {
      const t = setTimeout(() => res(new Response(JSON.stringify({ model: "deepseek-v4-flash", usage: {prompt_tokens: 20, completion_tokens: 60},
        choices: [{message: {content: "این یک پاسخ آزمایشی است.\\n\\n\`\`\`python\\ndef is_prime(n):\\n    return n > 1 and all(n % d for d in range(2, int(n**0.5) + 1))\\n\`\`\`\\n\\nهزینه حدود $0.0001 است."}}],
        takrouter: {cost_usd: 0.0001, cluster: 4, chosen: "deepseek-v4-flash", tried: ["deepseek-v4-flash"]} }), {status: 200, headers: {"content-type": "application/json"}})), window.__delay);
      opts.signal?.addEventListener("abort", () => { clearTimeout(t); rej(new DOMException("aborted", "AbortError")); });
    });
    return real(url, opts);
  };
  me = {id: 7, name: "Sara", email: "sara@test.localhost", role: "user", prefs: {}}; TR.me = me; TR.apply(); convs = []; current = null; renderAll(); return 1; })()`;

try {
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Fetch.enable", { patterns: [{ urlPattern: "*/login*" }] });
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 820, deviceScaleFactor: 1, mobile: false });
  await cdp("Page.navigate", { url: SITE + "/chat?lang=fa" }); await sleep(2500);
  await ev(STUB); await sleep(300);

  ok("new chat: input sits in the middle with the greeting", await ev(`(() => { const b = document.querySelector(".box").getBoundingClientRect(); return document.querySelector("#main").classList.contains("fresh") && b.top > 250 && b.top < 560; })()`));
  ok("new chat: 4 suggestions under the input", await ev(`document.querySelectorAll("#sugbox .sug").length === 4 && document.querySelector("#sugbox").getBoundingClientRect().top > document.querySelector(".box").getBoundingClientRect().bottom`));
  ok("site header is gone on the chat page", await ev(`!document.querySelector(".site-head") && document.querySelector(".app").getBoundingClientRect().top === 0`));
  ok("logo, language and theme sit in the sidebar", await ev(`!!document.querySelector("#side .side-logo") && !!document.querySelector("#side #langbtn") && !!document.querySelector("#side #themebtn")`));
  ok("language switch in the sidebar works", await ev(`(() => { document.querySelector("#langbtn").click(); const en = document.documentElement.lang === "en"; document.querySelector("#langbtn").click(); return en && document.documentElement.lang === "fa"; })()`));
  await ev(`document.querySelector("#acctbtn").click(), 1`); await sleep(250);
  ok("account menu opens upward inside the window, with the site links", await ev(`(() => { const m = document.querySelector("#acctmenu"), r = m.getBoundingClientRect();
    return m.classList.contains("open") && r.top >= 0 && r.bottom <= innerHeight && m.querySelectorAll(".sitelinks a").length === 7; })()`));
  await shot("1b-account-menu-fa");
  await ev(`document.body.click(), 1`); await sleep(200);
  ok("decision-trace switch moved into the settings menu", await ev(`!!document.querySelector("#pop #tracebox")`));
  await shot("1-new-chat-fa");

  await ev(`(() => { document.querySelector("#input").value = "یک تابع پایتون برای عدد اول بنویس"; send(); return 1; })()`);
  ok("new message slides in", await ev(`!!document.querySelector(".msg.user.enter")`));
  ok("'picking the best model' shimmers", await ev(`!!document.querySelector(".msg.bot .shimmer")`));
  ok("after sending, the input moves to the bottom", await until(`!document.querySelector("#main").classList.contains("fresh") && document.querySelector(".box").getBoundingClientRect().top > 650`));
  ok("answer finishes typing", await until(`!document.querySelector("[data-typing]") && !!document.querySelector(".msg.bot .meta")`, 8000));
  ok("code block has a language label and a copy button", await ev(`(() => { const h = document.querySelector(".answer pre .codehead"); return !!h && h.textContent.includes("python") && !!h.querySelector("button"); })()`));
  ok("code copy button does not end up inside the copied code", await ev(`!document.querySelector(".answer pre code").textContent.includes("python")`));
  await ev(`document.querySelector(".msg.bot .acts button").click(), 1`);
  ok("copy shows a check mark", await ev(`document.querySelector(".msg.bot .acts button").classList.contains("done")`));
  ok("last answer's actions are visible without hover", await ev(`getComputedStyle(document.querySelector(".msg.bot.last .acts")).opacity === "1"`));
  ok("user message has copy and edit", await ev(`document.querySelectorAll(".msg.user .acts button").length === 2`));
  ok("input is focused again after the answer", await ev(`document.activeElement === document.querySelector("#input")`));
  await shot("2-answer-with-code-fa");

  // edit with the up arrow
  await ev(`document.querySelector("#input").focus(), 1`); await key("ArrowUp", "ArrowUp");
  ok("↑ in the empty input opens the last message for editing", await until(`!!document.querySelector(".editbox textarea")`, 2000));
  await shot("3-editing-fa");
  await key("Escape", "Escape");
  ok("Esc cancels the edit", await until(`!document.querySelector(".editbox")`, 2000));
  await ev(`startEdit(0), 1`);
  await ev(`(() => { document.querySelector(".editbox textarea").value = "یک تابع جاوااسکریپت بنویس"; document.querySelector(".editbox .btn.primary").click(); return 1; })()`);
  ok("edited message is sent again and replaces the old turn", await until(`conv().messages.length === 2 && conv().messages[0].content.includes("جاوااسکریپت") && conv().messages[1].role === "assistant"`, 8000));
  await until(`!document.querySelector("[data-typing]")`, 8000);

  // stop with Esc
  await ev(`(() => { window.__delay = 5000; document.querySelector("#input").value = "سوال طولانی"; send(); return 1; })()`); await sleep(300);
  await key("Escape", "Escape");
  ok("Esc stops a running answer", await until(`!!conv().messages.at(-1).error && !busy`, 3000));
  await ev(`window.__delay = 300, 1`);

  // sidebar: groups, search, rename, delete + undo, hide
  await ev(`(() => { const d = 86400000, mk = (title, ago) => ({id: title, title, ts: Date.now() - ago, messages: [{role: "user", content: title + " متن"}]});
    convs.push(mk("دیروزی", d * 1.2), mk("هفته", d * 4), mk("قدیمی", d * 40)); save(); renderList(); return 1; })()`);
  ok("chats grouped by day", await ev(`[...document.querySelectorAll("#list h6")].map(h => h.textContent).join("|") === "امروز|دیروز|۷ روز گذشته|قدیمی‌تر"`),
    await ev(`[...document.querySelectorAll("#list h6")].map(h => h.textContent).join("|")`));
  await ev(`(() => { const s = document.querySelector("#search"); s.value = "قدیمی"; s.dispatchEvent(new Event("input")); return 1; })()`);
  ok("search filters the list", await ev(`document.querySelectorAll("#list .conv").length === 1`));
  await ev(`(() => { const s = document.querySelector("#search"); s.value = ""; s.dispatchEvent(new Event("input")); return 1; })()`);
  await shot("4-sidebar-groups-fa");
  await ev(`document.querySelectorAll("#list .conv")[1].querySelector("button").click(), 1`);
  ok("rename happens in place (no pop-up)", await ev(`!!document.querySelector("#list .conv input")`));
  await ev(`(() => { const i = document.querySelector("#list .conv input"); i.value = "سفر شیراز"; i.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter"})); return 1; })()`);
  ok("rename saved", await ev(`convs.some(c => c.title === "سفر شیراز")`));
  const n0 = await ev(`convs.length`);
  await ev(`document.querySelectorAll("#list .conv")[2].querySelectorAll("button")[1].click(), 1`);
  ok("delete shows Undo", await ev(`convs.length === ${n0 - 1} && !!document.querySelector(".undo button")`));
  await ev(`document.querySelector(".undo button").click(), 1`);
  ok("Undo brings the chat back", await ev(`convs.length === ${n0}`));
  await ev(`document.querySelector("#sidetoggle").click(), 1`); await sleep(400);
  ok("sidebar collapses to a thin rail (like Claude)", await ev(`document.querySelector(".app").classList.contains("collapsed") && document.querySelector("#side").getBoundingClientRect().width <= 62`),
    String(await ev(`document.querySelector("#side").getBoundingClientRect().width`)));
  ok("rail keeps new chat, search and account as icons", await ev(`["#newchat", "#searchbtn", "#sidetoggle", ".acct-btn"].every(q => { const r = document.querySelector(q).getBoundingClientRect(); return r.width > 0 && r.width <= 46; })`));
  await shot("4b-rail-fa");
  await ev(`document.querySelector("#searchbtn").click(), 1`); await sleep(450);
  ok("search icon opens the sidebar and focuses search", await ev(`!document.querySelector(".app").classList.contains("collapsed") && document.activeElement === document.querySelector("#search")`));

  // jump-to-latest button
  await ev(`(() => { const c = conv(); for (let k = 0; k < 12; k++) c.messages.push({role: "user", content: "پیام " + k}, {role: "assistant", content: "پاسخ طولانی ".repeat(40), meta: {model: "gpt-5.6-luna", cost: 0.0001}}); renderAll(); document.querySelector("#scroll").scrollTop = 0; document.querySelector("#scroll").dispatchEvent(new Event("scroll")); return 1; })()`);
  ok("'jump to latest' appears when scrolled up", await until(`document.querySelector("#tobottom").classList.contains("show")`, 2000));
  await shot("5-scrolled-up-fa");
  await ev(`document.querySelector("#tobottom").click(), 1`);
  ok("and takes you to the bottom", await until(`!document.querySelector("#tobottom").classList.contains("show")`, 3000));

  // new chat shortcut
  await key("o", "KeyO", 8 | 2);
  ok("Ctrl+Shift+O starts a new chat", await until(`document.querySelector("#main").classList.contains("fresh")`, 2000));

  // English + dark, and a phone
  await ev(`TR.setLang("en"), 1`); await sleep(400); await shot("6-new-chat-en");
  await cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "dark" }] });
  await ev(`(() => { current = convs.find(c => c.messages.length > 3)?.id; renderAll(); return 1; })()`); await sleep(300);
  await ev(`document.querySelector("#scroll").scrollTop = 0, 1`); await sleep(200); await shot("7-chat-en-dark");
  await cdp("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await ev(`(() => { TR.setLang("fa"); current = null; renderAll(); return 1; })()`); await sleep(500);
  ok("phone: nothing wider than the screen", await ev(`document.documentElement.scrollWidth <= 390`));
  await shot("8-phone-fa-dark");
  await ev(`document.querySelector("#sidebtn").click(), 1`); await sleep(400);
  ok("phone: the chat list slides in over a backdrop", await ev(`(() => { const r = document.querySelector("#side").getBoundingClientRect(); return r.right <= 391 && r.left >= -1 && document.querySelector("#backdrop").classList.contains("show"); })()`));
  await shot("9-phone-side-open");
  await ev(`document.querySelector("#backdrop").click(), 1`); await sleep(400);
  ok("phone: tapping outside closes it", await ev(`(() => { const r = document.querySelector("#side").getBoundingClientRect(); return r.left >= 389 || r.right <= 1; })()`));
} catch (e) { fail++; console.log("FAIL  " + e.message); }
finally { chrome.kill(); }
console.log(`\n${pass} passed, ${fail} failed. Screenshots: ${OUT}`);
process.exit(fail ? 1 : 0);
