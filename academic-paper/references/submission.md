# Formatting and submission

## Start from the official template, always

Download the venue's current-year style files and build the paper inside them.
Reconstructing a layout by hand produces margin and font violations that
trigger desk rejection, and formats change between years. If the user has no
template, say which file is needed rather than approximating one.

Common families:

- **NeurIPS / ICML / ICLR** — own `.sty` per year; ICLR and NeurIPS have a
  distinct anonymous vs. camera-ready mode (`\usepackage[final]{...}`).
- **CVPR / ICCV / ECCV** — `cvpr.sty` family, numeric citations, hard page
  limit excluding references.
- **ACL / EMNLP** — `acl.sty`, natbib author-year, mandatory Limitations
  section that does not count against the page limit.
- **IEEE journals/conferences** — `IEEEtran`, two-column, `\IEEEkeywords`.
- **Springer / LNCS** — `llncs.cls`, strict on heading levels, captions above
  tables.
- **Elsevier** — `elsarticle.cls`, often single-column for review.

Verify the exact requirements against the venue's current call for papers
rather than from memory; page limits and required sections change year to year.

## Anonymity

For double-blind submission, check all of these, because each one has
de-anonymized real papers:

- No author names, affiliations, emails, or acknowledgments.
- Self-citations in third person: "Smith et al. [12] showed", never "our
  previous work [12]".
- No links to a personal or named GitHub, no project page with a lab name;
  use an anonymized repository link.
- Strip PDF metadata (author field from the LaTeX toolchain) and check
  embedded figure filenames and paths.
- Funding and ethics statements that name the institution go in camera-ready
  only.

## BibTeX hygiene

Bibliographies are where sloppiness is most visible and most mechanical to fix:

- Prefer the final published venue over the arXiv preprint when a paper has
  been published; keep arXiv only for genuinely unpublished work.
- Consistent venue naming — don't mix "NeurIPS", "Advances in Neural
  Information Processing Systems", and "NIPS" in one file.
- Protect capitalization with braces: `title = {{BERT}: Pre-training of Deep
  {B}idirectional Transformers}`, or the style will lowercase acronyms.
- Every entry needs year and venue; fill the DOI when the style prints it.
- **Verify entries against a real source.** Never generate a BibTeX entry from
  memory — a hallucinated reference survives review badly. If a citation can't
  be verified, mark it `% TODO verify` and list it in the gaps section.

## Figures and tables

- Vector formats (PDF/EPS) for plots, raster only for photographs; 300 dpi+.
- Text in figures at least as large as the caption text. A figure legible only
  at 200% zoom is a reviewer complaint.
- Readable in grayscale and under color-vision deficiency — vary markers and
  line styles, not only hue.
- Table captions above, figure captions below, per most CS conventions.
- Every float referenced in the text by number ("Figure 3 shows"), and placed
  near its first mention.

## Pre-submission checklist

Run through this and report what fails:

1. Page limit met **in the compiled PDF**, with the venue's rule on whether
   references and appendix count.
2. No LaTeX warnings for overfull boxes crossing the margin, no `??`
   references, no missing citations.
3. Abstract within the word limit of both the PDF and the submission form —
   they often differ.
4. Anonymity checks above, if double-blind.
5. Reproducibility checklist, ethics statement, broader-impact section, and
   author-contribution statement, where the venue requires them.
6. Supplementary material as a separate file in the required format, and the
   paper readable without it.
7. Spell check with a fixed dialect (US or UK, consistently), and a final
   read of the abstract and intro aloud — that's what everyone reads.
