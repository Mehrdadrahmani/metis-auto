# Deck v3 outline (D-135) — HBS NVC order + J.P. Morgan checklist; ≤ 10 min pitch, then technical part

Rules applied: story first; one message per slide (headline = the message); ≥ 30 pt main text; every
number has [n] + references slide; no unsupported claims, no "blue ocean"; small new SVG diagrams
(one idea each); speaker notes carry the context. Sources: `sources/market_global.md`,
`sources/market_iran.md`, `results/final/test_report.md`, `results/khayyam`.

## Pitch (14 slides)
1. **Cover** — tagline: "Every message to the best-value model, from every provider, in Persian." Date, presenter.
2. **Problem** — Iranian teams building chatbots: no direct access (OpenAI/Anthropic/Google block Iran,
   cards sanctioned), pay 15–30% reseller markup, and send every message to one famous model. Cost of
   that habit: 24× the price for a lower pass rate (Sonnet $16.32 vs DeepSeek $0.68 per 1k msgs).
   Diagram: "today" flow, one app → one famous model.
3. **Why now** — 400+ models, 60–80 providers; price per token ÷10 per year; open models 3.3 pts
   behind; 37% of enterprises already use 5+ models; Iran: 32% of adults use AI, National AI Document,
   2026 blackout showed the need for a local gateway with failover.
4. **Solution** — one API + one chat; per message it picks the best-value model; shows model, cost,
   saving; failover. Diagram: 3 steps (ask → match topic → best-value model).
5. **Proof** — sealed test n = 299: 96% cheaper than Sonnet, same quality (+2.0 pts, CI −3.0 to +7.1),
   0 failures in a 10-min outage; Khayyam exam set: routing beats best single model (+0.020 area).
6. **Product** — screenshot (chat shows model/cost/saving) + 4 features (OpenAI-compatible API,
   3 modes, semantic cache, failover). Diagram: small 4-box architecture.
7. **Market** — bottom-up funnel (assumptions shown): SAM Iran B2B ≈ 25k software teams/companies
   × 20% building LLM features × $1,800/yr model spend ≈ **$9M/yr**; our 20% fee pool ≈ $1.8M/yr.
   TAM context: GenAI model spend $28.3B (Gartner 2026), gateway market 27–35% CAGR. Region: 130M
   Persian speakers, MEA GenAI 36% CAGR.
8. **Competition** — matrix: OpenRouter (user picks, 5.5% fee) · learned routers Martian/Not Diamond
   (not for Iran) · cloud routers AWS/Azure (own models only) · Iranian resellers AvalAI/1xAi/Metis
   (no routing) · "always one model". Our edge: learned per-message routing across providers + Persian
   eval data + rial payment. Honest line: always-DeepSeek ties us on chatbot data today.
9. **Business model** — fee on model spend (proposed 20%, in line with 15–30% local markups; global
   5–8%); customer still saves ~95% vs flagship; free starter credit; enterprise self-hosted licence.
   Unit view: avg customer $1,800/yr spend → $360/yr gross profit; LTV vs CAC targets.
10. **Go-to-market** — who: Iranian chatbot builders (startups, Bale/Telegram bot makers, support
    desks); how: free credit + one-line switch, Persian docs/content, dev communities, 3–5 pilot partners;
    then Persian-speaking region.
11. **Milestones** — done: router, gateway, site, sealed test (2026); next 6 months: 30 customer
    interviews, live server in Iran, 5 pilots; 12 months: 100 paying teams; 18 months: region launch.
12. **Team** — names + project roles only (owner: no backgrounds). Mentor.
13. **The ask** (owner D-136: no money amount) — (a) cleaner, more varied data that can be classified
    more easily: chatbot traffic with topic/category labels, harder tasks, true answers; (b) resources to
    build the product: servers in Iran, model credits for evaluation, human labelers, pilot partners.
    What it unlocks: routing gains show up on varied data (Khayyam), a live service.
14. **Thank you** + contact.

## Technical part (6 slides, simplified diagrams)
T1 How routing works (clusters → score table → pick) · T2 Data and evaluation (338k prompts, val 800,
sealed test once) · T3 Results curve (deferral curve, all routers tie on chatbot data) · T4 Why (easy
chatbot data vs Khayyam) · T5 Adding a new model in one step · T6 Gateway (cache, checks, failover).

## Appendix
Detailed stats, cache, judge, full references, financial assumptions.

## Open questions for the owner
- Market assumptions (25k teams, 20%, $1,800/yr, 20% fee) shown as assumptions.
- Keep the technical part at 6 slides?
