# Critical appraisal

Read this when judging a paper, a result, a claim, or a body of literature.

**Contents**
1. The order to read a paper in
2. Reporting guidelines: which one applies
3. Risk-of-bias tools
4. Evidence hierarchy — and why it is not a ladder
5. Reading the metrics
6. Statistics that do not survive scrutiny
7. Reproducibility and availability
8. LLM- and foundation-model-specific checks
9. Writing the appraisal

---

## 1. The order to read a paper in

Not front to back. Appraisal is faster and more honest in this order:

1. **Claim** — what exactly is asserted in the abstract's last sentences?
   Write it down in one sentence, in your own words. Most appraisal failures
   start here: the reviewer never pinned the claim.
2. **Data** — who are the subjects, how many, from how many sites, recruited
   how, over what period? This bounds everything that follows.
3. **Split** — how were train/validation/test separated, and at what unit
   (patient? image? slice? visit?). Sub-patient splits leak, silently.
4. **Comparator** — against what? No comparator means no claim of improvement.
5. **Primary outcome and when it was chosen** — pre-registered, or picked after
   looking?
6. **Numbers** — only now. With uncertainty intervals, or they are decorative.
7. **Methods detail** — enough to rebuild it? Code and data available?
8. **Limitations and funding** — what they admit, and who paid.

If steps 2–4 fail, the numbers in step 6 do not matter and you should say so
rather than discussing them politely.

---

## 2. Reporting guidelines: which one applies

Guidelines describe what a paper *must report*. A paper that omits most items of
its applicable guideline is not necessarily wrong — it is unassessable, which
for practical purposes is the same problem. Match the guideline to the study
type; citing the wrong one makes your appraisal look mechanical.

| Study type | Guideline | What it is for |
|---|---|---|
| Systematic review / meta-analysis | **PRISMA 2020** | Search, screening, flow diagram, synthesis |
| Scoping review | **PRISMA-ScR** | Mapping breadth rather than pooling effects |
| AI in medical imaging | **CLAIM** | Imaging-specific: acquisition, ground truth, model, evaluation |
| Prediction model (development/validation), incl. ML | **TRIPOD+AI** (2024) | Supersedes TRIPOD 2015 for AI; covers data, model, calibration, fairness |
| LLM-based study | **TRIPOD-LLM** | Prompts, versions, temperature, dates — the parts that make LLM work irreproducible |
| Diagnostic accuracy study | **STARD 2015** | Index test, reference standard, flow of participants |
| RCT with an AI intervention | **CONSORT-AI** | Extension: skill of operators, input handling, error analysis |
| Protocol for such an RCT | **SPIRIT-AI** | The protocol-side twin of CONSORT-AI |
| Early-stage live clinical evaluation | **DECIDE-AI** | The stage between offline accuracy and an RCT |
| Observational cohort/case-control | **STROBE** | Classic epidemiology reporting |
| Radiomics | **RQS** + **IBSI** feature definitions | Feature stability is the whole problem there |
| Trustworthy-AI design across the lifecycle | **FUTURE-AI** | Fairness, universality, traceability, usability, robustness, explainability |

Two practical uses: (a) to appraise, check the handful of items that actually
bite — ground truth definition, external validation, calibration, patient-level
split; (b) to *plan*, hand the user the full checklist early, because
retrofitting a missing design element into a finished study is impossible.

A frequent and avoidable error: applying CONSORT-AI to a retrospective accuracy
study. Most AI-in-health papers are **not** trials; they are diagnostic accuracy
or prediction-model studies, so CLAIM / STARD / TRIPOD+AI are usually the right
lens.

---

## 3. Risk-of-bias tools

Reporting ≠ validity. These assess whether the design can support the claim.

- **PROBAST** (and **PROBAST+AI**) — prediction model studies. Four domains:
  participants, predictors, outcome, analysis. The analysis domain is where
  most ML papers fail: small events-per-variable, no calibration, optimistic
  internal validation, selection of predictors on the full dataset.
- **QUADAS-2** (and the emerging **QUADAS-AI**) — diagnostic accuracy. Domains:
  patient selection, index test, reference standard, flow and timing. Watch for
  a reference standard that is itself the model's training label.
- **RoB 2** — randomized trials. **ROBINS-I** — non-randomized interventions.
- **GRADE** — certainty of a body of evidence, not a single study. Useful when
  the user asks "so what do we actually know about X?"

Name the domain and the specific fact that triggered the concern. "High risk of
bias in patient selection: cases came from a tertiary referral centre and
controls from a screening programme" is appraisal; "some risk of bias" is noise.

---

## 4. Evidence hierarchy — and why it is not a ladder

Rough ordering of strength for a *clinical* claim:

```
systematic review of RCTs  >  RCT  >  prospective cohort  >  retrospective cohort
>  case-control  >  case series  >  retrospective accuracy study on curated data
>  expert opinion / unreviewed preprint
```

Three corrections that keep this from being misused:

1. **Match the design to the question.** An RCT is the right design for "does
   deploying this model improve patient outcomes?" and the wrong one for "does
   this architecture segment better than that one?" Demanding an RCT of a
   methods paper is not rigour, it is a category error.
2. **A well-run retrospective study beats a badly run trial.** Position in the
   hierarchy is a prior, not a verdict.
3. **ML papers sit outside this hierarchy entirely.** For a NeurIPS/CVPR-style
   contribution, the equivalent questions are: strong and current baselines,
   standard benchmark protocol, multiple seeds with variance, ablations that
   isolate the claimed mechanism, and no test-set tuning.

**The translation gap is the point.** Most AI-in-health work lives at the
bottom of that stack — retrospective, curated, single-site — while its abstract
is written as though it were at the top. Flagging that mismatch is often the
single most useful thing you can say about a paper.

---

## 5. Reading the metrics

**Prevalence rules PPV.** Sensitivity and specificity are properties of the
test; positive predictive value is a property of the test *and the population*.
A test at 95% sensitivity and 95% specificity, in a population with 1%
prevalence, yields a PPV around 16% — roughly five false alarms per true
positive. Any paper reporting a balanced-dataset accuracy for a rare condition
without translating to the deployment prevalence is overstating its case. Do
that arithmetic yourself; it takes seconds and changes conclusions.

**Other metric traps:**
- **Accuracy on imbalanced data** is close to meaningless — compare against the
  majority-class floor before being impressed.
- **AUROC** is threshold-free and prevalence-insensitive, which is why it looks
  good; it says nothing about performance at the operating point a clinic would
  use. For rare outcomes, AUPRC is the more informative curve.
- **Calibration** is routinely ignored and clinically critical. A model that
  ranks well but outputs 0.9 for 30%-risk patients cannot support a decision.
  Look for a calibration plot, slope and intercept, or Brier score.
- **Dice/IoU** on small structures punish boundary error harshly; a Dice of 0.75
  on a 4 mm lesion may be excellent, on a liver it is poor. Context-free Dice
  comparisons across papers are invalid.
- **Net benefit / decision curve analysis** answers "would using this help?"
  better than any discrimination metric. Its absence is worth noting.
- **Metrics without a per-subgroup breakdown** hide performance collapse on
  skin tone, sex, age, scanner vendor or site. Ask for it.

---

## 6. Statistics that do not survive scrutiny

- **No uncertainty interval.** A single point estimate from one test split has
  unknown variance. For ML: multiple seeds, reported mean ± std. For clinical:
  95% CI. A difference between two numbers with overlapping CIs is not a result.
- **Single test split, small n.** With a 200-case test set, a 2-point accuracy
  gap is noise.
- **Multiple comparisons unaccounted for.** Twenty subgroups, one significant
  finding, no correction — that is the expected yield of chance.
- **Optimistic internal validation.** Cross-validation that includes feature
  selection or hyperparameter tuning *inside* the loop is not validation.
  Nested CV, or a held-out set, or neither.
- **p < 0.05 as the finding.** Report effect size. A statistically significant
  AUC gain of 0.004 is irrelevant to anyone.
- **Post-hoc outcome switching.** Compare against the registered protocol
  (ClinicalTrials.gov, ReBEC) when one exists; discrepancies are common and
  reportable.
- **Survivor/selection effects.** Excluded cases are information. Who was
  dropped for "poor image quality", and would they have been dropped in a clinic?

---

## 7. Reproducibility and availability

Check and report, concretely:

- Code public? Does it include training, or only inference?
- Data public, on request, or private? "Available from the corresponding author
  on reasonable request" means, empirically, unavailable.
- Exact data version, splits and preprocessing specified — can someone else
  rebuild the same test set?
- Model weights, hyperparameters, random seeds, compute, training time.
- For clinical models: a model card or equivalent, stating intended use and
  out-of-scope use.
- Was the dataset used as intended by its licence? Many medical datasets forbid
  commercial or redistributive use (see `references/datasets-benchmarks.md`).

A paper whose claims cannot be rebuilt is a hypothesis with a press release.
Say it more politely than that, but say it.

---

## 8. LLM- and foundation-model-specific checks

Newer, and reviewers often miss these:

- **Contamination.** Was the benchmark or clinical corpus plausibly in the
  pretraining data? For public benchmarks released before the model's cutoff,
  assume contamination until argued otherwise.
- **Unpinned model.** "GPT-4" without a version and date is irreproducible —
  the endpoint changes underneath the paper.
- **Prompt and decoding undisclosed.** Prompts, temperature, seed, and number of
  samples decide the result; omitting them makes the number unverifiable.
- **Single-run evaluation** of a stochastic system, reported as a point value.
- **LLM-as-judge** without human agreement statistics, or judged by a sibling of
  the model under evaluation.
- **Clinical hallucination** measured on exam questions rather than on patient
  cases — USMLE performance is not clinical safety evidence.
- **Human-comparison framing.** "Outperformed clinicians" usually means
  clinicians working without their usual context, images, history or colleagues.
  Check what the humans were allowed to see.

---

## 9. Writing the appraisal

Structure that respects the reader's time:

```
Verdict        One or two sentences. What the paper does and does not establish.
Strongest      What genuinely holds up — be fair; a hostile read is not a rigorous one.
Key limitation The one that most constrains the claim, with the specific evidence.
Other concerns Ranked, brief.
What would change my mind  The concrete study or data that would settle it.
Confidence     Yours, and why — abstract-only? field outside your depth?
```

Two habits that separate an advisor from a critic: say what the authors did
well, and always end with what *would* work. The purpose is a better next
study, not a demonstration of scepticism.
