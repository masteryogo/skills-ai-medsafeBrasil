# Ethics, privacy and regulation

Read this whenever the work touches patient data, human participants, or a tool
that might be used in care.

> This is research guidance, not legal advice. Norms and resolution numbers
> change — verify the current text with ANPD, CONEP, ANVISA or the user's
> institutional office before anything binding. Tell the user plainly that an
> institutional review is required; do not let them treat your summary as
> clearance.

**Contents**
1. The question to ask first
2. LGPD and health data
3. Anonymization vs. pseudonymization
4. CEP/CONEP: the Brazilian ethics route
5. De-identifying images, signals and text
6. When research becomes a medical device
7. International frames you will meet
8. Fairness and harm beyond privacy
9. Publication ethics

---

## 1. The question to ask first

Before methods, before datasets: **where does the data come from, and under
what authority is it being used?** Three cases, with very different paths:

| Case | Path |
|---|---|
| Public, already de-identified dataset | Licence/DUA compliance; ethics review often waived — but confirm with the institution, not with yourself |
| Identifiable or hospital-sourced data | CEP (and sometimes CONEP) approval, institutional data agreement, LGPD legal basis |
| New collection from participants | CEP approval + informed consent (TCLE), before any collection |

Getting this wrong is not recoverable: data collected without approval cannot
be retroactively legitimized, and journals will refuse the paper. When a user
describes a project that has already started collecting, ask about approval
immediately rather than at the end.

---

## 2. LGPD and health data

Under the **LGPD (Lei 13.709/2018)**, health data is **dado pessoal sensível**,
which narrows the lawful bases considerably. Two routes matter for research:

- **Consent** — for sensitive data it must be *specific and highlighted*, for
  stated purposes. Broad "for future research" consent is weak under the LGPD;
  where a biobank or repeated use is planned, design the consent and the
  governance around that from the start.
- **Research by an *órgão de pesquisa*** — the law provides for studies by a
  research body, with anonymization required whenever possible, and processing
  restricted to the research purpose. There is a parallel provision for public
  health studies allowing access to personal data held in a controlled, secure
  environment, used solely for the research. The practical conditions attached:
  purpose limitation, data minimization, controlled environment, no transfer to
  third parties, and anonymization or at least pseudonymization wherever
  feasible.

The conditions do the real work, and they constrain architecture:

- **Minimization** — do not pull the whole record because it is easier. Each
  field should have a stated reason to exist in the study.
- **No third-party transfer** — this covers hosted APIs. Sending identifiable
  or credentialed clinical data to an external LLM, OCR or vision service is a
  transfer. Local or self-hosted models, or a contracted environment with the
  proper agreement, are the compliant routes.
- **Security and access control**, encryption at rest and in transit, logged
  access, and a defined retention and disposal plan.
- **Controller/operator roles** named, and an incident response path.

Breaches of health data are reportable to the **ANPD**. Say this once when
designing a project; it changes where data is allowed to live.

---

## 3. Anonymization vs. pseudonymization

The distinction decides whether the LGPD applies at all, and it is routinely
misused.

- **Anonymized** — the subject cannot be identified, considering reasonable
  technical means available at the time. Truly anonymized data falls outside the
  law. The qualifier matters: if re-identification is reasonably achievable, it
  is not anonymized.
- **Pseudonymized** — identifiers replaced by a key that still exists
  somewhere. This is still personal data, still fully in scope. Most projects
  that claim anonymization are pseudonymized.

Re-identification risk in health data is higher than people assume: rare
diagnoses, dates, small geographies, long time series, genomic data and medical
images are all quasi-identifiers. A head MRI can be used to reconstruct a face.
Treat "we removed the name" as the beginning, not the end.

Be precise about which of the two the project actually achieves, and if the key
exists, say the data is personal data.

---

## 4. CEP/CONEP: the Brazilian ethics route

Human-subject research in Brazil is reviewed by the **CEP** (local committee)
through **Plataforma Brasil**, with escalation to **CONEP** for specific
categories. The framework rests on CNS **Resolução 466/2012** (and 510/2016 for
social/human sciences), with **Lei 14.874/2024** reshaping the system — verify
the current regulation and the institution's own procedure, since this is in
transition.

What to plan for, practically:

- **Timeline.** Weeks to several months. For a one-year project this is a
  scheduling fact, not a formality. Submit while writing the protocol, not after.
- **TCLE** (termo de consentimento livre e esclarecido) — written in language
  the participant actually understands. For retrospective record-based studies,
  a **dispensa de TCLE** can be requested with justification, and is commonly
  granted; it must still be requested and approved.
- **Vulnerable participants** — children, people with cognitive or
  communication impairment, hospitalized patients — require extra safeguards,
  and assent plus guardian consent where applicable. For assistive-technology
  research with participants who cannot speak or write, the consent *process*
  itself needs design: an accessible format, and a means of withdrawal the
  participant can actually use.
- **Data custody** — the protocol must state who holds the data, where, for how
  long, and what happens at the end.
- **Amendments** — scope changes (new data source, new model use) usually
  require an *emenda*; using the data for an unapproved purpose is a breach.

The committee may have no ML background. Write the protocol so a clinician or
lawyer can evaluate the risk without understanding the architecture.

---

## 5. De-identifying images, signals and text

Removing the obvious field is not de-identification.

- **DICOM** — identifiers live across many tags, including private and
  institutional ones. Use an established profile/tool rather than a hand-rolled
  tag list, and verify the output rather than trusting the pipeline.
- **Burned-in pixel text** — names and dates rendered into the image survive
  every metadata scrub. Ultrasound and some radiographs are frequent offenders.
- **Facial reconstruction** — head CT/MRI can yield a recognizable face.
  Defacing or skull-stripping is required before sharing, and it must be
  checked for effects on the downstream task.
- **Free text** — Brazilian clinical notes carry names, CPF, CNS, addresses,
  phone numbers, record numbers and dates, often malformed. Rule-based scrubbing
  alone under-performs; measure recall on a manually annotated sample and report
  it. See the `medical-nlp-ptbr` skill for the Portuguese-specific work.
- **Dates and geography** — date shifting (consistent per patient) and
  aggregation of small areas; a rare diagnosis in a small municipality is
  identifying on its own.
- **Verify, then report.** State the method and its measured residual risk in
  the paper. "De-identified" without a method is not a claim a reviewer should
  accept, and you should not write it either.

---

## 6. When research becomes a medical device

A research prototype becomes a regulated product sooner than most researchers
expect. In Brazil, software intended for diagnosis, screening, monitoring,
prediction or treatment decisions falls under **ANVISA**'s medical-device
framework, including its software-as-a-medical-device rules (see RDC 751/2022
and the SaMD-specific regulation — verify current numbering and text). Risk
class follows intended use and the consequence of error, and it determines the
evidence required.

What this means for research conversations:

- **Intended use is the regulatory pivot.** "Supports a clinician who makes the
  decision" and "produces the diagnosis" are different classes. Wording in a
  paper, a pitch or an app store listing can create a regulatory claim.
- **Claims discipline.** Research results do not authorize clinical claims.
  "Detects X with 94% accuracy on a retrospective cohort" is a research finding;
  "detects X" on a product page is a device claim. Flag the drift when you see
  it, especially in abstracts and grant texts.
- **Wellness vs. medical.** Framing a product as wellness to avoid regulation
  while marketing a diagnostic benefit is a known failure path, and auditors
  read the marketing, not the disclaimer.
- **Post-market and model updates.** Continuously learning models raise change
  control questions; regulators expect a pre-specified change plan rather than
  silent retraining.

When the user is heading toward a product, the honest advice is: decide the
intended-use statement early, because it determines the study you need.

---

## 7. International frames you will meet

- **HIPAA** (US) — its Safe Harbor method enumerates 18 identifier categories
  to remove; many public US datasets are de-identified to that standard, which
  is not automatically sufficient under the LGPD.
- **GDPR** (EU) — special-category data, with research provisions; relevant for
  European collaborations and datasets.
- **EU AI Act** — AI that is a medical device, or used in health triage, lands
  in high-risk categories with documentation, data governance and human
  oversight obligations. Expect this to shape what EU journals and partners ask.
- **FDA** (US) — SaMD pathways, and predetermined change control plans for
  models expected to update.
- **Declaration of Helsinki** — the ethical baseline journals cite; ICMJE
  journals require a statement of approval and consent.

---

## 8. Fairness and harm beyond privacy

Privacy compliance does not make a study ethical.

- **Representation.** Who is in the data, and who will the model fail? Report
  performance by subgroup, and name the groups the dataset cannot speak for.
- **Label bias.** If labels encode past clinical decisions, the model inherits
  historical inequity — including access-driven differences in who got tested.
- **Deployment harm.** A false positive costs a biopsy and months of anxiety; a
  false negative costs a missed diagnosis. Asymmetric costs should drive the
  operating point, not a default 0.5 threshold.
- **Automation bias.** Clinicians defer to confident systems. A decision-support
  tool can degrade care while scoring well offline — this is why DECIDE-AI-style
  live evaluation exists.
- **Assistive and disability contexts.** Participants are not inspiration or
  demo material. Involve them in design, measure what matters to them rather
  than what is easy to measure, and avoid claims about quality of life that the
  study did not measure.
- **Dual use and misuse** — ask what happens if the tool is used by an insurer,
  an employer, or without the clinician it assumes.

---

## 9. Publication ethics

- **Authorship** — ICMJE criteria: substantial contribution, drafting or
  critical revision, final approval, accountability. Data access alone is not
  authorship; nor is supervision without contribution. Raise this early, because
  it is poisonous late.
- **Conflicts of interest and funding** — disclose, including equity in a
  company whose product is evaluated.
- **Registration** — trials registered before enrolment (ReBEC,
  ClinicalTrials.gov); systematic reviews in PROSPERO. Many journals refuse
  unregistered trials.
- **Reporting negative results.** Suppressing them distorts the field and is the
  reason false novelty persists (`references/gap-and-proposal.md` §1).
- **Disclosure of AI assistance** in manuscript preparation is now required by
  most publishers; generative tools cannot be authors.
