# TakRouter on Node.js (Next.js 16)

The complete TakRouter website served by **Node.js** instead of Python, looking exactly like the original,
with better right-to-left / left-to-right handling. The Python gateway (FastAPI) stays the backend.

The 14 pages in `site/` started as copies of `../web/*.html` (the original site, which stays as it was);
`public/web/` holds the same `site.css`, `site.js` and `data.json`. `chat.html` and `account.html` carry the
Node-only additions listed below.

## Run

```bash
# 1. the Python gateway (in the repository root)
TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000

# 2. the website on Node.js (in web-node/)
npm ci
npm run build && npx next start -p 3001        # open http://localhost:3001
```

Another gateway address: `TAKROUTER_GATEWAY=http://host:port npm run build`.

## How it works

| Part | File |
|---|---|
| The 14 pages, same routes as the Python server (`/`, `/chat`, `/compare`, `/learn`, `/docs`, `/dashboard`, `/pricing`, `/how`, `/login`, `/account`, `/models`, `/results`, `/khayyam`, `/khayyam/chat`) | `src/app/[[...slug]]/route.ts`, `src/pages.ts`, `site/*.html` |
| API calls (`/auth`, `/v1`, `/admin`, `/health`, `/metrics`) passed to the Python gateway; the sign-in cookie passes through | `next.config.ts` |
| RTL/LTR add-on, linked into every page | `public/web/assets/rtl-fix.css`, `rtl-fix.js` |

## What Node.js adds over the Python-served site

1. **The right direction from the first paint.** The Python server always sent `lang="fa" dir="rtl"` and JavaScript
   flipped English pages afterwards. Node sets `lang`/`dir` on the server from the saved language (cookie `tr_lang`,
   or `?lang=`). One-language pages (`/results`) keep their own tag.
2. **Each message finds its own direction** (`unicode-bidi: plaintext`): an English message or answer in the
   Persian interface is laid out left-to-right (`Hello, how are you?`, not `?Hello, how are you`), and the other way round.
3. **Left-to-right runs inside Persian are isolated** (`<bdi dir="ltr">`, also for answers that arrive later):
   `$0.0007` stays `$0.0007`, not `0.0007$`. Code stays left-to-right.
4. **Typing** English into the Persian chat box (or Persian into the English one) is laid out correctly.

## Node-only additions (2026-11-04)

| What | Where |
|---|---|
| **Your own Metis AI key** on /account: paste, save and test, switch on/off, remove. Stored encrypted by the gateway; only the last 4 characters are shown. Chats and comparisons then run on the user's key: their TakRouter credit and our budget are not used. A refused key gives a clear message. | `site/account.html`, gateway `metis-auto/src/metis/gateway/{auth,app,pipeline,providers}.py` |
| **Live typing**: answers type themselves out (≈2 s, click to skip, off with "reduce motion"); the waiting dots bounce | `site/chat.html` |
| **Sliding mode toggle** (Eco / Balanced / Best) | `site/chat.html` |
| **Clearer errors**: "server cannot reach Metis AI" vs. "no model answered" vs. "your key was refused" | `site/chat.html`, gateway 503 now names failure kinds |
| **Header fits** at laptop widths (English "Sign in" was cut off at 1280 px); menu button below 1180 px; chat page header no longer gets the score-bar style (which clipped the account menu) | `public/web/assets/plus.css` |

## Tests ($0, no paid calls)

```bash
node scripts/check.mjs            # 26 checks: every page is the original file, assets identical, lang/dir, API pass-through
SITE=... EMAIL=... PASSWORD=... node scripts/byok-ui.mjs   # 23 checks of the additions, against a MOCK gateway
node scripts/visual-compare.mjs   # 31 checks (since the header fix, pages differ from the Python site in the top 65 px only): every page in fa and en pixel-compared with the Python site,
                                  # plus the RTL cases on the real chat page (screenshots/)
```

Last run: 26/26 and 31/31. Every page matched the Python site (0.00–0.01% of pixels differ; the Khayyam page
shows a random sample question). RTL cases on the chat page, Python site → Node site: English message BAD → ok,
English answer BAD → ok, price inside Persian BAD → ok.

## Not tested

- Signing in and a real (paid) chat answer through the Node site.
- Admin actions (adding a model) through the Node site.
