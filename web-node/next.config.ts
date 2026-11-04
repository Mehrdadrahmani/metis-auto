import type { NextConfig } from "next";

// Node.js serves the pages; the Python gateway (FastAPI) stays the backend for every API call.
const GATEWAY = process.env.TAKROUTER_GATEWAY ?? "http://127.0.0.1:8000";
const API = ["/auth/:path*", "/v1/:path*", "/admin/:path*", "/health", "/metrics"];

const nextConfig: NextConfig = {
  cacheComponents: true,
  // No gzip here: it holds back streamed answers (server-sent events) until they are complete.
  // In production the web server in front (Caddy) compresses the pages and passes streams straight through.
  compress: false,
  partialPrefetching: true,
  async rewrites() {
    // Checked before the page route, so API paths always reach the gateway.
    return { beforeFiles: API.map((source) => ({ source, destination: `${GATEWAY}${source}` })), afterFiles: [], fallback: [] };
  },
  async headers() {
    // As on the Python server: browsers always load the current files.
    return [{ source: "/web/:path*", headers: [{ key: "cache-control", value: "no-cache, no-store, must-revalidate" }] }];
  },
};

export default nextConfig;
