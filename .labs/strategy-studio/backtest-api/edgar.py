"""SEC EDGAR connector — insider (Form 4) purchase dates + 13F-HR holdings. Free, no key.

SEC fair-access rules: identify yourself via User-Agent, stay under 10 req/s.
Results are cached in-process; the first call for a ticker takes a while
(one request per Form 4 filing scanned).
"""

import json
import os
import re
import time
import urllib.request
from pathlib import Path

UA = {"User-Agent": "strategy-studio-lab crossanick@gmail.com"}
_cache = {}

# On-disk cache directory for 13F results (survives process restarts).
_CACHE_DIR = Path(os.getenv("EDGAR_CACHE_DIR", Path(__file__).parent / ".edgar_cache"))
_CACHE_DIR.mkdir(exist_ok=True)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def cik_for(ticker: str) -> str | None:
    data = json.loads(_get("https://www.sec.gov/files/company_tickers.json"))
    for v in data.values():
        if v["ticker"].upper() == ticker.upper():
            return str(v["cik_str"]).zfill(10)
    return None


def purchase_filing_dates(ticker: str, max_filings: int = 80) -> list[str]:
    """Filing dates of Form 4s containing an open-market PURCHASE (code P).
    Uses the filing date (not trade date) — that's when the public could act."""
    key = (ticker.upper(), max_filings)
    if key in _cache:
        return _cache[key]

    cik = cik_for(ticker)
    if not cik:
        return []
    subs = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    recent = subs["filings"]["recent"]

    dates, scanned = [], 0
    for form, acc, doc, fdate in zip(recent["form"], recent["accessionNumber"],
                                     recent["primaryDocument"], recent["filingDate"]):
        if form != "4" or scanned >= max_filings:
            continue
        scanned += 1
        accn = acc.replace("-", "")
        raw = doc.split("/")[-1]  # strip xsl-rendered path to reach the raw XML
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{raw}"
        try:
            xml = _get(url).decode(errors="replace")
            if "<transactionCode>P</transactionCode>" in xml:
                dates.append(fdate)
        except Exception:
            pass
        time.sleep(0.12)  # respect SEC rate limits

    _cache[key] = dates
    return dates


# ---------------------------------------------------------------------------
# 13F-HR holdings — "whale copycat" signal
# ---------------------------------------------------------------------------

def _ticker_to_name(ticker: str) -> str | None:
    """Map a ticker to a company name fragment via EDGAR's company_tickers.json."""
    data = json.loads(_get("https://www.sec.gov/files/company_tickers.json"))
    time.sleep(0.2)
    ticker_up = ticker.upper()
    for v in data.values():
        if v["ticker"].upper() == ticker_up:
            return v["title"].lower()
    return None


def thirteenf_holding_periods(fund_cik: int | str, symbol: str,
                               max_filings: int = 12) -> list[tuple[str, bool]]:
    """13F-HR filing history for a fund/symbol pair.

    For each of the fund's most recent 13F-HR filings (up to max_filings), checks
    whether `symbol` appears in the infotable holdings (matched by a case-insensitive
    substring of nameOfIssuer against the company name from company_tickers.json).

    Returns a list of (filing_date: str, held: bool) sorted ascending by date — the
    raw filing date, NOT the period-of-report end, so the public-information lag is
    already baked in (13F filers have ~45 days after quarter-end; using filing_date
    means any backtest built on this data cannot peek ahead of what the market knew).

    Results are cached per (cik, symbol) to .edgar_cache/<cik>_<symbol>.json so
    subsequent calls in the same process — or a restarted process — avoid hitting
    EDGAR again.
    """
    cik = str(fund_cik).zfill(10)
    cache_key = (cik, symbol.upper(), max_filings)

    # in-process cache
    if cache_key in _cache:
        return _cache[cache_key]

    # on-disk cache
    disk_path = _CACHE_DIR / f"{cik}_{symbol.upper()}_{max_filings}.json"
    if disk_path.exists():
        try:
            result = json.loads(disk_path.read_text())
            _cache[cache_key] = result
            return result
        except Exception:
            pass  # corrupted cache — re-fetch

    # Resolve symbol to company name for infotable matching
    try:
        issuer_name = _ticker_to_name(symbol)
    except Exception:
        issuer_name = None
    # Normalize both sides: titles say "Apple Inc." / infotables say "APPLE INC",
    # "Coca-Cola Company" vs "COCA COLA CO" — punctuation and suffixes differ, so
    # match on the leading word(s), not the full string.
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()
    name_words = _norm(issuer_name or symbol).split()
    match_token = name_words[0] if name_words else symbol.lower()

    # Fetch fund submissions
    try:
        subs = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
        time.sleep(0.2)
    except Exception as e:
        print(f"[edgar] WARNING: could not fetch CIK{cik} submissions: {e}")
        return []

    recent = subs.get("filings", {}).get("recent", {})
    forms      = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    docs       = recent.get("primaryDocument", [])
    dates      = recent.get("filingDate", [])

    results: list[tuple[str, bool]] = []
    scanned = 0

    for form, acc, doc, fdate in zip(forms, accessions, docs, dates):
        if form not in ("13F-HR", "13F-HR/A"):
            continue
        if scanned >= max_filings:
            break
        scanned += 1

        accn = acc.replace("-", "")
        cik_int = int(cik)

        # The infotable is a separate XML attachment with an ARBITRARY name
        # (e.g. '53405.xml' — never '*infotable*'). List the filing folder via
        # index.json ('{acc}-index.json' does not exist) and probe each
        # non-cover-page XML for <nameOfIssuer> tags to find the real one.
        index_url = (f"https://www.sec.gov/Archives/edgar/data/"
                     f"{cik_int}/{accn}/index.json")
        try:
            idx = json.loads(_get(index_url))
            time.sleep(0.2)
        except Exception:
            continue  # no listing — skip this filing rather than guess

        xml_names = [item.get("name", "")
                     for item in idx.get("directory", {}).get("item", [])
                     if item.get("name", "").lower().endswith(".xml")
                     and "primary_doc" not in item.get("name", "").lower()]

        held = None
        for name in xml_names:
            try:
                xml = _get(f"https://www.sec.gov/Archives/edgar/data/"
                           f"{cik_int}/{accn}/{name}").decode(errors="replace").lower()
                time.sleep(0.2)
            except Exception:
                continue
            # Match the leading company-name word against <nameOfIssuer> tags
            # (word match, not substring — 'coca' must not match 'cocaine labs')
            issuers = re.findall(r"<nameofissuer>(.*?)</nameofissuer>", xml)
            if issuers:  # this XML is the infotable
                held = any(match_token in _norm(iss).split() for iss in issuers)
                break
        if held is None:
            continue  # no parseable infotable — skip, don't fabricate a signal
        results.append((fdate, held))

    results.sort(key=lambda x: x[0])

    # Persist to disk and in-process cache
    try:
        disk_path.write_text(json.dumps(results))
    except Exception:
        pass
    _cache[cache_key] = results
    return results
