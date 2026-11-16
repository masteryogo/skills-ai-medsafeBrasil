# Searching the literature

Read this when the task involves finding papers, assessing coverage of a topic,
or claiming something has or has not been done.

**Contents**
1. Which source answers which question
2. Open APIs (no key needed)
3. What you cannot reach, and how to say so
4. Building a query that actually recalls
5. The two-lexicon problem (clinical vs. ML)
6. Beyond keyword search: citation chasing
7. Documenting the search

---

## 1. Which source answers which question

Choosing by reputation wastes calls. Choose by what the index actually holds.

| Question | Source | Why |
|---|---|---|
| Is there clinical/biomedical evidence? | **PubMed / Europe PMC** | Curated biomedical scope, MeSH indexing, trial publication types |
| What is the newest ML method? | **arXiv** | ML publishes to arXiv first; the conference version lags 6–12 months |
| Who cites / is cited by this? | **OpenAlex**, **Semantic Scholar** | Both expose the citation graph and let you traverse it |
| Does this DOI exist, and what is it really? | **Crossref** | Authoritative DOI metadata registry |
| Can I read the full text? | **Europe PMC**, **Unpaywall**, **PMC** | Open-access full text and legal OA locations |
| Has a systematic review already covered this? | **Cochrane Library**, **PROSPERO**, **Epistemonikos** | Reviews and registered review protocols |
| Is there a trial running? | **ClinicalTrials.gov**, **ReBEC** (Brazil) | Registered, often unpublished, studies |
| Broad orientation, grey literature, blogs, leaderboards | **WebSearch** | Fast framing — never the final citation |

Europe PMC is the pragmatic default for health: it mirrors PubMed/MEDLINE, adds
preprints and full text, and its API is open and generous.

**Peer-reviewed vs. preprint matters more here than elsewhere.** arXiv and
medRxiv/bioRxiv carry much of the AI-in-health frontier *and* much of its
unreviewed overclaiming. Always label which you are citing.

---

## 2. Open APIs (no key needed)

`scripts/litsearch.py` wraps these. Use the script first; these endpoints are
here so you can go off-script when a query needs shaping.

**Identification etiquette.** OpenAlex, Crossref and Unpaywall offer a faster
"polite pool" to clients that identify themselves with an email. Never send the
user's personal email to an external service without asking. Use a generic
client identifier in the User-Agent, or ask the user whether they want their
academic email used. Unpaywall *requires* an email parameter — ask before using
it, or skip it and resolve OA through Europe PMC instead.

```
# OpenAlex — citation graph, concepts, open everything
https://api.openalex.org/works?search=<terms>&filter=from_publication_date:2023-01-01&per-page=25
https://api.openalex.org/works/doi:<doi>
https://api.openalex.org/works?filter=cites:<openalex_id>      # who cites it

# Europe PMC — biomedical, incl. preprints and full text
https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<query>&format=json&resultType=core&pageSize=25

# PubMed E-utilities — MeSH-aware, two steps
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<query>&retmode=json&retmax=50
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<ids>&retmode=json

# Crossref — DOI truth
https://api.crossref.org/works/<doi>
https://api.crossref.org/works?query.bibliographic=<title+authors>&rows=5

# Semantic Scholar — abstracts, influential citations, TLDRs
https://api.semanticscholar.org/graph/v1/paper/search?query=<terms>&fields=title,year,venue,authors,externalIds,abstract,citationCount
https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>/references?fields=title,year,externalIds

# arXiv — ML preprints
http://export.arxiv.org/api/query?search_query=all:<terms>&sortBy=submittedDate&sortOrder=descending&max_results=25

# ClinicalTrials.gov v2
https://clinicaltrials.gov/api/v2/studies?query.term=<terms>&pageSize=20
```

Rate limits are real: Semantic Scholar throttles unauthenticated clients hard,
NCBI asks for ≤3 requests/second. Batch, back off, and do not hammer in a loop.

---

## 3. What you cannot reach, and how to say so

| Source | Status |
|---|---|
| **Google Scholar** | Blocks automated access. Do not claim to have searched it. |
| **IEEE Xplore** | Full text paywalled, API needs a key; metadata often surfaces via Crossref/OpenAlex |
| **ACM DL** | Same — reachable indirectly through Crossref/OpenAlex/Semantic Scholar |
| **Scopus / Web of Science** | Subscription-only. Their coverage claims cannot be verified from here. |
| **Embase** | Subscription-only. Relevant: it indexes European/pharma literature PubMed misses. |
| **Cochrane Library** | Browsable on the web, no open API; fetch specific reviews by URL |
| **Many publisher PDFs** | Paywalled — use OA versions, or read the abstract and *say* it is abstract-only |

Say this once, plainly, in the answer: which sources you searched, which you
could not, and what that likely misses. For a formal review, the Embase and
Scopus gap is a genuine limitation worth one sentence — not a footnote to bury.

---

## 4. Building a query that actually recalls

A single natural-language string is a demo, not a search. Build it in blocks.

**Block structure** — concepts joined by AND, synonyms inside each by OR:

```
(deep learning OR convolutional OR "neural network" OR transformer)
AND ("chest radiograph" OR "chest X-ray" OR CXR OR thorax)
AND (pneumothorax OR "collapsed lung")
```

**Then iterate, deliberately:**
- Too few hits → drop the most specific block, loosen phrases to single terms,
  remove date limits, try the other lexicon (§5).
- Too many → add a design filter (RCT, systematic review), a date floor, or
  require terms in title/abstract rather than full text.
- Run at least two differently-worded queries. If both return the same core
  papers, your recall is probably reasonable. If they return disjoint sets, your
  query is the bottleneck, not the literature.

**Useful field syntax:**
- PubMed/Europe PMC: `TITLE:"..."`, `ABSTRACT:"..."`, `AUTH:"Silva J"`,
  `PUB_YEAR:[2022 TO 2026]`, `SRC:MED`, `(PUB_TYPE:"Randomized Controlled Trial")`,
  MeSH as `"Deep Learning"[MeSH]`, explosion is default — `[MeSH:noexp]` turns it off.
- arXiv: `cat:cs.CV AND abs:"federated learning"`.
- OpenAlex: `filter=type:article,is_oa:true,from_publication_date:2024-01-01`.

**MeSH deserves a moment.** MeSH terms are curated and hierarchical, so
`"Neural Networks, Computer"[MeSH]` catches papers that never wrote the phrase
you searched. Indexing lags months, though — so MeSH alone systematically misses
the newest work. Combine MeSH with free text; never rely on either alone.

---

## 5. The two-lexicon problem

This is the single highest-yield idea in this file. AI×health work lives in two
communities that cite each other rarely and name the same thing differently.
Search both or your recall is roughly half.

| Concept | Clinical / MeSH side | ML side |
|---|---|---|
| Model quality | sensitivity, specificity, PPV, NPV, calibration | accuracy, F1, AUROC, mAP, Dice |
| Testing elsewhere | external validation, multicentre | domain generalization, distribution shift, OOD |
| Finding a lesion | detection, screening, diagnostic accuracy | object detection, segmentation, anomaly detection |
| Model explanation | clinical interpretability, decision support | XAI, saliency, attention, Grad-CAM, concept bottleneck |
| Privacy-preserving collaboration | multicentre study, data governance | federated learning, differential privacy, split learning |
| Predicting outcomes | prognostic model, risk prediction, survival analysis | time-to-event modelling, sequence model, EHR foundation model |
| The data | cohort, registry, medical record, EHR | dataset, benchmark, corpus |
| Few labels | pilot study, limited sample | few-shot, self-supervised, semi-supervised |

Also translate the **disease**: lay name, clinical name, MeSH entry term and
acronym (ALS / amyotrophic lateral sclerosis / motor neuron disease / Lou
Gehrig; ELA in Portuguese sources). And remember non-English literature exists —
LILACS and SciELO carry Latin American clinical work that PubMed indexes thinly.

---

## 6. Beyond keyword search: citation chasing

Keyword search has a ceiling. Once you have 2–3 solid, on-target papers:

- **Backward** — read their related-work and reference list (Semantic Scholar
  `/references`). This finds the foundational work whose vocabulary predates yours.
- **Forward** — who cites them (`OpenAlex filter=cites:`). This finds the newest
  work, including papers that renamed the problem.
- **Sideways** — the authors' other papers, and the group's. Research is done by
  labs; one relevant paper usually implies a line of them.
- **Reviews first.** A recent systematic review or survey is a search someone
  already ran with more resources. Start there, then update it forward from its
  cutoff date — that gap is also often where the real opportunity sits.

Stop when new searches keep returning papers you have already seen. Say so
explicitly — saturation is evidence about coverage, and it is honest evidence.

---

## 7. Documenting the search

For anything beyond a casual question, report the search so the user can judge
and reproduce it. Minimal, non-bureaucratic form:

```
Searched: Europe PMC, OpenAlex, arXiv (2026-11-12)
Queries:  ("federated learning" OR "distributed training") AND (EHR OR "electronic health record")
          + MeSH variant: "Machine Learning"[MeSH] AND "Electronic Health Records"[MeSH]
Filters:  2020–present, English + Portuguese
Not searched: Scopus, Embase, Web of Science (no access) — likely misses some
          European clinical informatics work
Hits:     61 screened on title/abstract → 12 read → 9 cited below
```

If the deliverable is a formal systematic or scoping review, the reporting
standard is **PRISMA 2020** (PRISMA-ScR for scoping) — the search strategy,
screening counts and flow diagram are required, not optional. See
`references/appraisal.md` for the guideline set and when each applies.
