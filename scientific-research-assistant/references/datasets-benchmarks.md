# Datasets, benchmarks and metrics

Read this when choosing data to work on, judging the data a paper used, or
deciding what counts as a fair evaluation.

**Contents**
1. How to recommend a dataset
2. Common datasets by modality
3. Access tiers and what licences actually forbid
4. Label quality — the thing nobody checks
5. Leakage, duplicates and shortcuts
6. Choosing a benchmark without inheriting its bias
7. Choosing metrics
8. Brazilian and non-US data sources

> Dataset terms, sizes and availability change. Treat the entries below as
> pointers for *where to look*, and verify the current licence, access process
> and version on the official page before advising anyone to rely on it. Never
> state a dataset's size or licence from memory in a deliverable.

---

## 1. How to recommend a dataset

Answer five questions before naming anything:

1. **Does it contain the task's label at all**, or only something adjacent that
   the user would have to re-derive?
2. **Does its population resemble the deployment population** — age, sex, skin
   tone, comorbidity, disease prevalence, country, care setting?
3. **Can this person actually get it?** Credentialed datasets take weeks to
   months and sometimes an institutional signature. For a 3-month project that
   is disqualifying, regardless of fit.
4. **Does the licence permit the intended use** — commercial? redistribution?
   model weights released? sending text to a third-party API?
5. **Is there a standard split and protocol**, and will the user use it? Custom
   splits make results incomparable to the literature, which usually defeats the
   point of using a public dataset.

If a public dataset does not fit, say so and discuss collecting data as a real
project with its own cost — not as a footnote.

---

## 2. Common datasets by modality

Starting points, not a catalogue. Verify everything at the source.

**Chest radiography** — MIMIC-CXR (credentialed, PhysioNet; paired reports),
CheXpert, NIH ChestX-ray14, PadChest (Spanish reports), VinDr-CXR
(radiologist-annotated bounding boxes).

**CT / MRI / volumetric** — Medical Segmentation Decathlon, BraTS (brain
tumour), LIDC-IDRI and NLST (lung nodules, screening), TCIA as the umbrella
archive for many oncology collections, AMOS and TotalSegmentator for
multi-organ segmentation.

**Neuroimaging** — ADNI (Alzheimer's, application required), OASIS, ABIDE,
OpenNeuro, HCP.

**Pathology** — CAMELYON16/17 (lymph node metastasis, whole-slide), TCGA via
GDC, PANDA (prostate grading).

**Ophthalmology** — EyePACS / Kaggle DR, MESSIDOR, DRIVE and STARE (vessel
segmentation), ODIR.

**Dermatology** — ISIC archive and HAM10000; **Fitzpatrick17k** and DDI exist
specifically because the others under-represent dark skin — cite that when skin
tone fairness is the question.

**Mammography** — CBIS-DDSM, INbreast, RSNA screening challenge data.

**Endoscopy / ultrasound / echo** — HyperKvasir, Kvasir-SEG, EchoNet-Dynamic,
BUSI.

**Biomedical signals** — PhysioNet is the hub: PTB-XL and MIT-BIH (ECG),
Sleep-EDF and SHHS (polysomnography), CHB-MIT and TUH EEG (EEG), plus the
annual PhysioNet/CinC Challenges, which come with a defined evaluation protocol
worth reusing.

**EHR / tabular / time series** — MIMIC-IV, eICU-CRD, HiRID, and national
registries. The UK Biobank is deep and multimodal but requires a paid
application and takes months.

**Clinical text** — MIMIC notes, the n2c2/i2b2 shared tasks (de-identification,
relations, medication extraction), emrQA. For Portuguese, see §8.

**Medical QA / LLM benchmarks** — MedQA (USMLE), MedMCQA, PubMedQA, MMLU
clinical subsets, HealthBench-style evaluations. Treat exam performance as
exam performance; it is not clinical safety evidence.

**Prototyping** — MedMNIST is fine for pipeline debugging and teaching, and is
not evidence of anything clinical. Say that when it appears as a paper's main
result.

---

## 3. Access tiers and what licences actually forbid

| Tier | Examples | Practical reality |
|---|---|---|
| Open | NIH ChestX-ray14, HAM10000, many Kaggle sets | Download now; still check the licence |
| Registered | ISIC, some TCIA collections | Account, click-through terms |
| Credentialed | MIMIC-*, eICU, many PhysioNet sets | Ethics/CITI training + signed DUA; weeks |
| Application | ADNI, UK Biobank, NLST | Research proposal reviewed; months; sometimes fees |
| Institutional / private | Hospital partner data | Ethics committee + data agreement; the slowest path |

**The licence clauses that actually bite:**

- **Non-commercial (CC BY-NC and similar)** — blocks a startup path. Ask the
  user about commercial intent *before* recommending the dataset, not after
  they have trained on it.
- **No redistribution** — you cannot republish images, and often cannot publish
  derived data or a processed copy. Affects reproducibility packages directly.
- **No re-identification attempts**, standard in every health DUA.
- **No sharing with third parties.** This is the clause people breach without
  noticing: sending credentialed clinical data to a hosted LLM or cloud vision
  API is sharing with a third party. PhysioNet has issued explicit guidance
  restricting the use of its credentialed data with online third-party APIs.
  Flag this whenever someone proposes "MIMIC notes + GPT/Claude API". The
  compliant routes are local/self-hosted models or an approved environment.
- **Model-weight restrictions** — some agreements constrain releasing models
  trained on the data.
- **Citation and acknowledgement requirements** — minor, but a condition.

When data touches Brazilian patients, licence compliance is not the whole story:
see `references/ethics-data.md` for LGPD and CEP/CONEP.

---

## 4. Label quality — the thing nobody checks

A model cannot be better than its reference standard, and medical labels are
weaker than they look.

- **NLP-mined labels.** Several large radiology datasets derive labels from
  report text with rule-based or model extractors. Error rates are material,
  and benchmark ceilings reflect label noise, not model capability. A reported
  gain inside the noise band is not a gain.
- **Single-reader ground truth.** Radiologist agreement on many findings is
  moderate. Without multi-reader consensus or a follow-up/biopsy standard, the
  "truth" has its own variance — ask for the inter-rater statistic.
- **The reference standard may be the wrong one.** If the label is "what the
  clinician wrote", the model learns clinician behaviour, including clinician
  error. Outcome-based labels (biopsy, 5-year follow-up) are stronger and rarer.
- **Label definitions drift between datasets.** "Pneumonia" in one set is not
  "pneumonia" in another, so cross-dataset numbers are often incomparable.
- **Missingness is informative.** In EHR data, that a test was ordered carries
  prognostic signal — models exploit it, and it does not transfer across
  hospitals with different ordering habits.

---

## 5. Leakage, duplicates and shortcuts

Check these in the user's plan and in any paper under appraisal:

- **Patient-level splitting.** Multiple studies per patient are the norm; split
  by patient ID, always. Several published datasets contain patient overlap
  between their own official splits — verify rather than assume.
- **Duplicate and near-duplicate images** across sources, especially in
  aggregated sets.
- **Overlap between datasets.** Some public sets re-package others; training on
  A and testing on B can be training and testing on the same images.
- **Preprocessing fitted before splitting** — normalization statistics,
  resampling, feature selection, imputation.
- **Test-set-guided choices** — architecture, early stopping, threshold.
- **Shortcut learning.** The canonical case: models detecting pneumothorax
  partly from the chest tube that treats it. Others: laterality markers, burned-in
  text, scanner/vendor signature, and source-mixing (a COVID set where positives
  and negatives come from different hospitals or different age groups lets the
  model classify the *source*). Whenever classes correlate with acquisition,
  suspect this first.
- **Temporal leakage** in EHR work: using variables recorded after the
  prediction time, including the outcome's own treatment.

The practical test for a shortcut: performance that survives aggressive
cropping, or collapses under a site/scanner change, tells you what the model
is reading.

---

## 6. Choosing a benchmark without inheriting its bias

- **Use the official split and protocol.** Custom splits produce numbers no one
  can compare, and comparisons are the only reason to use a benchmark.
- **A saturated benchmark measures overfitting to itself.** When the top entries
  sit within noise of each other, improvements there carry little information.
- **One benchmark is one population.** Generalization claims need a second,
  differently-sourced set — ideally a different country, vendor or care setting.
- **Check the ceiling.** Human or inter-rater agreement on the task bounds what
  any model can score; exceeding it usually means leakage or label artefacts.
- **For medical imaging, nnU-Net is the baseline to beat** in segmentation; a
  new architecture that does not compare against a properly tuned nnU-Net has
  not been evaluated. The general principle: a well-tuned standard method is a
  much stronger comparator than an untuned exotic one.
- **Report multiple seeds with variance.** Benchmark deltas smaller than seed
  variance are not findings.

---

## 7. Choosing metrics

Pick the metric from the decision, not from convention.

- **Screening** (missing a case is costly): sensitivity at a fixed, clinically
  acceptable specificity; expect and report the false-positive burden at
  deployment prevalence.
- **Rule-in / confirmation**: specificity and PPV at the real prevalence.
- **Rare outcomes**: AUPRC alongside AUROC; AUROC flatters rare-event models.
- **Risk scores used for decisions**: calibration (plot, slope, intercept,
  Brier) is as important as discrimination, and net benefit / decision-curve
  analysis answers the actual question.
- **Segmentation**: Dice plus a boundary metric (HD95 or surface distance), and
  report per-structure — mean Dice across unequal structures hides failure.
- **Detection**: mAP is the vision convention, but clinically, sensitivity per
  lesion at a stated false-positives-per-image rate is what a radiologist needs.
- **Always**: uncertainty intervals, and a per-subgroup breakdown over the
  attributes where failure would matter (sex, age, skin tone, site, device).

Define the primary metric before the experiment and say so. See
`references/appraisal.md` §5 for how these go wrong in published work.

---

## 8. Brazilian and non-US data sources

Relevant when the work targets Brazilian practice, and under-used:

- **DATASUS / OpenDataSUS** — national administrative and surveillance data
  (SIH hospitalizations, SIM mortality, SINAN notifications, SIVEP-Gripe). Huge,
  population-level, public, and weak on clinical detail; excellent for
  epidemiology and health-services questions.
- **ReBEC** — Brazilian clinical trial registry.
- **SciELO and LILACS** — Latin American literature and, for NLP, a corpus of
  Portuguese scientific text.
- **Hospital partnerships** — for most clinical ML in Brazil this is the real
  data source. It requires CEP/CONEP approval, an institutional agreement and a
  named local investigator; budget months, and see `references/ethics-data.md`.

A model validated only on US or European data has an untested generalization
claim for Brazilian populations and equipment — that gap is itself a legitimate,
fundable research contribution (see `references/gap-and-proposal.md` §1).
