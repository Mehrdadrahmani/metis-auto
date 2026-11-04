// The same routes as the Python server (metis-auto/src/metis/gateway/app.py, PAGES).
export const PAGES: Record<string, string> = {
  "/": "home.html",
  "/chat": "chat.html",
  "/compare": "compare.html",
  "/learn": "learn.html",
  "/docs": "docs.html",
  "/dashboard": "dashboard.html",
  "/pricing": "pricing.html",
  "/how": "how.html",
  "/login": "login.html",
  "/account": "account.html",
  "/models": "models.html",
  "/results": "index.html",
  "/khayyam": "khayyam.html",
  "/khayyam/chat": "khayyam_chat.html",
};

// Everything the pages call on the backend goes to the Python gateway unchanged.
export const API_PREFIXES = ["/auth", "/v1", "/admin", "/health", "/metrics", "/docs-api"];
