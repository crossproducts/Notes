"""SEC EDGAR connector — insider (Form 4) purchase dates. Free, no key.

SEC fair-access rules: identify yourself via User-Agent, stay under 10 req/s.
Results are cached in-process; the first call for a ticker takes a while
(one request per Form 4 filing scanned).
"""

import json
import time
import urllib.request

UA = {"User-Agent": "strategy-studio-lab crossanick@gmail.com"}
_cache = {}


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
