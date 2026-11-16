---
name: llm-app-engineer
description: Build and ship production LLM applications the way a senior engineer would - eval sets before prompt changes, versioned prompts, validated structured output, grounding and citation, RAG that is measured retrieval-first, streaming, timeouts and retries, cost and token budgets, prompt-injection defense, and observability. Use when the user works on an LLM feature - chatbot, assistant, agent, extraction, summarization, classification, RAG, tool calling, function calling, SSE streaming - or asks to improve a prompt, reduce hallucination, cut token cost, evaluate model output, choose a model, or debug flaky or slow LLM responses. Covers the OpenAI SDK, FastAPI/SSE, and provider-agnostic app architecture.
user-invocable: true
---

# LLM Application Engineer

The hard part of an LLM app is not getting a good answer once — it is knowing whether a
change made the system better. Without a measurement, prompt work is superstition: every
edit feels like an improvement because you only look at the cases you were just thinking
about. **The eval set is the deliverable that makes every later change cheap.**

Two rules govern everything below:

1. **Never change a prompt without a way to see the effect.** Build the eval set first, even
   a small one. 20 real cases beats an intuition.
2. **The model's output is untrusted data.** Validate it, constrain it, and never let it
   silently become a database write, a shell command, an instruction, or a clinical or
   financial fact.

When the provider is Anthropic (Claude, `anthropic`, `claude-*`), load the `claude-api`
skill for model ids, pricing, and API specifics. This skill covers application
architecture, which is provider-independent. Never state a model's price, context window,
or capability from memory — look it up.

## The order of work

1. **Write down what "correct" means** for this feature, as concretely as a test would.
   "Better summaries" is not a target; "includes every medication with its dose, and never
   invents one" is.
2. **Collect 20-50 real inputs** from logs, real users, or realistic hand-written cases —
   including the ugly ones: empty input, wrong language, off-topic, adversarial, and the
   edge case that broke last week. Store them in the repo.
3. **Write the expected output or a grader** for each. See `references/evals.md`.
4. **Ship the simplest thing that could work:** one prompt, a capable model, structured
   output, validation. Measure it. That number is your baseline.
5. **Improve in this order** — it is roughly the order of payoff per hour:
   prompt/instructions → structured output and validation → context (retrieval quality,
   what you actually put in the prompt) → few-shot examples → model choice → decomposition
   into steps → fine-tuning (almost never the right answer).
6. **One change at a time, re-run the eval, record the number** with the prompt version.
7. **Then optimize cost and latency**, re-running the eval after each optimization to prove
   quality held. See `references/reliability-and-cost.md`.

## Non-negotiables

- **Prompts live in versioned files**, not inline f-strings scattered across handlers. Give
  each a version id, and log which version produced each response. You cannot debug a
  complaint about last Tuesday's output without knowing which prompt ran.
- **Ask for structured output and validate it.** Use the provider's JSON-schema or
  tool/function-calling mode, parse into a Pydantic model, and handle the failure path
  explicitly (retry once with the validation error appended, then fail loudly). Never
  regex-scrape fields out of prose.
- **"Not found" must be a valid answer.** Every extraction schema needs an explicit null or
  `nao_informado` for each field, and the prompt must say that leaving it empty is correct.
  Without this, the model fills the gap with something plausible — which is the mechanism
  behind most hallucinations in extraction tasks.
- **Ground factual answers in provided text and require attribution.** If the answer must be
  supported by a document, make the model return the supporting span or id, then verify that
  span exists in the source. An unverifiable citation is worse than no citation.
- **Set a timeout on every call** and decide what happens when it fires. The default SDK
  timeout is long enough to hold an HTTP request open past the point where the user gave up.
- **Cap and count tokens.** Log input tokens, output tokens, model, and cost per request.
  A feature whose cost you cannot state is a feature you cannot operate.
- **Treat every string that reaches the prompt from outside as hostile** — user messages,
  retrieved documents, transcriptions, file contents, webhook payloads. See the injection
  section of `references/rag-and-grounding.md`.
- **Minimize what you send to the provider.** Strip or mask what the task does not need,
  especially personal data. For health, financial, or legal data, confirm the provider's data
  handling and retention terms cover the use, and record that decision in the repo.
- **Set temperature deliberately.** 0 (or near) for extraction, classification, and anything
  evaluated against a fixed answer; higher only for genuinely open generation. Note that 0
  is not deterministic across provider-side changes — pin the model version too, and expect
  eval drift when the provider updates it.

## Choosing the model

Start with a capable mid-tier model, get the eval passing, *then* try to move down. Going
straight to the cheapest model wastes days debugging a capability problem that looks like a
prompt problem.

- Extraction, classification, routing, short rewrites → a small/fast model, usually enough
  once the prompt and schema are tight.
- Reasoning over long documents, ambiguous clinical or legal text, multi-step tool use → the
  strongest model available; the cost difference is usually smaller than the cost of being
  wrong.
- Mixed traffic → route by difficulty (a cheap classifier or a heuristic first), with the
  strong model as the escalation path. Measure the routing decision itself.
- Check current model names, context limits, and prices from the provider's docs at the time
  of the work. They change often and stale assumptions produce wrong architecture.

## Anti-patterns

- Judging a prompt change by trying two or three inputs by hand.
- A megaprompt that grew for six months and nobody dares to touch, because there is no eval
  to prove a deletion was safe. Prune with the eval as your safety net.
- Putting the whole database, whole document, or whole chat history in the context because
  the window is large. More irrelevant context measurably lowers accuracy and raises cost.
- Building RAG before measuring whether retrieval finds the right chunk at all.
- Reaching for fine-tuning to fix accuracy. Fine-tuning teaches format and style reliably;
  it teaches facts poorly. Fix the prompt, the schema, and the retrieved context first.
- Adding an agent loop where a single call plus a `for` loop in Python would do. Every
  autonomous step multiplies latency, cost, and failure modes.
- Letting model output reach an action (a write, a send, a payment, a shell command) with no
  validation or confirmation step in between.
- Streaming a JSON payload that a downstream parser must validate — you get a half-object on
  disconnect. Stream prose to humans; return structured data whole.
- Silent fallbacks: swapping to another model or a cached answer without logging it, so the
  eval and the production behavior quietly diverge.

## Reporting results

Give the eval number, the size of the set, what moved, and what is still broken:

> Extraction eval (48 casos reais): campos obrigatórios corretos 91% (era 78% na v3 do
> prompt). O ganho veio de exigir `null` explícito em vez de campo ausente. Ainda falha em
> dose com vírgula decimal (6 de 48) e em receita com dois medicamentos na mesma linha.
> Custo médio 0,004 USD por chamada, p95 de latência 2,1 s.

Say plainly when a feature is not ready and what the blocker is. In a domain where a wrong
answer causes harm, state the required human review step as part of the design, not as a
disclaimer bolted on at the end.

## Reference files

- `references/evals.md` — building the eval set, choosing graders, LLM-as-judge done
  correctly, regression suites in CI, and how to read a small-sample result honestly.
- `references/rag-and-grounding.md` — chunking, retrieval measured on its own, reranking,
  grounding and citation verification, and prompt-injection defense.
- `references/reliability-and-cost.md` — timeouts, retries, idempotency, streaming and SSE,
  caching, token and cost budgets, observability, and the pre-launch checklist.
