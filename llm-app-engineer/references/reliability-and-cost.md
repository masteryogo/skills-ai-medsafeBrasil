# Reliability, streaming, cost, and observability

## Failure handling

LLM APIs fail in ways ordinary HTTP services do not: they are slow, occasionally very slow,
rate-limited by tokens as well as requests, and they return syntactically valid nonsense.
Plan for all four.

- **Timeout every call**, sized to the task (a short extraction: 15-30 s; a long
  document analysis: 60-120 s). Set it on the client, not just on your web framework. Decide
  and implement what the user sees when it fires.
- **Retry only what is retryable:** 429 and 5xx, with exponential backoff and jitter, 2-3
  attempts. Honor `Retry-After` when present. Never blind-retry a 400 — the request is
  malformed and will fail identically.
- **Retry validation failures differently.** When the output fails schema validation, retry
  once appending the validation error to the conversation ("o campo `dose` veio como texto;
  responda de novo respeitando o schema"). Cap at one retry, then fail loudly. Silent
  infinite repair loops burn money and hide bugs.
- **Idempotency.** Webhooks (Telegram, WhatsApp, payment providers) redeliver. Key every
  incoming event by its provider event id, persist that key, and drop duplicates *before*
  spending a model call. Without this, one retried delivery becomes two answers to the user.
- **Circuit breaker plus fallback.** When the provider is degraded, stop hammering it: return
  a graceful message, queue the work, or fall back to another provider or a smaller model.
  Log every fallback — an unlogged fallback makes production quietly diverge from your eval.
- **Never let a provider outage lose user data.** Persist the incoming request before calling
  the model, so the work can be retried or replayed.

## Streaming and SSE

Streaming is a UX feature, and it changes the failure model.

- **Stream prose to humans; return structured data whole.** A stream cut mid-JSON leaves the
  parser with a fragment. If you must stream while also producing structured data, stream the
  human-readable part and send the validated object in a final event.
- **Send heartbeats or comment frames** on an idle SSE connection so proxies do not close it.
  Disable response buffering on the proxy (`X-Accel-Buffering: no` for nginx) or the client
  receives everything at once at the end.
- **Handle client disconnect.** Detect it and cancel the upstream call, or you pay for tokens
  nobody will read. In FastAPI, check `await request.is_disconnected()` in the generator loop
  and break.
- **Define an error event.** Once headers are sent you cannot change the status code, so
  mid-stream failures must arrive as a typed event the client understands and renders.
- **Persist the full response server-side as it completes**, not only in the stream. The
  client may have gone away, and you still need it for logs, evals, and the conversation
  history.
- With Socket.IO across multiple instances, the message broker (Redis) is required for rooms
  to work — otherwise an event emitted on instance A never reaches a client held by
  instance B. This shows up as "funciona local, não funciona em produção".

## Latency

Perceived latency is what matters. In order of effect:

1. **Stream the first token.** A response that starts in 400 ms feels faster than one that
   completes in 3 s.
2. **Shorten the output.** Output tokens dominate latency — a request generating 800 tokens
   takes roughly 8x one generating 100. Ask for concise output and cap `max_tokens`.
3. **Use a smaller model on the easy path**, escalating only when needed.
4. **Parallelize independent calls** (`asyncio.gather`) instead of chaining them. Two
   sequential 2 s calls are 4 s; concurrently they are 2 s.
5. **Cut input tokens** — helps cost a lot and latency somewhat, mostly via prefill.
6. **Prompt caching**, where the provider offers it: put the stable content (system prompt,
   long document, few-shot examples) at the *start* of the prompt and the variable part at
   the end, so the shared prefix is cacheable. This can cut both cost and time-to-first-token
   substantially on repeated calls over the same context.
7. Do not let pre-processing hide in the latency budget — transcription, retrieval, embedding
   the query, and PDF parsing are often larger than the model call. Time each stage
   separately before optimizing.

## Cost control

- **Instrument first.** Log input tokens, output tokens, model, and computed cost per
  request, with a user or tenant id. You cannot manage what you cannot attribute.
- **Set a budget per request and per user/day**, enforced in code. An abuse case or a runaway
  agent loop otherwise arrives as an invoice.
- **The big levers, in order:** shorter prompts (stop pasting whole documents), a smaller
  model where the eval permits, prompt caching for repeated prefixes, caching identical
  requests outright, batching where the provider offers an async batch discount, and fewer
  agent steps.
- **Cache aggressively for deterministic tasks.** Classification and extraction over the same
  input at temperature 0 should be a cache hit, keyed on
  `(prompt_version, model, normalized_input)`.
- **Embeddings are cheap; re-embedding a whole corpus repeatedly is not.** Store embeddings
  with a content hash and only recompute what changed.
- Re-run the eval after every cost optimization. A cost cut that lost 8 points of accuracy is
  not a cost cut.

## Observability

Log one structured record per LLM interaction:

`request_id`, `user/tenant id`, `feature`, `prompt_version`, `model` and model version,
`input_tokens`, `output_tokens`, `cost`, `latency_ms`, `temperature`, `finish_reason`,
`retry_count`, whether a fallback fired, validation outcome, and — for RAG — the retrieved
ids. Store the prompt and response themselves, subject to your retention and privacy rules.

Alert on: error rate, p95 latency, rate-limit rate, **validation-failure rate** (the earliest
signal that a provider-side model change broke your schema), fallback rate, and cost per day
against the budget. Track `finish_reason == "length"` specifically — silent truncation
produces plausible, incomplete answers and is easy to miss.

Sample outputs for human review continuously — a few per day, read by someone. Metrics will
not tell you the tone went wrong or the model started answering in the wrong language.

## Pre-launch checklist

- [ ] Eval set in the repo, runnable in one command, with the current score recorded.
- [ ] Prompts in versioned files; version id logged with every response.
- [ ] Structured output validated; failure path defined and tested.
- [ ] "Não sei / não informado" is reachable and covered by eval cases.
- [ ] Timeout, retry policy, and user-visible fallback defined for provider failure.
- [ ] Webhook and request handling idempotent by provider event id.
- [ ] Untrusted input delimited; tools scoped to caller permissions; injection cases in eval.
- [ ] Personal data minimized before leaving your infrastructure; provider terms and
      retention verified and documented; your own retention policy implemented.
- [ ] Token, cost, and latency logged per request; per-user budget enforced.
- [ ] Model and model version pinned, not a floating alias.
- [ ] Human review step defined where a wrong answer causes harm, with the source visible to
      the reviewer.
- [ ] Alerts live on error rate, validation failures, truncation, latency, and daily cost.
