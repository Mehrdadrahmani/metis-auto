# Live latency

Measured through the real gateway and Metis AI, one request at a time, 50 validation messages per row (Sonnet 49 ok, 1 failed). Includes gateway overhead. TakRouter row is a separate fresh run: the first one reused cached calls and was thrown out.

| Setup | n ok | p50 s | p90 s | $ per 1k |
|---|---:|---:|---:|---:|
| gemini-2.5-flash-lite | 50 | 4.38 | 8.12 | 0.420 |
| deepseek-v4-flash | 50 | 4.39 | 8.40 | 0.194 |
| gpt-5.6-luna | 50 | 4.69 | 10.14 | 0.860 |
| takrouter | 50 | 4.84 | 10.60 | 0.257 |
| claude-sonnet-5-5 | 49 | 8.88 | 18.09 | 17.408 |

Live latency ran about twice the stored replay figures. The cause was not investigated.
