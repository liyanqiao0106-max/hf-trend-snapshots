"""Read-only audit: public dashboard vs original tables and a second publisher endpoint.

Downloads and JSON evidence stay in work/tmp; never writes site/data or history.
Two publisher endpoints share TrendForce's upstream and are NOT independent
market surveys. The check verifies extraction and quote dates, not trade prices.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bs4 import BeautifulSoup
from dashboard.storage_market import parse_dramexchange, parse_samsung_ssd, SAMSUNG_SSD_URL
from dashboard.common import UA, utc_now


def download(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", required=True)
    args = parser.parse_args()
    output = ROOT / "work/tmp" / ("storage-audit-" + args.day)
    output.mkdir(parents=True, exist_ok=True)
    public_url = "https://liyanqiao0106-max.github.io/hf-trend-snapshots/data/storage/latest.json"
    public = json.loads(download(public_url))
    (output / "published.json").write_text(json.dumps(public, ensure_ascii=False), encoding="utf-8")
    raw = download("https://www.dramexchange.com/")
    (output / "original.html").write_bytes(raw)
    fresh = parse_dramexchange(raw, args.day)
    old = {row["id"]: row for row in public["rows"]}
    comparisons = [{"id": row["id"], "item": row["item"], "published_price": old.get(row["id"], {}).get("price"),
                    "source_price": row["price"], "matches": old.get(row["id"], {}).get("price") == row["price"],
                    "published_as_of": old.get(row["id"], {}).get("as_of"), "actual_quote_date": row["as_of"],
                    "observed_on": row["observed_on"]} for row in fresh]
    endpoints = []
    for name, url in [("DRAM", "https://www.trendforce.com/price/dram/dram_spot"), ("SSD", "https://www.trendforce.com/price/flash/ssd_street")]:
        try:
            body = download(url)
            (output / (name + ".html")).write_bytes(body)
            soup = BeautifulSoup(body, "html.parser")
            # Inspect leaf rows, independently of dashboard parser and columns.
            cells = [[cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"], recursive=False)] for tr in soup.find_all("tr")]
            endpoints.append({"name": name, "url": url, "status": "retrieved", "rows": [row for row in cells if len(row) >= 6]})
        except Exception as exc:
            endpoints.append({"name": name, "url": url, "status": "unavailable", "error": type(exc).__name__})
    independent = {}
    try:
        samsung = download(SAMSUNG_SSD_URL)
        (output / "samsung.html").write_bytes(samsung)
        listing = parse_samsung_ssd(samsung, args.day)[0]
        independent = {"source": SAMSUNG_SSD_URL, "official_listing": listing,
                       "street_average": next((row for row in fresh if "Samsung" in row["item"] and "990 Pro" in row["item"]), None),
                       "comparability": "Different date and market: single-store listing (possibly unavailable) vs cross-retailer average. Do not overwrite or average."}
    except Exception as exc:
        independent = {"source": SAMSUNG_SSD_URL, "status": "unavailable", "error": type(exc).__name__}
    result = {"checked_at_utc": utc_now(), "published_snapshot_date": public.get("snapshot_date"),
              "matched_prices": sum(row["matches"] for row in comparisons), "compared": len(comparisons),
              "quote_date_mismatches": sum(row["published_as_of"] != row["actual_quote_date"] for row in comparisons),
              "comparisons": comparisons, "second_endpoints": endpoints, "independent_retail_check": independent,
              "limits": "TrendForce and DRAMeXchange share a publisher. Matching extracts does not independently verify transactions. Street averages are not individual retailers' live offers; HBM cloud proxies are not chip prices."}
    (output / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output / "audit.json"), "compared": result["compared"], "matched_prices": result["matched_prices"], "quote_date_mismatches": result["quote_date_mismatches"], "second_endpoints": [{"name": x["name"], "status": x["status"]} for x in endpoints]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
