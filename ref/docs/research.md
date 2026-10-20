# LLM routing: state of the art (as of 2026-10-14)

Background research for the project: what the field and industry do about routing LLM requests
by cost and quality.

## 1. The architecture the field converged on

A March 2026 survey of routing and cascading ([arXiv 2603.04445](https://arxiv.org/html/2603.04445v2))
recommends a three-stage production design:

1. A **cheap router before generation** that uses features of the prompt and the models.
2. A **check after generation** for quality or uncertainty.
3. An **escalation policy** that accepts, repairs, or sends the request to a stronger model.

Our design follows this structure. Current work learns the stage-1 decision from data instead
of hand-written rules.

## 2. The main current approaches

| Family | Representative methods | Main idea |
|---|---|---|
| Learned from preferences | RouteLLM, Hybrid LLM, Arch-Router (1.5B), P2L | Train a classifier on "which model won" data. RouteLLM found that adding LLM-judge labels to human labels helps a lot. |
| Clustering / model profiles | **UniRoute** (ICLR 2026), Avengers-Pro | Group prompts into clusters. Each model is described by its error rate in each cluster. Send each prompt to the model with the lowest cost-adjusted error in its cluster. |
| Difficulty prediction | BEST-Route, IRT-Router, GraphRouter, vLLM Semantic Router | Predict how hard a prompt is and match it to model ability. |
| Reinforcement learning and bandits | Router-R1, R2-Router, MixLLM, PILOT | Learn the routing policy online from feedback. |
| Cascades with uncertainty | FrugalGPT, AutoMix, Conformal Cascade (2026), UCCI (2026) | Escalate based on calibrated uncertainty. Internal-probe and perplexity signals beat a model's own stated confidence. |

### Three findings that apply to us

- **UniRoute** ([paper](https://arxiv.org/html/2502.08773v2)): embed prompts, cluster them, and give
  each model a feature vector of its error rate per cluster. The model features are measured, not
  hand-written. Adding a new model only takes running it on a small reference set, with no retraining.
- **Routers fail mostly by being too cautious.** RouterArena (ICLR 2026,
  [arXiv 2510.00202](https://arxiv.org/html/2510.00202v1)) found that every router fell short of the
  ideal choice, mainly because they don't recognize when a small, cheap model is enough. Commercial
  routers did not reliably beat open ones; for example, Not Diamond often picked expensive models.
- **One answer per prompt is a noisy label** ([DARS, EMNLP 2026](https://arxiv.org/abs/2606.06924)).
  Models answer differently each time, so sample several answers per (prompt, model), including
  from rephrased prompts.

## 3. Industry

- **Microsoft Foundry Model Router:** a trained router across several vendors, but only inside Azure.
- **Amazon Bedrock Intelligent Prompt Routing:** routes between two models of the same family. AWS
  claims savings of up to about 30%.
- **Not Diamond and Martian:** commercial learned routers. Their savings claims (up to 85–92%) are
  reported by the vendors themselves, not independently checked.
- **OpenRouter Auto:** sources conflict about which router it currently uses.
- **Open source:** Arch-Router and vLLM Semantic Router. LiteLLM, Portkey and similar tools are
  gateways handling failover, retries and caching, not smart routing.

## 4. Prompt shrinking and a warning

- **LLMLingua-2** is still the standard general-purpose compressor. Intel's Adaptive Token
  Compressor (2026) packages this for agent system prompts.
- **Warning:** several 2026 reports found that with provider prompt caching, sending the full
  context was often cheaper and better than compressing it
  ([agentgateway](https://agentgateway.dev/blog/2026-07-27-optimize-token-cost-with-context-compression/),
  [Bouchard](https://www.louisbouchard.ai/context-engineering-2026/)). Any prompt compression must
  be checked against "full prompt with caching" as a baseline.

## 5. Persian is a gap, which is an opportunity

No router research measured on Persian was found. Related multilingual work found that how
well-resourced a language is matters for the best prompting choice
([ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.1864/)).

## What this means for our design

1. Use the standard three-stage shape: router before generation, checks after, escalation.
2. Use a UniRoute router: embed each prompt (e.g. a multilingual model such as multilingual-e5),
   cluster the prompts, and measure each candidate model's error per cluster.
3. Build labels the DARS way: several answers per (prompt, model), scored by a strong judge, with a
   small human-checked subset to verify the judge.
4. Retest the prompt compression against full prompt plus caching.
5. Calibrate escalation decisions on real data instead of fixed thresholds.

## Sources

- [Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey (arXiv 2603.04445)](https://arxiv.org/html/2603.04445v2)
- [RouteLLM (arXiv 2406.18665)](https://arxiv.org/pdf/2406.18665)
- [RouterArena (arXiv 2510.00202)](https://arxiv.org/html/2510.00202v1) · [ICLR 2026 paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/4987bb24bc53c198785922d1bd9e18cf-Paper-Conference.pdf)
- [LLMRouterBench (arXiv 2601.07206)](https://arxiv.org/html/2601.07206v1)
- [R2-Router (arXiv 2602.02823)](https://arxiv.org/pdf/2602.02823)
- [From Sampled Outcomes to Capability Distributions / DARS (arXiv 2606.06924)](https://arxiv.org/abs/2606.06924)
- [Universal Model Routing / UniRoute (arXiv 2502.08773)](https://arxiv.org/html/2502.08773v2)
- [Conformal Cascade (arXiv 2607.25018)](https://arxiv.org/html/2607.25018v1)
- [UCCI (arXiv 2605.18796)](https://arxiv.org/html/2605.18796v1)
- [CascadeDebate (arXiv 2604.12262)](https://arxiv.org/html/2604.12262v1)
- [Language Model Cascades and Deferral Rules (arXiv 2404.10136)](https://www.emergentmind.com/papers/2404.10136)
- [Amazon Bedrock Intelligent Prompt Routing docs](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html)
- [Best LLM routers 2026 (Braintrust)](https://www.braintrust.dev/articles/best-llm-routers-2026)
- [OpenRouter Auto Router guide](https://aireiter.com/blog/openrouter-auto-router-guide)
- [Not Diamond alternative (Morph)](https://www.morphllm.com/notdiamond-alternative)
- [LLMLingua (Microsoft Research)](https://www.microsoft.com/en-us/research/project/llmlingua/)
- [agentgateway: context compression (Jul 2026)](https://agentgateway.dev/blog/2026-07-27-optimize-token-cost-with-context-compression/)
- [Context engineering 2026 (Louis Bouchard)](https://www.louisbouchard.ai/context-engineering-2026/)
- [No One Fits All: multilingual learned routing (ACL 2026 Findings)](https://aclanthology.org/2026.findings-acl.1864/)
