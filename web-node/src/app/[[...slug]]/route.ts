import { readFile } from "node:fs/promises";
import path from "node:path";
import type { NextRequest } from "next/server";
import { PAGES } from "@/pages";

// Serves the original TakRouter pages (copied unchanged into ./site) from Node.js, with two additions:
//  1. <html lang dir> is set on the server from the visitor's language (cookie tr_lang or ?lang=),
//     so an English page is LTR from the first paint (the Python server always sent lang="fa" dir="rtl"
//     and let JavaScript flip it, which made English pages flash right-to-left).
//  2. The RTL/LTR add-on (rtl-fix.css + rtl-fix.js) and the layout fixes (plus.css) are linked into every page.
//     The page files are copies of metis-auto/web; only chat.html and account.html carry Node-only additions.
const SITE = path.join(process.cwd(), "site");
const NO_CACHE = "no-cache, no-store, must-revalidate"; // as on the Python server: browsers always load the current site

export async function GET(request: NextRequest, ctx: RouteContext<"/[[...slug]]">) {
  const { slug } = await ctx.params;
  const route = "/" + (slug ?? []).join("/");
  const file = PAGES[route.replace(/\/$/, "") || "/"];
  if (!file) return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain" } });

  const q = request.nextUrl.searchParams.get("lang");
  const saved = request.cookies.get("tr_lang")?.value;
  const lang = q === "en" || q === "fa" ? q : saved === "en" || saved === "fa" ? saved : "fa";
  const dir = lang === "fa" ? "rtl" : "ltr";

  let html = await readFile(path.join(SITE, file), "utf8");
  // Only pages that have both languages (they load site.js); a one-language page (/results) keeps its own tag.
  if (html.includes("/web/assets/site.js")) html = html.replace(/<html[^>]*>/, `<html lang="${lang}" dir="${dir}">`);
  html = html.replace("</head>", `<link rel="stylesheet" href="/web/assets/rtl-fix.css">\n<link rel="stylesheet" href="/web/assets/plus.css">\n</head>`);
  html = html.replace(/<\/body>(?![\s\S]*<\/body>)/, `<script src="/web/assets/rtl-fix.js"></script>\n</body>`);
  return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": NO_CACHE } });
}
