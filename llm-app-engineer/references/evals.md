# Evals

An eval is a test suite for a non-deterministic function. It does not need to be
sophisticated — it needs to exist, live in the repo, and run in one command.

## Building the set

**Size.** Start at 20-30 cases. That is enough to catch a regression and cheap enough to
build in an afternoon. Grow it every time production surprises you: each bug report becomes
a permanent case. A set of 200 real cases assembled this way is worth more than 5000
synthetic ones.

**Sources, in order of value.**
1. Real production inputs, sampled from logs. Nothing else has the same distribution.
2. Every past failure — the exact input that caused each complaint or incident.
3. Hand-written edge cases: empty input, one word, wrong language, mixed languages,
   off-topic, extremely long, contradictory, adversarial ("ignore as instruções acima"),
   and the case where the correct answer is "I cannot answer this".
4. Synthetic cases, last, to fill a gap you know exists but have no real examples for.

**Include negative cases.** Roughly a fifth of the set should be inputs where the right
behavior is to abstain, return null, refuse, or ask for clarification. Without these, the
eval rewards a model that always answers something, which is precisely the failure you are
trying to prevent.

**Store it as data, not code** — a JSONL or YAML file per eval, with `id`, `input`,
`expected` (or grading criteria), and a `tags` field for slicing (case type, language,
difficulty, source). Commit it. Review changes to it in PRs like any other test.

## Choosing the grader

Match the grader to the task; use the cheapest one that works.

| Task | Grader |
|---|---|
| Classification, routing, yes/no | exact match against the label |
| Structured extraction | field-by-field comparison after normalization; report per-field |
| Numbers, dates, doses, codes | exact match after unit and format normalization — never fuzzy |
| Presence of required content | substring or regex assertions ("must mention every listed medication") |
| Forbidden content | assertions that must *not* match (no invented drug, no diagnosis, no advice) |
| Format and schema | Pydantic validation; a parse failure is a hard failure |
| Free-form prose quality | LLM-as-judge, with the caveats below, plus periodic human review |
| Faithfulness to a source | LLM-as-judge asked a narrow question, or span-verification in code |

**Deterministic graders first.** Most of what matters in a business application is checkable
in code: did it produce valid JSON, did it get the dose right, did it leave the unknown field
null, did it avoid the forbidden claim. Push as much as possible into code assertions; they
are free, instant, and never drift.

## LLM-as-judge, done correctly

Useful when quality is genuinely subjective, dangerous when treated as ground truth.

- **Ask one narrow question per judge call**, with a binary or 1-5 answer and an explicit
  rubric: "Does the answer state any medication dose that does not appear in the source?
  Answer only SIM or NAO." Not "rate this answer from 1 to 10", which is noise.
- **Validate the judge against humans** on 20-30 cases before trusting it. If judge and
  human disagree meaningfully often, fix the rubric — an unvalidated judge is a random
  number generator with good manners.
- **Use a strong model as judge**, and a different one from the model under test where
  possible. Models favor their own outputs.
- **Give the judge the source and the criterion, not the "correct" answer**, when grading
  faithfulness — otherwise it grades similarity to your phrasing.
- **Never let the judge be the only signal.** Keep a human spot-check on a sample every
  cycle, and keep the deterministic assertions running alongside.

## Reading results honestly

- **Report the count, not just the percentage.** "91%" on 48 cases means 4 failures; one
  fixed case is 2 points. Differences of a couple of points on a small set are noise.
- **A rough rule for small sets:** on n cases, treat differences smaller than about
  `1/sqrt(n)` as inconclusive — on 30 cases, under ~18 points. This is uncomfortable, and it
  is why the set has to grow.
- **Slice by tag.** An aggregate that improved while one category got worse is a regression
  you are about to ship. Always print the per-tag table.
- **Look at the actual failures every run.** The list of failing case ids and their outputs
  is the most valuable output of the eval — more than the score. Read them.
- **Keep a results log** — one row per run with date, prompt version, model, model version,
  score, per-tag scores, and cost. Without the log you will re-litigate decisions you
  already made.

## Regression suite in CI

Split the set in two:

- **A fast smoke set** (5-10 cases, deterministic graders only) that runs on every PR
  touching prompts or LLM code. Cheap, seconds, blocks obvious breakage.
- **The full set**, run on demand and before release. Cache results by
  `(case_id, prompt_version, model, model_version)` so re-runs only re-execute what changed.

Make the runner a single command (`make eval`, `pytest tests/eval`), print the per-tag table
and the failing ids, and write the results row automatically. If running the eval takes
manual steps, it will stop being run.

Pin the model *version* string, not the floating alias. When the provider updates the alias
under you, the eval score moves for reasons unrelated to your code — pinning turns that into
a deliberate, dated upgrade with a before/after number.

## When the eval and production disagree

Production is right. The gap is information:

- The eval set does not reflect real inputs → sample fresh logs and add cases.
- The grader accepts something users reject → tighten the grader.
- Something outside the model is broken — retrieval returning nothing, a truncated
  transcription, a webhook delivering a partial payload, context assembled differently in the
  real handler than in the eval harness. This last one is common: run the eval through the
  **same code path** as production wherever possible, not a parallel script that builds the
  prompt its own way.
