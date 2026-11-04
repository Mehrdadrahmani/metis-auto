"""Deck v3 generator (D-135, D-136). Writes slides/*.html and deck.json. Run: python3 deck/v2/project/build_v3.py
Public numbers + our aggregates only. Sources: deck/v2/sources/*.md (local), results/final/test_report.md."""
import json
import pathlib

D = pathlib.Path(__file__).parent
INK, MUTE, PUR, BLUE, PINK, GREEN = "#17132b", "#6b6684", "#7a22e0", "#3366ff", "#e0336e", "#0f9d6e"
FONT = "font-family:'Inter', Arial, sans-serif"
CARD = "background:#ffffff;border:1px solid #e8e6f2;border-radius:28px;box-shadow:0 12px 34px rgba(60,40,140,0.08)"
BG = {"a": "radial-gradient(circle at 10% 90%, #efe4ff, #fbfaff 45%)", "b": "#fbfaff",
      "c": "radial-gradient(circle at 90% 10%, #e4ecff, #fbfaff 45%)"}


def r(n):
    return f'<span style="color:{PUR};font-size:24px;font-weight:600">[{n}]</span>'


def slide(sid, tag, title, body, notes, refs="", bg="b", gap=40):
    foot = (f'<p style="position:absolute;left:128px;right:128px;bottom:64px;font-size:24px;color:#7d7893;'
            f'line-height:1.35">{refs}</p>') if refs else ""
    pill = (f'<p style="align-self:flex-start;font-size:24px;font-weight:600;color:{PUR};background:#f1e9ff;'
            f'padding:8px 20px;border-radius:999px">{tag}</p>') if tag else ""
    h = f'<h2 style="font-size:58px;font-weight:800;line-height:1.12;letter-spacing:-1px">{title}</h2>' if title else ""
    html = (f'<section id="{sid}" data-transition="fade" style="background:{BG[bg]};color:{INK};{FONT};'
            f'padding:96px 128px 150px;display:flex;flex-direction:column;gap:{gap}px">\n{pill}\n{h}\n{body}\n{foot}\n'
            f'<aside>{notes}</aside>\n</section>\n')
    (D / "slides" / f"{sid}.html").write_text(html)
    return sid


def row(*items, gap=28):
    return f'<div style="display:flex;flex-direction:row;gap:{gap}px;align-items:stretch">{"".join(items)}</div>'


def card(big, text, color=BLUE, size=96):
    return (f'<div style="flex:1;{CARD};padding:40px 36px;display:flex;flex-direction:column;gap:14px">'
            f'<p style="font-size:{size}px;font-weight:800;line-height:1;letter-spacing:-2px;color:{color}">{big}</p>'
            f'<p style="font-size:30px;font-weight:600;line-height:1.35">{text}</p></div>')


def textcard(head, text, color=PUR):
    return (f'<div style="flex:1;{CARD};padding:36px 36px;display:flex;flex-direction:column;gap:12px">'
            f'<p style="font-size:34px;font-weight:800;color:{color}">{head}</p>'
            f'<p style="font-size:30px;line-height:1.4;color:{INK}">{text}</p></div>')


def para(t, size=32, color=INK, w=600):
    return f'<p style="font-size:{size}px;font-weight:{w};line-height:1.4;color:{color}">{t}</p>'


def svg_flow(boxes, w=1660, h=300, colors=None, sub=None, arrow_labels=None):
    """Horizontal chain of rounded boxes with arrows. boxes: list of (title, subtitle)."""
    n = len(boxes)
    gapx = 70
    bw = (w - gapx * (n - 1)) / n
    pal = colors or ["#dae8fc"] * n
    strokes = {"#dae8fc": "#6c8ebf", "#ffe6cc": "#d79b00", "#d5e8d4": "#82b366", "#f5f5f5": "#666666",
               "#fff2cc": "#d6b656", "#efe4ff": "#9b6ad6"}
    label = " then ".join(t + ": " + s_.replace("|", " ") for t, s_ in boxes)
    out = [f'<svg aria-label="{label}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="display:block">',
           '<defs><marker id="ah" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">'
           '<path d="M0,0 L12,6 L0,12 z" fill="#17132b"/></marker></defs>']
    for i, (t, s) in enumerate(boxes):
        x = i * (bw + gapx)
        f = pal[i]
        out.append(f'<rect x="{x+2}" y="20" width="{bw-4}" height="{h-40}" rx="26" fill="{f}" stroke="{strokes.get(f,"#666")}" stroke-width="3"/>')
        out.append(f'<text x="{x+bw/2}" y="{h/2-12}" text-anchor="middle" font-family="Inter, Arial" font-size="36" font-weight="800" fill="#17132b">{t}</text>')
        for j, line in enumerate(s.split("|")):
            out.append(f'<text x="{x+bw/2}" y="{h/2+34+j*36}" text-anchor="middle" font-family="Inter, Arial" font-size="26" fill="#3d3856">{line}</text>')
        if i < n - 1:
            out.append(f'<line x1="{x+bw+6}" y1="{h/2}" x2="{x+bw+gapx-10}" y2="{h/2}" stroke="#17132b" stroke-width="3" marker-end="url(#ah)"/>')
    out.append("</svg>")
    return "".join(out)


S = []
# ---------- PITCH ----------
S.append(slide("cover", "Smart LLM gateway for Persian AI products", "",
    f'<h1 style="font-size:170px;font-weight:800;line-height:1;letter-spacing:-5px;background:linear-gradient(90deg,#3366ff,#9933ff 55%,#ff3366);background-clip:text;-webkit-text-fill-color:transparent">TakRouter</h1>'
    f'<p style="font-size:60px;font-weight:800;line-height:1.15;letter-spacing:-1px">Every message goes to the <span style="color:{PUR}">best-value model</span>, from every provider.</p>'
    + para("Team Synapse · Rahnema College 2026 · Presenter: Mehrdad Rahmani · November 2026", 30, MUTE, 500),
    "Open with the one-line promise. TakRouter is a gateway that Persian chatbots and apps call instead of one AI model. "
    "For every message it picks the model that gives a good answer for the lowest price, from many providers, and it keeps working "
    "when one provider fails. Then go straight to the problem.", bg="a", gap=36))

S.append(slide("problem", "Problem", "Persian AI products overpay for every message",
    row(textcard("1 · No direct access", f"OpenAI, Anthropic and Google do not serve Iran; foreign cards are blocked. Teams buy through resellers at <b>+15–30%</b> {r(3)}", PINK),
        textcard("2 · One famous model for everything", f"Easy and hard messages go to the same expensive model. Nobody can test 400+ models {r(4)}", PINK),
        textcard("3 · One provider, one point of failure", f"In 2026 Iran lost the internet for ~90 days {r(5)}; a single provider link stops the product", PINK))
    + row(card("24×", f"the price of Claude Sonnet vs DeepSeek on our real chatbot traffic, and Sonnet passed <b>fewer</b> answers (64.9% vs 68.6%) {r(1)}", PINK, 110)),
    "Who has the pain: Iranian teams that run chatbots and AI features, for support, education, shops and bots on Bale or Telegram. "
    "Three problems. First, access: the big providers do not serve Iran and cards are sanctioned, so teams buy through local resellers that add 15 to 30 percent. "
    "Second, habit: they send every message to one famous model, even a greeting. They cannot test hundreds of models themselves. "
    "Third, reliability: one provider link is a single point of failure, and this year showed how fragile the connection is. "
    "The cost of the habit, measured on 299 real chatbot messages: Claude Sonnet cost 24 times DeepSeek and passed fewer answers.",
    f"[1] Our sealed test, n = 299, AI judge: Sonnet $16.32 vs DeepSeek $0.68 per 1,000 messages · [3] 1xai.ir pricing, Oct 2026; provider supported-country pages · "
    f"[4] TechCrunch, 26 May 2026 (OpenRouter 400+ models) · [5] IPinfo, Apr 2026; Shafaq News, 26 May 2026"))

S.append(slide("whynow", "Why now", "More models, lower prices: choosing per message now pays",
    row(card("400+", f"models from 60–80 providers in one catalog {r(4)}", BLUE),
        card("÷10", f"price per token every year at the same quality {r(6)}", GREEN),
        card("3.3", f"points: gap between the best open and best closed model {r(7)}", PUR))
    + row(card("37%", f"of enterprises already use 5 or more models {r(8)}", BLUE),
          card("32%", f"of Iranian adults use AI tools; 54% of ages 15–29 {r(9)}", GREEN),
          card("$28B", f"world spend on GenAI models in 2026, +117% in a year {r(10)}", PUR)),
    "Why this has to be solved now. The number of good models exploded, prices fall about ten times a year, and open models like DeepSeek are only a few points "
    "behind the best closed ones. So the choice of model per message is now worth real money, and big companies already mix several models. "
    "In Iran, a third of adults and more than half of young people already use AI tools, so Persian AI products are growing fast, and they all face the access problem.",
    f"[4] TechCrunch 26 May 2026; Sacra 2026 · [6] a16z, LLMflation, Nov 2024 · [7] Stanford AI Index 2026 · [8] a16z CIO survey, Jun 2025 (n = 100) · "
    f"[9] ISPA survey, Sep 2025 (n = 1,502) · [10] Gartner, 16 Sep 2026", bg="c", gap=30))

S.append(slide("solution", "Solution", "One address. The best-value model for each message.",
    svg_flow([("Your app", "sends a message|to one address"), ("TakRouter", "finds the topic and|the best-value model"),
              ("The answer", "plus the model, the cost|and the saving")],
             colors=["#dae8fc", "#efe4ff", "#d5e8d4"], h=280)
    + row(textcard("Cheaper", "Easy messages go to strong low-cost models; only hard topics pay for premium."),
          textcard("Reliable", "If a provider fails, the next model answers. Repeated questions come from the cache."),
          textcard("Simple", "OpenAI-compatible: change one line. New models join without retraining.")),
    "The solution in one sentence: one address that sends each message to the model with the best quality for its price. "
    "The app sends the message as usual. TakRouter recognises the kind of question and picks the model that does best on that kind of question for the price. "
    "The app gets the answer and sees which model answered, what it cost and how much it saved. Behind it: failover, a semantic cache, and new models join in one step.",
    bg="a"))

S.append(slide("proof", "Proof", "Measured on 299 real Persian chatbot messages",
    row(card("96%", f"cheaper than always using Claude Sonnet {r(1)}", BLUE, 110),
        card("=", f"quality: not lower than Sonnet (+2.0 pts, CI −3.0 to +7.1) {r(1)}", GREEN, 110),
        card("0", f"failed requests in a simulated 10-minute provider outage {r(1)}", PINK, 110))
    + para(f"On exam questions with true answers, the best model changes by subject, and routing beats every single model {r(2)}", 32, INK, 600),
    "Our evidence. We froze the router, then opened a sealed test set once: 299 real Persian chatbot messages. "
    "TakRouter cost 96% less than always using Claude Sonnet, and quality was not lower; the interval includes zero, so we claim equal, not better. "
    "In a simulated ten-minute outage of the main provider, no request failed. On the Khayyam exam benchmark with true answers, "
    "the best model changes by subject and routing beat the best single model. Honest note: on easy chatbot traffic, always using DeepSeek is as good; "
    "the gain grows with harder, more varied traffic. That is why our ask is about data.",
    "[1] Our sealed test, n = 299, opened once, session bootstrap 10,000; outage replayed from cached calls · [2] Our Khayyam benchmark, n = 1,100, +0.020 area (95% CI +0.001 to +0.044)",
    bg="c"))

S.append(slide("product", "Product", "Live today: a chat for people and an API for developers",
    row(f'<div style="flex:1.25;{CARD};padding:16px;display:flex;align-items:center"><img src="/_blob/6909816369246c77827bf3feabe98efe" alt="TakRouter chat in Persian: the answer shows the model, its cost, the time and the saving against Claude Sonnet" style="width:100%;border-radius:18px"></div>',
        f'<div style="flex:1;display:flex;flex-direction:column;gap:22px">'
        + textcard("OpenAI-compatible API", "Change one line of code.", BLUE)
        + textcard("3 modes", "Economy · Balanced · Best quality", PUR)
        + textcard("Every answer is transparent", "Model, cost, time and saving.", GREEN) + "</div>"),
    "This is the working product, Persian and English. The chat shows on every answer which model answered, its cost and the saving versus Claude Sonnet. "
    "Developers call the same router through an OpenAI-compatible API, so switching is one line. Three modes let the customer trade cost for quality. "
    "Under the hood: semantic cache, answer checks with escalation to a stronger model, failover and streaming. Roadmap on the milestones slide.",
    bg="b", gap=32))

S.append(slide("market", "Market", "A fast-growing market, sized from the bottom up",
    svg_flow([("TAM  $28B", "world GenAI model|spend, 2026 [10]"), ("SAM  ~$9M / yr", "Iranian teams'|model spend"), ("SOM  ~$0.9M / yr", "500 teams|in 3 years")],
             h=260, colors=["#dae8fc", "#efe4ff", "#d5e8d4"])
    + row(textcard("How we sized SAM", f"~25,000 Iranian software teams and companies {r(11)} × 20% building AI features × $1,800 model spend a year (assumptions)", BLUE),
          textcard("Where it goes", f"Gateway/router market: $0.88B → $3.95B by 2031, 35% a year {r(12)}. Next: 130M Persian speakers in the region.", GREEN)),
    "Market size. Top down, the world spends about 28 billion dollars on generative AI models this year. Gateways and routers are a market of their own, growing about 35% a year. "
    "Bottom up, which is what counts for us: Iran has about 19,000 app teams and 10,000 knowledge-based companies; we assume about 25,000 teams overall, "
    "one in five building AI features, each spending about 1,800 dollars a year on models. That is about 9 million dollars a year of model spend in Iran today, growing fast. "
    "Our three-year goal is 500 teams, about 0.9 million dollars of spend through TakRouter. These are assumptions, written down so they can be challenged.",
    "[10] Gartner, 16 Sep 2026 · [11] Aftab News 1405 (19,000 app teams); Farhikhtegan, Oct 2025 (~10,013 knowledge-based companies) · [12] Knowledge Sourcing Intelligence, 2026 (estimate)",
    bg="c", gap=30))

TD = "text-align:center"
S.append(slide("competition", "Competition", "Many gateways; few choose the model for you",
    f'<table style="font-size:28px;{FONT};color:{INK};background:#ffffff">'
    f'<tr style="background:#f3eefe"><th style="width:30%">Option</th><th style="{TD}">Picks the model per message</th><th style="{TD}">Many providers</th><th style="{TD}">Works from Iran, rial</th><th style="{TD}">Failover</th></tr>'
    f'<tr style="background:#efe7ff"><td><b>TakRouter</b></td><td style="{TD}"><b>Yes, learned</b></td><td style="{TD}"><b>Yes</b></td><td style="{TD}"><b>Yes</b></td><td style="{TD}"><b>Yes</b></td></tr>'
    f'<tr><td>Iranian resellers (AvalAI, 1xAi, Metis AI)</td><td style="{TD}">No, you choose</td><td style="{TD}">Yes</td><td style="{TD}">Yes</td><td style="{TD}">Partly</td></tr>'
    f'<tr><td>OpenRouter, LiteLLM, Portkey</td><td style="{TD}">Mostly you choose</td><td style="{TD}">Yes</td><td style="{TD}">No</td><td style="{TD}">Yes</td></tr>'
    f'<tr><td>Martian, Not Diamond</td><td style="{TD}">Yes, learned</td><td style="{TD}">Yes</td><td style="{TD}">No</td><td style="{TD}">Yes</td></tr>'
    f'<tr><td>AWS, Azure, GPT-5 routers</td><td style="{TD}">Yes, own models only</td><td style="{TD}">No</td><td style="{TD}">No</td><td style="{TD}">—</td></tr>'
    f'</table>'
    + para(f"Why not copied easily: a Persian evaluation set and a per-topic score table built from real traffic; new models join in one step. Global players move fast: OpenRouter raised $113M {r(4)}.", 28, MUTE, 500),
    "No blue ocean. Iranian resellers give access and rial payment but leave the model choice to you. Global gateways like OpenRouter are big and growing, "
    "but you choose the model and they do not serve Iran. Learned routers like Martian and Not Diamond are closest to us but are not available here and not tuned to Persian. "
    "Cloud routers only pick inside one company's models. Our edge is the combination: learned per-message routing across providers, a Persian evaluation set, rial payment and failover. "
    "Our toughest honest competitor today is simply always using DeepSeek; we win when traffic is varied.",
    "[4] TechCrunch, 26 May 2026 · company websites and docs, Oct–Nov 2026 (avalai.ir, 1xai.ir, metisai.ir, openrouter.ai, aws.amazon.com/bedrock)", gap=30))

S.append(slide("business", "Business model", "We earn a fee on every message; the customer still saves",
    row(card("20%", f"fee on the model price, paid in rial; local resellers add 15–30% {r(3)}", PUR),
        card("95%", f"still cheaper than always-Sonnet after our fee {r(1)}", GREEN),
        card("$360", "gross profit per team per year (assumed $1,800 model spend)", BLUE))
    + row(textcard("Free start", "Starter credit; the saving is shown on every answer, so the value is visible."),
          textcard("Enterprise", "Self-hosted licence and support for large companies and data-sensitive customers.")),
    "How we make money. The customer pays the model price plus a 20% fee, in rial. That is inside the range local resellers charge today, and global gateways charge 5 to 8 percent. "
    "Because routing moves most messages to strong low-cost models, the customer still pays about 95% less than with always-Sonnet, even after our fee. "
    "With the assumed 1,800 dollars of model spend, one team brings about 360 dollars a year. Later: an enterprise self-hosted licence.",
    "[1] Our sealed test: routed $0.69 per 1,000 messages + 20% = $0.83 vs Sonnet $16.32 · [3] 1xai.ir pricing, Oct 2026 · global take rates 5–8%: Sacra 2026, Cloudflare docs", bg="a"))

S.append(slide("gtm", "Go-to-market", "Start with Iranian chatbot builders, then the region",
    svg_flow([("Who", "teams with chatbots:|support, schools, shops,|Bale and Telegram bots"), ("How we reach them", "Persian docs and content,|developer communities,|pilot partners"),
              ("Why they switch", "one-line change,|free credit, saving|shown on every answer"), ("Then", "Persian-speaking|region and|enterprise")],
             h=320, colors=["#dae8fc", "#efe4ff", "#d5e8d4", "#fff2cc"]),
    "What we sell: a gateway with routing, paid per message. To whom: Iranian teams that already run chatbots or AI features, the ones paying resellers today. "
    "How we reach them: Persian documentation and content, developer communities, and a small number of pilot partners whose traffic we study together. "
    "Why they switch: it is a one-line change, there is free credit to try, and the saving is visible on every answer. Then we grow to the Persian-speaking region and to enterprise licences.",
    bg="c"))

S.append(slide("milestones", "Milestones", "Built and measured; next, live with partners",
    svg_flow([("Done · 2026", "data pipeline, router,|sealed test, gateway,|website and API"), ("Next 6 months", "30 customer interviews,|live server in Iran,|3–5 pilot partners"),
              ("12 months", "first paying teams,|human labels,|more models"), ("18+ months", "Persian-speaking|region,|enterprise")],
             h=320, colors=["#d5e8d4", "#efe4ff", "#dae8fc", "#fff2cc"]),
    "What we achieved: the full data pipeline on 338 thousand real prompts, the router, a sealed test opened once, the gateway with cache and failover, the website and the API. "
    "Next six months: talk to thirty potential customers to measure demand, which we do not have yet, run the service on a server in Iran, and start three to five pilots. "
    "Within a year: first paying teams, human labels for quality, more models. After that: the region and enterprise.", bg="a"))

S.append(slide("team", "Team", "Team Synapse built TakRouter end to end",
    row(*[f'<div style="flex:1;{CARD};padding:40px 24px;display:flex;flex-direction:column;align-items:center;gap:18px">'
          f'<div style="width:120px;height:120px;border-radius:60px;background:linear-gradient(135deg,#3366ff,#9933ff);color:#fff;font-size:44px;font-weight:800;display:flex;align-items:center;justify-content:center">{i}</div>'
          f'<p style="font-size:32px;font-weight:700;text-align:center">{n}</p></div>'
          for i, n in [("MR", "Mehrdad Rahmani"), ("FN", "Farzaneh Nademi"), ("KK", "Kimia Komeili"), ("RG", "Roham Ghlabi")]])
    + para(f"Mentor: Peyman Naseri · Rahnema College 2026 · Built and measured on 338,325 real prompts {r(1)}", 30, MUTE, 500),
    "Why us: we already did the hard part. We built the router, the gateway and the product, and we measured them honestly on real Persian traffic with a sealed test. "
    "We know the local problem first hand: access, payment and outages.", "[1] Our evaluation report, results/final/test_report.md", bg="c"))

S.append(slide("ask", "The ask", "Help us prove routing on richer data",
    row(textcard("1 · Cleaner, more varied data", "Chatbot traffic with topic labels, harder tasks and true answers, so messages can be classified easily and the router can learn where models differ.", BLUE),
        textcard("2 · Resources to build the product", "Servers in Iran, model credits for evaluation, human labelers, and 3–5 pilot partners.", PUR))
    + para(f"Why it matters: on easy chatbot data the cheapest good model wins almost everywhere; on varied exam data routing shows a real gain {r(2)}.", 30, INK, 600),
    "Our ask is not money today. First, data: cleaner and more varied traffic with topic labels and known answers. On our chatbot data the questions were easy and similar, "
    "so one cheap model won almost everywhere; on the Khayyam exam set, where subjects differ, routing showed a real gain. Better data lets us show the value clearly. "
    "Second, resources to build the product: servers in Iran, model credits for evaluation, human labelers, and a few pilot partners. "
    "With these, the next milestone is a live service with measured gains for real customers.",
    "[2] Our Khayyam benchmark, n = 1,100, true answers: +0.020 area (95% CI +0.001 to +0.044)", bg="a"))

S.append(slide("thanks", "", "",
    f'<h1 style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-4px;background:linear-gradient(90deg,#3366ff,#9933ff 55%,#ff3366);background-clip:text;-webkit-text-fill-color:transparent">Thank you</h1>'
    + para("TakRouter · Team Synapse · github.com/Mehrdadrahmani/metis-auto", 34, MUTE, 500)
    + para("Technical part and backup slides follow.", 30, MUTE, 500),
    "Thank the audience. Offer the technical part next, or jump to questions.", bg="a"))

# ---------- TECHNICAL ----------
S.append(slide("techdiv", "Technical part", "How the router works and how we measured it",
    para("1 · How it chooses · 2 · Data and evaluation · 3 · Results · 4 · Why, and what's next · 5 · Adding a model · 6 · The gateway", 34, MUTE, 500),
    "Technical part: six short slides. Formulas and full diagrams are in the backup.", bg="c"))

S.append(slide("t1how", "T1 · How it chooses", "Topic first, then the best quality for the price",
    svg_flow([("1 · Embed", "turn the message|into a vector"), ("2 · Topic", "nearest of|8 topic centres"), ("3 · Score table", "each model's error|on that topic"),
              ("4 · Pick", "lowest error|+ λ × cost")], h=300, colors=["#dae8fc", "#dae8fc", "#efe4ff", "#d5e8d4"])
    + row(textcard("Topics from user text only", "8 topics learned from 209,109 unlabeled prompts (K-means)."),
          textcard("Score table from 800 judged prompts", "Each model's error per topic, measured once on validation.")),
    "How the router chooses, in four steps. It turns the message into a vector, finds the nearest of eight topic centres, looks up each model's error on that topic, "
    "and picks the model with the lowest error plus lambda times cost. Lambda sets the balance; we chose 0.515 on validation. "
    "The topics come from user text only; the score table comes from 800 validation prompts judged by an AI judge. This is UniRoute, from Google, published at ICLR 2026.",
    bg="b"))

S.append(slide("t2data", "T2 · Data and evaluation", "Real traffic, a sealed test opened once",
    svg_flow([("338,325", "real chatbot prompts"), ("209,109", "unlabeled: learn|the 8 topics"), ("800", "validation, judged:|score table, λ, K"), ("300", "sealed test,|opened once")],
             h=300, colors=["#f5f5f5", "#dae8fc", "#ffe6cc", "#fff2cc"])
    + para("Golden rules: no choice made with test data · every model and judge call cached · seeds recorded · prompts over 20,000 characters excluded.", 30, INK, 500),
    "Our data: 338 thousand real prompts from Persian chatbots. The large unlabeled part only teaches the topics. 800 validation prompts were answered by all four models "
    "and judged; every choice, the number of topics, lambda, thresholds, was made there. The 300-prompt test set stayed sealed until the router was frozen and was opened once.",
    bg="c"))

S.append(slide("t3results", "T3 · Results", "Every learned router ties on chatbot data",
    f'<div style="{CARD};padding:16px;display:flex;justify-content:center"><img src="/_blob/61ec7699a96d4c6c5ae9ed4eff2670a6" alt="Area under the deferral curve per router on the sealed test and cost to reach the best single model" style="height:560px"></div>',
    "On the sealed test every learned router reaches about the same area under the cost-quality curve, 0.68 to 0.70, and all beat always-cheapest. "
    "Each reaches the best single model's quality at about 4% of Sonnet's cost. So on this data clustering did not beat simpler routers; the next slide shows why.",
    "[1] Sealed test, n = 299, one run, session bootstrap; every router-vs-router interval includes 0", gap=28))

S.append(slide("t4why", "T4 · Why, and what's next", "Varied data is where routing pays",
    f'<div style="{CARD};padding:16px;display:flex;justify-content:center"><img src="/_blob/1f37d77db48ab08e713ec0960f82d493" alt="Winner per topic: on chatbot data only DeepSeek and Sonnet win; on Khayyam different models win per subject" style="height:540px"></div>',
    "On our chatbot data only two models ever win a topic, and once cost counts DeepSeek wins almost everywhere. On Khayyam exam questions the winner changes by subject, "
    "and routing showed a real gain. This is the reason for our ask: cleaner, more varied, labeled data.",
    "[14] Validation, n = 798, AI judge · [2] Khayyam, n = 1,100, true answers", bg="c", gap=28))

S.append(slide("t5newmodel", "T5 · Adding a model", "A new model joins in one step, no retraining",
    svg_flow([("New model", "answers the 800|validation prompts"), ("New row", "its error per topic|in the score table"), ("Live", "the router can pick it|right away")],
             h=300, colors=["#dae8fc", "#efe4ff", "#d5e8d4"])
    + para("Holdout check: adding Gemini from its validation row moved the test area from 0.680 to 0.686.", 30, INK, 600),
    "Adding a model does not need retraining. The new model answers the validation prompts once, we compute its error per topic, and it becomes one new row in the table. "
    "We tested this by holding Gemini out and adding it back from its row only; the result improved slightly.", "[1] Sealed test, holdout demo (results/holdout_demo.md)"))

S.append(slide("t6gateway", "T6 · The gateway", "Around the router: cache, checks and failover",
    svg_flow([("Request", "OpenAI-compatible"), ("Cache", "same question?|answer at once"), ("Router", "best-value|model"), ("Check", "weak answer?|escalate"), ("Failover", "provider down?|next model")],
             h=300, colors=["#dae8fc", "#f5f5f5", "#efe4ff", "#fff2cc", "#d5e8d4"])
    + para("Replay on the test set: 0.3% escalated; 10-minute DeepSeek outage → 0 failed requests, 21 failovers.", 30, INK, 600),
    "The gateway around the router: a semantic cache answers repeated questions, a check escalates weak answers to a stronger model, and failover moves to the next model "
    "when a provider is down. All requests are traced for cost and latency.", "[1] Sealed test replay, simulated from cached calls", bg="c"))

# ---------- BACKUP ----------
S.append(slide("bassume", "Backup · Market assumptions", "How the market numbers were built",
    row(textcard("SAM ≈ $9M/yr", "25,000 teams × 20% building AI × $1,800 model spend/yr. Teams: 19,000 app teams + ~10,000 knowledge-based companies, overlap assumed.", BLUE),
        textcard("SOM ≈ $0.9M/yr", "500 paying teams in 3 years × $1,800. Our revenue = 20% fee ≈ $180k/yr.", GREEN),
        textcard("To verify", "No public count of Iranian API buyers exists; the 30 customer interviews will test the 20% and the $1,800.", PINK)),
    "Every market number in the pitch is an assumption built from public counts; these are the inputs to challenge.",
    "Aftab News 1405; Farhikhtegan Oct 2025; Gartner 16 Sep 2026; DataReportal Digital 2026 Iran (73.8M internet users)"))

S.append(slide("brefs", "Backup · References", "Sources",
    f'<div style="font-size:24px;line-height:1.45;display:grid;grid-template-columns:1fr 1fr;gap:4px 56px;color:{INK}">'
    "<p>[1] TakRouter sealed test, n = 299, results/final/test_report.md, Nov 2026</p>"
    "<p>[2] TakRouter Khayyam benchmark, n = 1,100, results/khayyam, Nov 2026</p>"
    "<p>[3] 1xai.ir pricing (markup 15–30%), Oct 2026; OpenAI, Anthropic, Google supported-country pages</p>"
    "<p>[4] TechCrunch, “OpenRouter more than doubles valuation to $1.3B”, 26 May 2026; Sacra, OpenRouter, 2026</p>"
    "<p>[5] IPinfo, Measuring Iran's internet collapse, Apr 2026; Shafaq News, 26 May 2026</p>"
    "<p>[6] a16z, “LLMflation”, Nov 2024</p>"
    "<p>[7] Stanford HAI, AI Index Report 2026</p>"
    "<p>[8] a16z, Enterprise CIO survey, Jun 2025 (n = 100)</p>"
    "<p>[9] ISPA survey via Zoomit, 17 Sep 2025 (n = 1,502)</p>"
    "<p>[10] Gartner, AI spending forecast, 16 Sep 2026</p>"
    "<p>[11] Aftab News, app industry, 1405; Farhikhtegan, Oct 2025</p>"
    "<p>[12] Knowledge Sourcing Intelligence, AI model routing and gateway market, 2026 (estimate)</p>"
    "<p>[13] Lu et al., UniRoute, arXiv 2502.08773, ICLR 2026</p>"
    "<p>[14] TakRouter validation, n = 798, results/fingerprints.md</p>"
    "</div>",
    "All sources, by number. Market estimates are marked as estimates.", gap=28))

ORDER = S + ["t2psi", "t3rule", "t6curves", "t1clusters", "bstats", "bjudge", "bcache"]
ORDER = ORDER[:-9] + ORDER[-7:] + ORDER[-9:-7]  # backups, then bassume, brefs last
deck = json.loads((D / "deck.json").read_text())
deck["order"] = ORDER
deck["title"] = "TakRouter Pitch Deck"
deck["sections"] = {"s1": {"description": "The pitch: problem, why now, solution, market, business, go-to-market and the ask", "start": "cover"},
                    "s2": {"description": "Technical part: how the router chooses, evaluation and results", "start": "techdiv"},
                    "s3": {"description": "Backup slides for questions", "start": "t2psi"}}
(D / "deck.json").write_text(json.dumps(deck, ensure_ascii=False))
print(len(ORDER), ORDER)
