#!/usr/bin/env python3
"""Verify that references actually exist, and that they say what you think.

Give it DOIs, arXiv IDs, PMIDs, titles or raw bibliography lines. Each one is
looked up against Crossref, Europe PMC, OpenAlex or arXiv and comes back as:

  VERIFIED   record found and its title matches what you supplied
  MISMATCH   the identifier resolves, but to a different paper -- the dangerous
             case, because the citation looks right and points somewhere else
  UNCERTAIN  a plausible match with imperfect title agreement; read it yourself
  NOT FOUND  nothing in these indexes matches; do not cite it
  UNRESOLVED the lookup itself failed (rate limit, timeout, outage). This is
             NOT evidence about the citation -- retry before judging it. The
             distinction matters: treating a 429 as NOT FOUND would accuse a
             real paper of being fabricated.

Run this before any deliverable that contains citations. A fabricated or
drifted reference is the one error in research assistance that destroys trust
entirely, and it costs seconds to rule out.

Usage
-----
  python verify_refs.py "10.1038/s41586-021-03819-2"
  python verify_refs.py "Attention is all you need" "arXiv:1706.03762"
  python verify_refs.py --file refs.txt
  cat refs.txt | python verify_refs.py
  python verify_refs.py --file refs.txt --json

Exit codes: 0 = everything verified, 1 = at least one not VERIFIED, 2 = usage
error. The non-zero exit makes it usable as a gate before publishing output.

Note: absence from these indexes is not proof a work does not exist -- books,
theses, local journals and some conference proceedings are indexed poorly.
NOT FOUND means "unverifiable here", which is still a reason not to assert it.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "scientific-research-assistant/1.0 (Claude Code skill; reference verification)"
TIMEOUT = 30
# Deliberately strict. A false VERIFIED is the expensive error here: it puts a
# wrong citation into a deliverable with a confident label. A false UNCERTAIN
# only costs the reader ten seconds of checking. Near-miss titles ("Attention
# is all you need" vs "Is Attention All You Need?") score ~0.88, so the bar
# sits above that.
STRONG, WEAK = 0.93, 0.60

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>,;]+)", re.I)
ARXIV_RE = re.compile(r"\barxiv[:\s/]*((?:\d{4}\.\d{4,5})(?:v\d+)?|[a-z-]+(?:\.[A-Z]{2})?/\d{7})", re.I)
BARE_ARXIV_RE = re.compile(r"^\s*(\d{4}\.\d{4,5})(v\d+)?\s*$")
PMID_RE = re.compile(r"\bpmid[:\s]*(\d{6,8})\b", re.I)


# --------------------------------------------------------------------------- io


# Set when a lookup failed for transport reasons (rate limit, timeout, outage)
# rather than because the index had no such record. Keeping these apart matters:
# reporting a rate-limited lookup as NOT FOUND would accuse a real citation of
# being fabricated, which is exactly the judgement this script exists to make
# reliable.
NET_FAIL: list[str] = []


def _get(url: str, accept: str = "application/json") -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None  # a real "no such record"
            if exc.code in (429, 503) and attempt < 3:
                time.sleep(4 * (attempt + 1))  # arXiv in particular needs real backoff
                continue
            NET_FAIL.append(f"{host}: HTTP {exc.code}")
            return None
        except Exception as exc:
            if attempt < 3:
                time.sleep(2)
                continue
            NET_FAIL.append(f"{host}: {type(exc).__name__}")
            return None
    return None


def _json(url: str) -> dict | None:
    raw = _get(url)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------- helpers


def clean(text) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(text))).strip()


def norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", clean(title).lower()).strip()


def similarity(a: str, b: str) -> float:
    a, b = norm_title(a), norm_title(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def strip_identifiers(text: str) -> str:
    """What is left of a citation line once IDs and years are removed."""
    text = DOI_RE.sub(" ", text)
    text = ARXIV_RE.sub(" ", text)
    text = PMID_RE.sub(" ", text)
    return clean(text)


def guess_title(citation: str) -> str:
    """Pull the most title-like span out of a raw bibliography line.

    Heuristic on purpose: bibliography formats vary too much to parse, and the
    cost of a slightly wrong span is only a weaker similarity score, which the
    UNCERTAIN verdict already handles.
    """
    text = strip_identifiers(citation)
    quoted = re.findall(r'["“]([^"”]{15,})["”]', text)
    if quoted:
        return quoted[0]
    # typical pattern: Authors (Year). Title. Venue.
    after_year = re.split(r"\(?(?:19|20)\d{2}\)?\.?", text, maxsplit=1)
    candidates = after_year[-1] if len(after_year) > 1 else text
    parts = [p.strip() for p in re.split(r"(?<=[a-z0-9])\.\s+", candidates) if len(p.strip()) > 15]
    return parts[0] if parts else clean(candidates) or text


# ---------------------------------------------------------------------- lookups


def by_doi(doi: str) -> dict | None:
    data = _json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
    if data and data.get("message"):
        m = data["message"]
        issued = (m.get("issued") or {}).get("date-parts") or [[None]]
        return {
            "title": clean((m.get("title") or [""])[0]),
            "year": issued[0][0] if issued and issued[0] else None,
            "venue": clean((m.get("container-title") or [""])[0] or m.get("publisher")),
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in m.get("author", [])][:5],
            "doi": (m.get("DOI") or "").lower(),
            "url": m.get("URL") or f"https://doi.org/{doi}",
            "type": m.get("type"),
            "is_preprint": m.get("type") == "posted-content",
            "index": "crossref",
        }
    # Crossref misses some DataCite/preprint DOIs; OpenAlex often has them
    data = _json(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
    if data and data.get("display_name"):
        loc = (data.get("primary_location") or {}).get("source") or {}
        return {
            "title": clean(data["display_name"]),
            "year": data.get("publication_year"),
            "venue": clean(loc.get("display_name")),
            "authors": [a.get("author", {}).get("display_name") for a in data.get("authorships", [])][:5],
            "doi": doi.lower(),
            "url": data.get("doi"),
            "type": data.get("type"),
            "is_preprint": data.get("type") == "preprint",
            "index": "openalex",
        }
    return None


def by_arxiv(arxiv_id: str) -> dict | None:
    """arXiv's own API throttles aggressively (HTTP 429) and will lock out a
    batch of lookups. Every arXiv paper also carries a DataCite DOI of the form
    10.48550/arXiv.<id>, which OpenAlex indexes, so try that first and keep the
    arXiv API as the fallback. This turns a rate-limited run into a verified
    one instead of a wall of UNRESOLVED."""
    bare = re.sub(r"v\d+$", "", arxiv_id)
    via_doi = by_doi(f"10.48550/arxiv.{bare}")
    if via_doi:
        via_doi["is_preprint"] = True
        return via_doi

    raw = _get(
        "http://export.arxiv.org/api/query?"
        + urllib.parse.urlencode({"id_list": arxiv_id, "max_results": "1"}),
        "application/atom+xml",
    )
    if not raw:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        entry = ET.fromstring(raw).find("a:entry", ns)
    except ET.ParseError:
        return None
    if entry is None or entry.findtext("a:title", default="", namespaces=ns) in ("", "Error"):
        return None
    return {
        "title": clean(entry.findtext("a:title", default="", namespaces=ns)),
        "year": int((entry.findtext("a:published", default="0000", namespaces=ns) or "0000")[:4]) or None,
        "venue": "arXiv (preprint)",
        "authors": [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)][:5],
        "doi": (entry.findtext("{http://arxiv.org/schemas/atom}doi", default="") or "").lower() or None,
        "url": entry.findtext("a:id", default=None, namespaces=ns),
        "type": "preprint",
        "is_preprint": True,
        "index": "arxiv",
    }


def by_pmid(pmid: str) -> dict | None:
    data = _json(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
        + urllib.parse.urlencode({"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json", "resultType": "core"})
    )
    results = ((data or {}).get("resultList") or {}).get("result") or []
    if not results:
        return None
    r = results[0]
    return {
        "title": clean(r.get("title")),
        "year": r.get("pubYear"),
        "venue": clean(r.get("journalTitle") or ((r.get("journalInfo") or {}).get("journal") or {}).get("title")),
        "authors": [a.strip() for a in (r.get("authorString") or "").split(",") if a.strip()][:5],
        "doi": (r.get("doi") or "").lower() or None,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "type": r.get("pubType"),
        "is_preprint": r.get("source") == "PPR",
        "index": "europepmc",
    }


def by_title(title: str) -> dict | None:
    """Best candidate for a free-text citation, across Crossref then Europe PMC."""
    best = None
    data = _json(
        "https://api.crossref.org/works?"
        + urllib.parse.urlencode({"query.bibliographic": title, "rows": "5"})
    )
    for it in ((data or {}).get("message") or {}).get("items", []):
        cand_title = clean((it.get("title") or [""])[0])
        score = similarity(title, cand_title)
        if best is None or score > best[0]:
            issued = (it.get("issued") or {}).get("date-parts") or [[None]]
            best = (score, {
                "title": cand_title,
                "year": issued[0][0] if issued and issued[0] else None,
                "venue": clean((it.get("container-title") or [""])[0] or it.get("publisher")),
                "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])][:5],
                "doi": (it.get("DOI") or "").lower() or None,
                "url": it.get("URL"),
                "type": it.get("type"),
                "is_preprint": it.get("type") == "posted-content",
                "index": "crossref",
            })

    if best is None or best[0] < STRONG:
        data = _json(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
            + urllib.parse.urlencode(
                {"query": f'TITLE:"{title}"', "format": "json", "resultType": "core", "pageSize": "5"}
            )
        )
        for r in ((data or {}).get("resultList") or {}).get("result", []):
            cand_title = clean(r.get("title"))
            score = similarity(title, cand_title)
            if best is None or score > best[0]:
                best = (score, {
                    "title": cand_title,
                    "year": r.get("pubYear"),
                    "venue": clean(r.get("journalTitle")
                                   or ((r.get("journalInfo") or {}).get("journal") or {}).get("title")),
                    "authors": [a.strip() for a in (r.get("authorString") or "").split(",") if a.strip()][:5],
                    "doi": (r.get("doi") or "").lower() or None,
                    "url": (f"https://doi.org/{r.get('doi')}" if r.get("doi")
                            else f"https://pubmed.ncbi.nlm.nih.gov/{r.get('pmid')}/" if r.get("pmid")
                            else None),
                    "type": r.get("pubType"),
                    "is_preprint": r.get("source") == "PPR",
                    "index": "europepmc",
                })

    # Crossref indexes conference proceedings (NeurIPS, CVPR, ICML) poorly and
    # Europe PMC is biomedical-only, so a core ML paper can be missed by both.
    # OpenAlex covers that ground and is the tie-breaker.
    if best is None or best[0] < STRONG:
        data = _json(
            "https://api.openalex.org/works?"
            + urllib.parse.urlencode({"search": title, "per-page": "5"})
        )
        for w in (data or {}).get("results", []):
            cand_title = clean(w.get("display_name"))
            score = similarity(title, cand_title)
            if best is None or score > best[0]:
                loc = (w.get("primary_location") or {}).get("source") or {}
                best = (score, {
                    "title": cand_title,
                    "year": w.get("publication_year"),
                    "venue": clean(loc.get("display_name")),
                    "authors": [a.get("author", {}).get("display_name") for a in w.get("authorships", [])][:5],
                    "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower() or None,
                    "url": w.get("doi") or w.get("id"),
                    "type": w.get("type"),
                    "is_preprint": w.get("type") == "preprint",
                    "index": "openalex",
                })
    return best[1] | {"_score": best[0]} if best else None


# ------------------------------------------------------------------- the verdict


def verify(raw: str) -> dict:
    raw = clean(raw)
    NET_FAIL.clear()
    result = {"input": raw, "verdict": "NOT FOUND", "record": None, "note": "", "score": None}

    doi_m = DOI_RE.search(raw)
    arxiv_m = ARXIV_RE.search(raw) or BARE_ARXIV_RE.match(raw)
    pmid_m = PMID_RE.search(raw)
    claimed_title = guess_title(raw)
    identifier_only = not strip_identifiers(raw)

    record = None
    if doi_m:
        record = by_doi(doi_m.group(1).rstrip(".,;"))
        result["note"] = "looked up by DOI"
    elif arxiv_m:
        record = by_arxiv(arxiv_m.group(1))
        result["note"] = "looked up by arXiv ID"
    elif pmid_m:
        record = by_pmid(pmid_m.group(1))
        result["note"] = "looked up by PMID"
    else:
        record = by_title(claimed_title)
        result["note"] = f'searched by title: "{claimed_title}"'

    if record is None:
        if NET_FAIL:
            result["verdict"] = "UNRESOLVED"
            result["note"] += f" -- lookup FAILED ({'; '.join(dict.fromkeys(NET_FAIL))}). " \
                              "This says nothing about the citation; retry before judging it."
        return result

    result["record"] = {k: v for k, v in record.items() if not k.startswith("_")}

    if identifier_only:
        # Nothing was claimed beyond the ID, so existence is all we can confirm.
        result["verdict"] = "VERIFIED"
        result["note"] += " (identifier only -- confirm the title below is the one you meant)"
        return result

    score = record.get("_score")
    if score is None:
        score = similarity(claimed_title, record["title"])
    result["score"] = round(score, 2)

    if score >= STRONG:
        result["verdict"] = "VERIFIED"
    elif score >= WEAK:
        result["verdict"] = "UNCERTAIN"
    elif doi_m or arxiv_m or pmid_m:
        result["verdict"] = "MISMATCH"
        result["note"] += " -- the identifier resolves to a DIFFERENT paper"
    else:
        result["verdict"] = "NOT FOUND"
        result["note"] += " -- closest index match is too different to accept"
    return result


def render(res: dict) -> str:
    lines = [f"{res['verdict']:<10} {res['input'][:110]}"]
    rec = res["record"]
    if rec:
        authors = ", ".join(a for a in rec["authors"] if a)
        if len(rec["authors"]) >= 5:
            authors += " et al."
        kind = "preprint" if rec.get("is_preprint") else "peer-reviewed"
        lines.append(f"           -> {rec['title']}")
        lines.append(f"              {authors or 'authors n/a'}")
        lines.append(
            f"              {rec.get('year') or 'year n/a'} · {rec.get('venue') or 'venue n/a'} · {kind}"
        )
        lines.append(f"              {rec.get('url') or 'no link'}  [{rec.get('index')}]")
    if res["note"]:
        sim = f" · title similarity {res['score']}" if res["score"] is not None else ""
        lines.append(f"              ({res['note']}{sim})")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="*", help="DOIs, arXiv IDs, PMIDs, titles or citation lines")
    ap.add_argument("--file", help="file with one reference per line")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--delay", type=float, default=3.0,
                    help="seconds between lookups (default 3.0; arXiv throttles bursts hard)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    refs = list(args.refs)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            refs += [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    if not refs and not sys.stdin.isatty():
        refs += [ln.strip() for ln in sys.stdin if ln.strip()]
    if not refs:
        ap.error("no references given (pass them as arguments, --file, or on stdin)")

    results = []
    for i, ref in enumerate(refs):
        if i:
            time.sleep(args.delay)  # arXiv and NCBI throttle bursts; pacing beats retrying
        results.append(verify(ref))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for res in results:
            print(render(res))
            print()
        counts: dict[str, int] = {}
        for res in results:
            counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
        print(" · ".join(f"{v} {k}" for k, v in sorted(counts.items())))
        if counts.get("MISMATCH"):
            print("MISMATCH means the citation points at the wrong paper. Fix before using it.")
        if counts.get("UNRESOLVED"):
            print("UNRESOLVED means the index could not be reached -- it is NOT a finding about "
                  "the citation. Re-run those with a larger --delay before drawing any conclusion.")
        if counts.get("NOT FOUND"):
            print("NOT FOUND is not proof of non-existence (books, theses and local journals "
                  "index poorly) -- but do not assert it without another source.")

    return 0 if all(r["verdict"] == "VERIFIED" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
