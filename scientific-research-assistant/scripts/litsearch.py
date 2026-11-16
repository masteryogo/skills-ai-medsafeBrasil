#!/usr/bin/env python3
"""Unified literature search across open scholarly APIs (no API key required).

Queries OpenAlex, Europe PMC, Crossref, Semantic Scholar and arXiv, normalizes
the records, de-duplicates them by DOI/title and prints one comparable table.

The point is that every row here came from a live index, so nothing in the
output is recalled from a language model's memory. Cite from this, not from
recollection.

Usage
-----
  python litsearch.py "federated learning electronic health records"
  python litsearch.py "deep learning pneumothorax" --since 2022 --limit 15
  python litsearch.py "ALS eye tracking communication" --sources europepmc,openalex
  python litsearch.py "foundation model pathology" --json > hits.json

Options
-------
  --sources   comma list: openalex,europepmc,crossref,semanticscholar,arxiv
              (default: openalex,europepmc,arxiv)
  --limit     results per source (default 20)
  --since     earliest publication year
  --peer      drop records detected as preprints
  --json      emit raw JSON instead of a table
  --mailto    identify to OpenAlex/Crossref's polite pool. Only pass an address
              the user explicitly agreed to share — never their personal email
              by default.

Notes
-----
Semantic Scholar throttles unauthenticated clients aggressively; a 429 is
normal and is reported, not hidden. Coverage gaps (Scopus, Embase, Web of
Science, Google Scholar) are not reachable from here and must be disclosed in
any write-up that uses this output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "scientific-research-assistant/1.0 (Claude Code skill; literature search)"
TIMEOUT = 30
PREPRINT_HINTS = ("arxiv", "biorxiv", "medrxiv", "preprint", "ssrn", "research square")

ERRORS: list[str] = []


# --------------------------------------------------------------------------- io


def _get(url: str, accept: str = "application/json") -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            ERRORS.append(f"{urllib.parse.urlsplit(url).netloc}: HTTP {exc.code}")
            return None
        except Exception as exc:  # network, timeout, decode
            if attempt < 2:
                time.sleep(1.5)
                continue
            ERRORS.append(f"{urllib.parse.urlsplit(url).netloc}: {type(exc).__name__}")
            return None
    return None


def _json(url: str) -> dict | None:
    raw = _get(url)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        ERRORS.append(f"{urllib.parse.urlsplit(url).netloc}: invalid JSON")
        return None


# ---------------------------------------------------------------- normalization


def record(
    source: str,
    title: str | None,
    year,
    venue: str | None,
    authors: list[str] | None,
    doi: str | None,
    url: str | None,
    citations=None,
    is_preprint: bool | None = None,
) -> dict | None:
    title = clean(title)
    if not title:
        return None
    venue = clean(venue) or ""
    if is_preprint is None:
        is_preprint = any(h in venue.lower() for h in PREPRINT_HINTS)
    doi = norm_doi(doi)
    return {
        "source": source,
        "title": title,
        "year": to_year(year),
        "venue": venue,
        "authors": (authors or [])[:5],
        "doi": doi,
        "url": url or (f"https://doi.org/{doi}" if doi else None),
        "citations": citations,
        "is_preprint": bool(is_preprint),
    }


def clean(text) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(text))).strip()


def to_year(value):
    m = re.search(r"(19|20)\d{2}", str(value or ""))
    return int(m.group(0)) if m else None


def norm_doi(doi) -> str | None:
    if not doi:
        return None
    doi = str(doi).strip().lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", doi)
    return doi or None


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())[:80]


# ------------------------------------------------------------------- the sources


def search_openalex(q, limit, since, mailto):
    params = {"search": q, "per-page": str(limit)}
    if since:
        params["filter"] = f"from_publication_date:{since}-01-01"
    if mailto:
        params["mailto"] = mailto
    data = _json("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
    out = []
    for w in (data or {}).get("results", []):
        loc = (w.get("primary_location") or {}).get("source") or {}
        out.append(
            record(
                "openalex",
                w.get("display_name"),
                w.get("publication_year"),
                loc.get("display_name"),
                [a.get("author", {}).get("display_name") for a in w.get("authorships", [])],
                w.get("doi"),
                w.get("doi") or w.get("id"),
                w.get("cited_by_count"),
                is_preprint=(w.get("type") == "preprint") or None,
            )
        )
    return out


def search_europepmc(q, limit, since, _mailto=None):
    query = f"({q})" + (f" AND (FIRST_PDATE:[{since}-01-01 TO 2099-12-31])" if since else "")
    params = {"query": query, "format": "json", "resultType": "core", "pageSize": str(limit)}
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(params)
    data = _json(url)
    out = []
    for r in ((data or {}).get("resultList") or {}).get("result", []):
        pmid, pmcid = r.get("pmid"), r.get("pmcid")
        link = (
            f"https://doi.org/{norm_doi(r.get('doi'))}" if r.get("doi")
            else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid
            else f"https://europepmc.org/article/{r.get('source', 'MED')}/{r.get('id', '')}"
        )
        out.append(
            record(
                "europepmc",
                r.get("title"),
                r.get("pubYear"),
                r.get("journalTitle")
                or (((r.get("journalInfo") or {}).get("journal") or {}).get("title"))
                or (r.get("bookOrReportDetails") or {}).get("publisher"),
                [a.strip() for a in (r.get("authorString") or "").split(",") if a.strip()],
                r.get("doi"),
                link,
                r.get("citedByCount"),
                is_preprint=(r.get("source") == "PPR") or None,
            )
        )
        if out and out[-1] and pmid:
            out[-1]["pmid"] = pmid
        if out and out[-1] and pmcid:
            out[-1]["pmcid"] = pmcid
    return out


def search_crossref(q, limit, since, mailto):
    params = {"query.bibliographic": q, "rows": str(limit)}
    if since:
        params["filter"] = f"from-pub-date:{since}-01-01"
    if mailto:
        params["mailto"] = mailto
    data = _json("https://api.crossref.org/works?" + urllib.parse.urlencode(params))
    out = []
    for it in ((data or {}).get("message") or {}).get("items", []):
        issued = (it.get("issued") or {}).get("date-parts") or [[None]]
        out.append(
            record(
                "crossref",
                (it.get("title") or [None])[0],
                issued[0][0] if issued and issued[0] else None,
                (it.get("container-title") or [None])[0] or it.get("publisher"),
                [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])],
                it.get("DOI"),
                it.get("URL"),
                it.get("is-referenced-by-count"),
                is_preprint=(it.get("type") == "posted-content") or None,
            )
        )
    return out


def search_semanticscholar(q, limit, since, _mailto=None):
    params = {
        "query": q,
        "limit": str(min(limit, 100)),
        "fields": "title,year,venue,authors,externalIds,citationCount,publicationTypes",
    }
    if since:
        params["year"] = f"{since}-"
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = _json(url)
    out = []
    for p in (data or {}).get("data", []):
        ext = p.get("externalIds") or {}
        link = (
            f"https://doi.org/{norm_doi(ext.get('DOI'))}" if ext.get("DOI")
            else f"https://arxiv.org/abs/{ext['ArXiv']}" if ext.get("ArXiv")
            else f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
        )
        out.append(
            record(
                "semanticscholar",
                p.get("title"),
                p.get("year"),
                p.get("venue"),
                [a.get("name") for a in p.get("authors", [])],
                ext.get("DOI"),
                link,
                p.get("citationCount"),
            )
        )
    return out


def search_arxiv(q, limit, since, _mailto=None):
    # arXiv binds a bare `all:` prefix to the first token only, so
    # `all:eye tracking foo` degenerates into "everything", and sorting by date
    # then returns the newest arXiv submissions regardless of topic. AND the
    # terms explicitly, and let relevance do the ordering.
    terms = [t for t in re.findall(r'"[^"]+"|\S+', q) if t.strip('"')]
    search_query = " AND ".join(f"all:{t}" for t in terms) or f"all:{q}"
    params = {
        "search_query": search_query,
        "start": "0",
        "max_results": str(limit),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    raw = _get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params), "application/atom+xml")
    if raw is None:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        ERRORS.append("arxiv: invalid Atom response")
        return []
    out = []
    for e in root.findall("a:entry", ns):
        published = (e.findtext("a:published", default="", namespaces=ns) or "")
        year = to_year(published)
        if since and year and year < int(since):
            continue
        doi = e.findtext("{http://arxiv.org/schemas/atom}doi", default=None)
        out.append(
            record(
                "arxiv",
                e.findtext("a:title", default="", namespaces=ns),
                year,
                "arXiv (preprint)",
                [a.findtext("a:name", default="", namespaces=ns) for a in e.findall("a:author", ns)],
                doi,
                e.findtext("a:id", default=None, namespaces=ns),
                is_preprint=True,
            )
        )
    return out


SOURCES = {
    "openalex": search_openalex,
    "europepmc": search_europepmc,
    "crossref": search_crossref,
    "semanticscholar": search_semanticscholar,
    "arxiv": search_arxiv,
}


# ------------------------------------------------------------------------ merge


def merge(batches: list[list[dict]]) -> list[dict]:
    """Collapse duplicates, preferring the record with richer metadata."""
    seen: dict[str, dict] = {}
    for batch in batches:
        for rec in batch:
            if not rec:
                continue
            key = f"doi:{rec['doi']}" if rec["doi"] else f"ti:{title_key(rec['title'])}"
            prior = seen.get(key)
            if prior is None:
                rec["seen_in"] = [rec["source"]]
                seen[key] = rec
                continue
            prior["seen_in"].append(rec["source"])
            for field in ("doi", "venue", "year", "url", "citations", "pmid", "pmcid"):
                if not prior.get(field) and rec.get(field):
                    prior[field] = rec[field]
            # a record is a preprint only if no index reports a published venue
            if prior["is_preprint"] and not rec["is_preprint"]:
                prior["is_preprint"] = False
    out = list(seen.values())
    out.sort(key=lambda r: (r.get("year") or 0, r.get("citations") or 0), reverse=True)
    return out


def table(rows: list[dict]) -> str:
    lines = []
    for i, r in enumerate(rows, 1):
        kind = "preprint" if r["is_preprint"] else "peer-reviewed"
        authors = ", ".join(a for a in r["authors"] if a)
        if len(r["authors"]) >= 5:
            authors += " et al."
        cites = f" · {r['citations']} citations" if r.get("citations") is not None else ""
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    {authors or 'authors n/a'}")
        lines.append(
            f"    {r.get('year') or 'year n/a'} · {r['venue'] or 'venue n/a'} · {kind}{cites}"
        )
        lines.append(f"    {r.get('url') or 'no link'}   (found in: {', '.join(sorted(set(r['seen_in'])))})")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query")
    ap.add_argument("--sources", default="openalex,europepmc,arxiv")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--since", type=int, default=None)
    ap.add_argument("--peer", action="store_true", help="drop detected preprints")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mailto", default=None, help="polite-pool contact; only with user consent")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    chosen = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in chosen if s not in SOURCES]
    if unknown:
        print(f"unknown source(s): {', '.join(unknown)}. available: {', '.join(SOURCES)}", file=sys.stderr)
        return 2

    batches = [SOURCES[name](args.query, args.limit, args.since, args.mailto) for name in chosen]
    rows = merge(batches)
    if args.peer:
        rows = [r for r in rows if not r["is_preprint"]]

    if args.json:
        print(json.dumps({"query": args.query, "sources": chosen, "errors": ERRORS, "results": rows},
                         ensure_ascii=False, indent=2))
        return 0

    print(f'query: "{args.query}"')
    print(f"sources: {', '.join(chosen)}" + (f" · since {args.since}" if args.since else ""))
    print(f"{len(rows)} unique records after de-duplication\n")
    print(table(rows))
    if ERRORS:
        print("source problems (coverage is incomplete):")
        for e in dict.fromkeys(ERRORS):
            print(f"  - {e}")
    print("not searched: Scopus, Embase, Web of Science, Google Scholar (no programmatic access)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
