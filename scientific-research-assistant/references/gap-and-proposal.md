# Gaps, questions and proposals

Read this when the user asks whether an idea is new, what to work on, how to
turn an interest into a research question, or how to write the proposal.

**Contents**
1. Kinds of gap — and the ones that are traps
2. Testing a novelty claim before you endorse it
3. From topic to answerable question
4. Writing the hypothesis so it can fail
5. Choosing the design
6. The minimum viable study
7. Feasibility audit
8. Pre-registration
9. Proposal structure
10. How to give this feedback

---

## 1. Kinds of gap — and the ones that are traps

A gap is a place where knowledge is missing *and the missing knowledge matters*.
Both halves are required. Useful kinds:

| Gap | Shape | Example |
|---|---|---|
| **Evidence** | Claim made, never tested rigorously | Model deployed in clinics, never prospectively evaluated |
| **Population** | Works for some, untested for others | Dermatology model trained on light skin only |
| **Setting** | Works in one context, untested elsewhere | Tertiary-hospital model in primary care; high-end scanner → portable device |
| **Methodological** | Existing studies share a fixable flaw | All prior work splits by image, not by patient |
| **Measurement** | No valid way to measure the thing | No validated metric for communication quality in AAC |
| **Translational** | Accuracy proven, usefulness never asked | High AUC, no decision-curve or workflow study |
| **Integration** | Two solved problems never combined, with a reason to combine | — |

**Traps that look like gaps:**

- **"No one has applied method X to problem Y."** Usually true and usually
  uninteresting. Novel *combination* is not a contribution unless Y has a
  property that makes X non-trivial, or the result changes what someone does.
  Make the user state that property; if they cannot, this is a trap.
- **The silent-failure gap.** Nobody published it because it was tried and did
  not work. Negative results are rarely published. Before celebrating an empty
  search, look for the method in related problems and for registered trials
  that never reported (ClinicalTrials.gov entries stuck at "completed").
- **The infeasible gap.** Nobody did it because the data cannot be obtained, the
  labels require unaffordable expert time, or the ethics approval is
  prohibitive. The gap is real; the project is not.
- **The vocabulary gap.** Nobody did it *under that name*. See the two-lexicon
  section of `references/search-sources.md` — this is the most common false gap.
- **The incremental delta.** A 0.3-point benchmark gain is a gap only to a
  leaderboard, not to a field.

---

## 2. Testing a novelty claim before you endorse it

Endorsing false novelty is costly, so run this before saying "this looks new":

1. **Search the other lexicon** — clinical terms and ML terms, plus the
   disease's lay name, acronym and Portuguese name.
2. **Find the most recent survey or systematic review** on the topic and read
   its future-work section. If the user's idea appears there, it is known and
   unexecuted, not unknown — a different, often *better*, position to be in.
3. **Forward-cite from the two most relevant papers.** The newest work renames
   things; keyword search misses it, citation traversal does not.
4. **Check registries and preprints** — the idea may be 18 months into
   execution without a publication yet.
5. **Check non-English sources** — LILACS, SciELO, and Portuguese/Spanish theses.
   Brazilian clinical work in particular is under-indexed in PubMed.
6. **Ask who would care.** If the result came out either way, who changes their
   behaviour? A gap no one would act on is a hobby, which is fine, but say so.

Then state your conclusion with its uncertainty: "I found no work doing X under
these terms across OpenAlex, Europe PMC and arXiv; the closest is [paper], which
does Y. I could not search Scopus or Embase. Treat this as suggestive, not
proof of novelty." Never say "this has never been done."

---

## 3. From topic to answerable question

A topic is "AI for ALS communication". A question can be answered, bounded and
disconfirmed.

**For clinical/applied questions — PICO:**
- **P**opulation: who, precisely, with what inclusion criteria?
- **I**ntervention / index test: what exactly is applied?
- **C**omparator: against what current practice or baseline?
- **O**utcome: what is measured, by whom, when, with what instrument?

For observational work, PECO swaps Intervention for Exposure. Prognostic work
needs a time horizon in the O: "30-day readmission", not "readmission".

**For ML/methods questions, the equivalent four:**
- Task and inputs/outputs, exactly
- Baselines, including the trivially strong one
- Benchmark/dataset and the evaluation protocol you are bound to
- The claim about *why* it works, and the ablation that isolates it

**Then apply FINER** — the filter that kills bad projects early:

| | Question to ask |
|---|---|
| **F**easible | Data, labels, compute, time, expertise, access — do they exist for *this* person? |
| **I**nteresting | To the field, not only to the author |
| **N**ovel | Confirms, refutes or extends something — see §2 |
| **E**thical | Approvable; data lawful to use (`references/ethics-data.md`) |
| **R**elevant | Changes practice, policy, or the next study |

Feasibility is where student projects die, and it is the one the advisor must
raise. A master's with no data-access agreement and no annotator budget does not
have a 12-month imaging project.

---

## 4. Writing the hypothesis so it can fail

A hypothesis that cannot be wrong is not a hypothesis. Force these four:

1. **Direction and magnitude.** Not "improves performance" — "increases
   sensitivity by ≥5 percentage points at fixed specificity of 0.90".
2. **The comparator**, named.
3. **The population and conditions** under which it should hold.
4. **The disconfirming result**, written out: "if the gain is under 2 points, or
   does not hold on the external cohort, the hypothesis is not supported."

Then ask the uncomfortable question: *what will you do if it fails?* A design
where the negative result is still publishable and informative is a much safer
project than one that only works if the model wins.

---

## 5. Choosing the design

Match the design to the question, not to ambition. Common progression in
AI-in-health, each step answering a different question:

| Question | Design |
|---|---|
| Can a signal be extracted at all? | Retrospective feasibility / proof of concept |
| How accurate is it? | Retrospective diagnostic accuracy study (STARD/CLAIM) |
| Does it generalize? | External validation on an independent cohort — different site, scanner, period |
| Does it predict future events? | Prospective cohort, prognostic model (TRIPOD+AI) |
| Is it usable and safe with real clinicians? | Early live evaluation (DECIDE-AI); human-factors study |
| Does it improve outcomes? | RCT (CONSORT-AI / SPIRIT-AI) |
| Is it worth the money? | Economic evaluation (CHEERS) |

Say plainly which rung the user's project is on. A great deal of disappointment
comes from writing an outcomes claim for a feasibility study.

**Sample size is a design decision, not an afterthought.** For diagnostic
accuracy, the binding constraint is usually the number of *positive* cases, not
total n. For prediction models, PROBAST-style events-per-variable thinking
applies. If the user cannot reach a defensible n, reframe the study as
feasibility and say so in the title — that is honest and still publishable.

---

## 6. The minimum viable study

Most proposals that reach you are 2–3× too large. The advisor's job is to find
the smallest study that still answers something real.

- **One primary question.** Everything else is secondary and clearly labelled.
- **Reuse before you collect.** A public dataset or an existing cohort can save
  a year; collection should be justified by the absence of an alternative.
- **The strongest simple baseline, built first.** Logistic regression on five
  clinical variables, or classical features. If the deep model cannot beat it,
  that is the finding, and it is worth knowing in week three rather than month
  nine.
- **A fixed, untouched evaluation set defined before modelling starts.**
- **A pre-agreed stopping point**, so the project ends in a result rather than
  in exhaustion.

Advise staging: feasibility → accuracy → external validation, with the later
stages as future work, instead of promising all three in one year.

---

## 7. Feasibility audit

Ask these explicitly; vague answers are the finding:

- **Data**: does it exist, who controls it, is there a written agreement, what
  is the realistic timeline to access (often 6+ months with an ethics committee)?
- **Labels**: who annotates, how many hours, inter-rater agreement measured how,
  and is the reference standard itself reliable?
- **Compute**: available, and sized for the model proposed?
- **Expertise**: is there a clinical collaborator who will actually engage, not
  just sign? Clinical co-authorship without clinical participation produces
  studies that answer no clinical question.
- **Time**: deadline, and what happens to the project if data arrives late.
- **Ethics/legal**: see `references/ethics-data.md`.

---

## 8. Pre-registration

Under-used in ML, standard in clinical work, and it strengthens any project:
register the question, primary outcome, analysis plan and sample size *before*
seeing the test data. OSF for general research, ClinicalTrials.gov or ReBEC
(Brazil) for trials, PROSPERO for systematic reviews.

The gain is concrete: it makes "we chose this metric before looking" a verifiable
statement instead of an assurance, and it immunizes the project against the
reviewer's most damaging suspicion.

---

## 9. Proposal structure

Adapt to the destination; the logic is constant.

**General research proposal:**
```
Problem        The clinical or scientific problem, with its cost, cited
State of art   What is known — organized by finding, with the strongest work named
Gap            What is missing and why it matters, from §1, with the search behind it
Question       PICO or the ML equivalent, one primary question
Hypothesis     Falsifiable, with the disconfirming result stated
Methods        Data, labels, splits, model/analysis, comparator, metrics, validation
Analysis plan  Primary analysis, sample size justification, how uncertainty is reported
Feasibility    Access, timeline, resources, expertise — §7
Ethics/data    Approval route, legal basis, privacy design
Risks          What could derail it, and the mitigation for each
Outputs        Papers, code, dataset, artefacts — and who benefits
Timeline       Milestones with decision points, not a wish list
```

**Brazilian agencies and programmes** (CNPq, FAPESP, CAPES, institutional PPG)
expect the same substance with local framing: *objetivo geral* and *objetivos
específicos* stated separately, *justificativa* carrying the social/health
relevance, *metodologia* detailed enough for a committee outside your subfield,
*cronograma* usually as a Gantt-style table, *resultados esperados* and
*orçamento* when funded. CEP/CONEP approval via Plataforma Brasil is mandatory
for human-subject research — budget real months for it, and write the proposal
knowing the committee may have no ML background. Write these in Portuguese.

**Conference/journal-bound work** is written in English, and the gap paragraph
is the one reviewers read hardest — see `academic-paper` once drafting starts.

---

## 10. How to give this feedback

You are advising, which means the comfortable answer is often the wrong one.

- **Lead with the structural problem**, not with encouragement. If the design
  cannot answer the question, that is the first sentence.
- **Be specific about the fix.** "Split by patient, not by image, and report the
  number of unique patients in each fold" — not "consider data leakage".
- **Separate fatal from improvable**, explicitly. Users cannot read severity
  from tone.
- **Offer the smaller version.** When a project is infeasible, the useful reply
  is the feasible study inside it.
- **Say what is good, and mean it.** An advisor who only finds faults stops
  being consulted, and the next flawed design never reaches you.
- **Leave the decision with them.** Give the reasoning and the trade-off; they
  own the research.
