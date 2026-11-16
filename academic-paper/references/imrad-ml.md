# Section-by-section: CS/ML manuscript

Read this when drafting or revising. Each section below gives the job the
section does, the shape that works, and the failure mode to avoid. Deviate when
the paper needs it — these are the defaults, not a cage.

## Title and abstract

The title states the contribution, not the topic. "Attention Is All You Need"
is a claim; "A Study of Attention Mechanisms" is a shrug.

Abstract in five moves, roughly 150-250 words, one or two sentences each:

1. **Context** - the problem, in terms a neighboring subfield understands.
2. **Gap** - what current methods cannot do. This is the sentence reviewers
   use to decide whether to care.
3. **What we do** - the method, named, in one sentence.
4. **What we find** - the headline numbers, with the baseline they beat and
   the dataset. Numbers, not adjectives.
5. **Why it matters** - the implication, sized honestly.

Failure mode: an abstract that describes the paper's *organization* ("Section 3
presents our method"). Describe the findings instead.

## Introduction - the five-paragraph shape

1. The problem matters, and here is the concrete reason.
2. Here is what has been tried, grouped into two or three approaches.
3. Here is the specific thing none of them handles - the gap, sharpened.
4. Here is what we do, and the key idea in one sentence a reader could
   reimplement the spirit of.
5. Contributions as a bulleted list. Each bullet is a thing the paper
   *demonstrates*, with a pointer to the section that demonstrates it.

Contribution bullets are claims, so they obey the claim contract: "we show X
improves Y by Z on W", never "we propose a novel framework".

## Related work - position, don't catalog

The four-move pattern per group of papers: name the approach, say what it gets
right, say precisely what it cannot do, say how this paper differs. A related
work section that reads as a list of summaries tells the reviewer the authors
don't know where they stand.

Be generous to prior work. Dismissiveness reads as insecurity and the author
you dismissed is often a reviewer.

## Method

Write so a competent graduate student could reimplement it. That means:

- Notation defined before use, consistent throughout, and a table if there is
  more than a handful of symbols.
- The problem formalized before the solution appears.
- The *idea* stated in prose before the equations. Equations confirm an
  intuition; they don't deliver one.
- Every equation's symbols explained in the surrounding text, and every
  equation numbered if it's referenced.
- Design choices justified: say why this loss, this architecture, this
  threshold. "We use X" with no reason invites "why not Y?" in review.

Failure mode: narrating the code. The method section describes the *approach*;
the hyperparameters go in experiments or an appendix.

## Experiments

Open by stating the questions the experiments answer - literally "We ask:
(Q1) does X help when Y? (Q2) ...". Then each subsection answers one.

A complete setup covers: datasets and splits (and whether the split is
standard), baselines and how they were tuned, metrics and why those metrics,
implementation details, compute budget, and number of seeds.

Table discipline:

- Caption says what the table shows and how to read it, standalone.
- Variance alongside every mean; state what the +/- is (std over seeds, CI).
- Bold the best result only when the gap exceeds the noise - and say in the
  caption what bold means.
- Same precision across a column; don't report four decimals of a number
  measured with two.

Ablations answer "which part is doing the work?". One row per removed
component, plus the full system and the simplest possible baseline.

Report the negatives. An experiment where the method ties or loses, reported
with a hypothesis about why, buys more reviewer trust than it costs.

## Discussion and limitations

Interpret, don't repeat the numbers. What does the result imply, and what
alternative explanation survives the evidence?

Limitations must name real threats: distribution shift the evaluation didn't
cover, a baseline tuned less than the method, a dataset whose labels are noisy,
a result that may not scale. A limitations section listing only things that
flatter the work ("future work could try more datasets") reads as evasive and
reviewers notice.

## Conclusion

Short. The contribution, what it showed, and one concrete next step. No new
claims, no new numbers.

## Reproducibility and ethics

Most venues require a checklist. Cover: code and data availability (and the
license), hyperparameters and search space, hardware and total compute, seeds,
and - for anything involving humans, health, or personal data - consent, IRB
or ethics-board status, and the risk of misuse. In health or assistive
applications, be explicit about what the system is *not* validated to do.
