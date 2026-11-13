"""Compare published GPU rows with a fresh, independently saved catalog sample.

Reads two JSON files and writes a non-secret audit under work/tmp. No network
requests or production snapshot writes are performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dashboard.common import write_json

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("provider", "sku", "region", "billing", "gpu_count")
VALUES = ("instance_usd_hour", "usd_per_gpu_hour")


def audit(old: dict, fresh: dict) -> dict:
    def index(payload: dict) -> dict:
        return {tuple(row.get(k) for k in KEYS): row for row in payload["rows"] if row.get("provider") == "Azure"}

    published = index(old)
    observed = index(fresh)
    matched = []
    changed = []
    for key in sorted(published.keys() & observed.keys()):
        values = {field: {"published": published[key].get(field), "fresh": observed[key].get(field)} for field in VALUES}
        record = {"key": dict(zip(KEYS, key)), "values": values,
                  "published_url": published[key].get("url"), "fresh_url": observed[key].get("url")}
        (changed if any(value["published"] != value["fresh"] for value in values.values()) else matched).append(record)
    return {
        "comparison_key": list(KEYS), "compared_values": list(VALUES),
        "published_source_url": "https://liyanqiao0106-max.github.io/hf-trend-snapshots/data/gpu/latest.json",
        "fresh_source_url": "https://prices.azure.com/api/retail/prices",
        "hardware_source_urls": sorted({row.get("hardware_url") for row in observed.values() if row.get("hardware_url")}),
        "published_snapshot_date": old.get("snapshot_date"), "fresh_snapshot_date": fresh.get("snapshot_date"),
        "published_azure_rows": len(published), "fresh_azure_rows": len(observed),
        "shared": len(matched) + len(changed), "same": len(matched), "changed": len(changed),
        "published_only": [dict(zip(KEYS, key)) for key in sorted(published.keys() - observed.keys())],
        "fresh_only_count": len(observed.keys() - published.keys()),
        "matched_rows": matched, "changed_rows": changed,
        "sample_matches": matched[:3],
        "limits": [
            "This compares official Azure retail catalog quotes for identical SKU, region, billing, GPU count and USD unit; it does not test actual invoice prices or VM availability.",
            "Azure Spot retail meter is not a real-time execution bid. A flat daily quote may be genuine; effectiveStartDate is not the observation timestamp.",
            "Lambda's sampled public page states its displayed prices take effect 2026-11-16 00:00 UTC; those nine future quotes are excluded from current rows as of 2026-11-13.",
            "RunPod/Vast API keys are not configured, so this audit cannot compare their protected catalogs."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--published", type=Path, default=ROOT / "work/tmp/gpu-pages-current.json")
    parser.add_argument("--fresh", type=Path, default=ROOT / "work/tmp/gpu-catalog-2026-11-13-current.json")
    parser.add_argument("--output", type=Path, default=ROOT / "work/tmp/gpu-audit-2026-11-13.json")
    args = parser.parse_args()
    result = audit(json.loads(args.published.read_text()), json.loads(args.fresh.read_text()))
    write_json(args.output, result)
    print(json.dumps({key: result[key] for key in ("shared", "same", "changed", "fresh_only_count")}))


if __name__ == "__main__":
    main()
