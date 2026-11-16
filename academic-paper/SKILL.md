---
name: academic-paper
description: >
  Write, revise and submit scientific papers for CS/ML venues (NeurIPS, ICML, CVPR, ICLR, MICCAI, ACL, IEEE/ACM): drafting a manuscript from results, hardening a draft against overclaim and weak statistics, answering peer reviewers, and submission work (LaTeX template, BibTeX, anonymity, page limits). Use it for the whole paper or one small piece of it: an abstract, a claim sentence that may be too strong, an ablation table, a messy .bib file, one reviewer comment, de-anonymizing for camera-ready. Those routine-looking chores are exactly where papers get rejected, so do not skip the skill because a request seems small. Trigger on how people actually describe the problem, not only formal terms: "my advisor says the intro doesn't establish the gap", "does this sentence overclaim", "reviewer 2 says it lacks novelty", "write this up for ICLR". Portuguese counts equally: artigo, resumo, revisor, parecer, rebuttal, submissão, "escrever o artigo", "responder o revisor", "meu orientador disse que está fraco".
---

# Academic paper (CS/ML)

Papers fail review for predictable reasons: a contribution the reader can't
restate, claims wider than the evidence, missing baselines, and tables nobody
can reproduce. This skill exists to catch those before a reviewer does.

Default language is **English**, even when the conversation is in another
language — venues are English. Talk to the user in their language; write the
manuscript in English unless they ask otherwise.

## Boundaries with neighbouring skills

This skill starts where the research is already done. It writes up evidence;
it does not go find or appraise it.

| The user is now... | Use |
|---|---|
| Drafting, revising, rebutting, formatting for a venue | **this skill** |
| Searching the literature, appraising a paper, establishing the gap, designing the study | `scientific-research-assistant` |
| Actually training, splitting, tuning, deploying a model | `machine-learning-engineer` |
| Building the vision pipeline (capture, ROI, tracking, on-device) | `computer-vision-engineer` |
| Processing Brazilian clinical text | `medical-nlp-ptbr` |

Hand back explicitly — name the skill and why — when the writing exposes a
research hole rather than a wording problem. The three that matter:

- The gap in the intro cites nothing, or the user cannot say which papers
  define the frontier. Do not paper over it with prose.
- A reviewer claims the work lacks novelty, or the rebuttal needs a citation
  not already retrieved in this session. Settling that is a literature search.
- A number is missing because the study was never designed to produce it.

## Pick the mode

| User is doing | Mode | Read next |
|---|---|---|
| Has results, needs a manuscript | **Draft** | `references/imrad-ml.md` |
| Has a draft, wants it stronger | **Revise** | `references/imrad-ml.md` + the review rubric below |
| Got reviews back | **Rebuttal** | `references/rebuttal.md` |
| Ready to submit | **Format** | `references/submission.md` |

Modes mix. A user who pastes reviews usually also needs text edits — do both.

## Before writing anything: the claim contract

Ask for, or extract from the material, these five things. If something is
missing, say which one and why it blocks you, then proceed with an explicit
placeholder rather than inventing it.

1. **Contribution**, in one sentence a reviewer could repeat from memory.
2. **The gap** — what existing work cannot do, with the specific papers that
   define the frontier.
3. **Evidence** — the actual numbers, with baseline, dataset, and variance.
4. **Scope limits** — what the result does *not* show.
5. **Venue**, which sets length, template, and how much background to assume.

Then write the claim table before prose:

| Claim | Where it is supported | Strongest counter-reading |
|---|---|---|

Every sentence in the abstract must trace to a row. If it doesn't, either the
claim is unsupported or the experiment is missing — both are worth saying out
loud to the user now, not at rebuttal time.

## Non-negotiables about evidence

These are where LLM-written papers get desk-rejected, so hold the line even if
it makes the paper sound less exciting:

- **Never invent a citation, a number, a dataset split, or a p-value.** If a
  number is needed and absent, write `[TODO: accuracy on X]` and list it in a
  gaps section at the end. A fabricated reference is worse than a blank.
- **Report variance.** A single-seed number is an anecdote. Give mean ± std
  over seeds, say how many, and never bold a win inside the noise.
- **Match the verb to the evidence.** "improves by 0.3 points on one dataset"
  is not "significantly outperforms"; correlation is not "causes"; a benchmark
  win is not "solves". Reserve *significant* for an actual test, named.
- **Baselines before novelty.** If the paper has no comparison against the
  obvious simple method, flag it — reviewers always ask.
- **Ablate the contribution.** If three components are claimed, the reader
  needs evidence about each one, not only the full system.
- **Fit the test to the sample.** With a small or paired cohort, a paired
  non-parametric test (Wilcoxon signed-rank) is usually the defensible choice;
  name the test and why it fits rather than reaching for a t-test by default.
- **Translate the metric into the unit that decides use.** An improvement of
  1.1 degrees means nothing until it becomes "this target size is now
  selectable"; a 3% F1 gain means nothing until it becomes a cost or a caseload.
  Application papers are accepted on that translation, so put it in the abstract.

## Voice

Write the way strong papers in the venue read: direct, present tense for what
the paper does, past tense for what was done. Prefer "we train" over "it is
trained". Cut hedging stacks ("may potentially suggest"), cut throat-clearing
("It is important to note that"), cut adjectives doing an experiment's job
("dramatically", "novel", "state-of-the-art" unless literally measured).

A paragraph should open with the sentence a skimming reviewer needs. If the
point only arrives at the end, move it up.

## Review rubric (Revise mode)

Go through these and report findings with file/section anchors, severity, and
a concrete fix — not a vague "could be clearer":

1. Can the contribution be restated in one sentence after reading only the
   abstract and intro? If not, that's finding #1.
2. Does every abstract claim have evidence in the paper?
3. Are baselines fair — same budget, same tuning effort, same data?
4. Are tables self-contained (units, n, variance, what bold means)?
5. Is related work positioned ("X does A but not B") or just listed?
6. Does the limitations section name a real threat to validity, or a fake one
   ("we only tested on five datasets")?
7. Reproducibility: seeds, hyperparameters, compute, code/data availability,
   license and ethics where the venue requires it.

## Output

Produce LaTeX when the venue or an existing `.tex` says so; otherwise Markdown
that converts cleanly. Always end a drafting or revision pass with:

- **Open gaps** — missing numbers, citations to verify, experiments a reviewer
  will demand.
- **Weakest point** — your honest guess at the reason this gets rejected, and
  the cheapest thing that would fix it.

That last section is the most useful thing in the deliverable. Do not soften it.
