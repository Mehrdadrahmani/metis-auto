# WP-15 report: gateway core

FastAPI service `metis.gateway.app`, OpenAI-compatible: `POST /v1/chat/completions`, `GET /health`, `/metrics`, `/v1/traces`. Model `takrouter` or `metis-auto` routes; a concrete id bypasses the router. Pipeline in `gateway/pipeline.py`, breaker in `failover.py`, traces in SQLite without text. MLflow per-request spans were not added to the gateway; `metis.llm.client.complete` still traces live calls. Fault tests: any single model down gives 0 failed requests; all down gives a clean 503 with a trace. Routing equals `router.route` exactly.
