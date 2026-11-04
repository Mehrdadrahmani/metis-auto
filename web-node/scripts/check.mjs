// $0 check of the Node.js site against the Python one. Needs: Python gateway on :8000, this app on :3001.
//  1. every page exists and its HTML is the original file, byte for byte, apart from the lang/dir tag and the two add-on lines;
//  2. every asset is identical; 3. API calls reach the gateway (free endpoints only; chat must be refused when signed out).
import { readFile } from "node:fs/promises";
const OLD = process.env.OLD ?? "http://127.0.0.1:8000";
const NEW = process.env.NEW ?? "http://127.0.0.1:3001";
const { PAGES } = await import(new URL("../src/pages.ts", import.meta.url)).catch(async () => {
  const src = await readFile(new URL("../src/pages.ts", import.meta.url), "utf8");
  return { PAGES: Object.fromEntries([...src.matchAll(/"([^"]+)":\s*"([^"]+\.html)"/g)].map((m) => [m[1], m[2]])) };
});
let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => { if (cond) pass++; else fail++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  " + extra : ""}`); };
const strip = (h) => h.replace(/<html[^>]*>/, "<html>").replace('<link rel="stylesheet" href="/web/assets/rtl-fix.css">\n', "")
  .replace('<link rel="stylesheet" href="/web/assets/plus.css">\n', "")
  .replace('<script src="/web/assets/rtl-fix.js"></script>\n', "");

// Pages with Node-only additions (own Metis key, live typing, sliding toggle, clearer errors): check the additions are there.
const NODE_ONLY = { "/chat": ["typeOut", "movePill", "own_key_rejected"], "/account": ['id="ownkey"', "/auth/provider-key"] };
for (const [route, file] of Object.entries(PAGES)) {
  const [a, b] = await Promise.all([fetch(OLD + route), fetch(NEW + route)]);
  const [ha, hb] = [await a.text(), await b.text()];
  if (NODE_ONLY[route]) { ok(`${route.padEnd(14)} Node page with its additions (${file})`, b.status === 200 && NODE_ONLY[route].every((x) => hb.includes(x))); continue; }
  ok(`${route.padEnd(14)} same page as the Python server (${file})`, a.status === 200 && b.status === 200 && strip(ha) === strip(hb), `${a.status}/${b.status}`);
}
for (const asset of ["/web/assets/site.css", "/web/assets/site.js", "/web/data.json"]) {
  const [a, b] = await Promise.all([fetch(OLD + asset).then((r) => r.text()), fetch(NEW + asset).then((r) => r.text())]);
  ok(`${asset} identical`, a === b && a.length > 0, `${a.length} bytes`);
}
for (const [lang, dir] of [["fa", "rtl"], ["en", "ltr"]]) {
  const h = await (await fetch(NEW + "/chat", { headers: { cookie: `tr_lang=${lang}` } })).text();
  ok(`server sends lang=${lang} dir=${dir} from the saved language`, h.includes(`<html lang="${lang}" dir="${dir}">`));
}
ok("?lang=en wins over the cookie", (await (await fetch(NEW + "/pricing?lang=en", { headers: { cookie: "tr_lang=fa" } })).text()).includes('dir="ltr"'));
ok("unknown page is 404", (await fetch(NEW + "/nope")).status === 404);

const h = await (await fetch(NEW + "/health")).json();
ok("API: /health reaches the Python gateway", h.product === "TakRouter", `live=${h.live} k=${h.k}`);
const r = await (await fetch(NEW + "/v1/router")).json();
ok("API: /v1/router", r.clusters?.length === 8);
const kh = await fetch(NEW + "/v1/khayyam/info");
ok("API: /v1/khayyam/info", kh.status === 200, String(kh.status));
const me = await (await fetch(NEW + "/auth/me")).json();
ok("API: /auth/me (signed out)", me.user === null && me.auth_required === true);
const chat = await fetch(NEW + "/v1/chat/completions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ messages: [{ role: "user", content: "hi" }] }) });
ok("API: chat refused when signed out (401, nothing spent)", chat.status === 401, String(chat.status));
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
