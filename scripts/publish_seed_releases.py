from __future__ import annotations

"""One-time importer for already validated compact Hugging Face snapshots."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from weekly_dashboard import local_snapshot_refs, load_snapshot  # noqa: E402


API_VERSION = "2022-11-28"


def request_json(url: str, token: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION, "User-Agent": "hf-trend-snapshots-seed/1.0",
        **({"Content-Type": "application/json"} if body is not None else {}),
    })
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def upload_asset(upload_url: str, path: Path, token: str) -> None:
    url = upload_url.split("{")[0] + "?" + urllib.parse.urlencode({"name": path.name})
    request = urllib.request.Request(url, data=path.read_bytes(), method="POST", headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION, "User-Agent": "hf-trend-snapshots-seed/1.0",
        "Content-Type": "application/gzip" if path.suffix == ".gz" else "application/json",
    })
    with urllib.request.urlopen(request, timeout=300):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish existing validated compact snapshots as GitHub Releases once.")
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=52, help="Newest snapshots to publish (default: 52)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN")
    if not args.dry_run and not token:
        raise SystemExit("Set GH_TOKEN to a GitHub token with repository contents write permission.")

    refs = local_snapshot_refs(args.snapshot_dir)
    selected = [refs[item] for item in sorted(refs, reverse=True)[:args.limit]]
    if len(selected) < 3:
        raise SystemExit("At least three compact snapshots are required for dashboard initialization.")
    for ref in selected:
        load_snapshot(ref)
    print(f"Validated {len(selected)} snapshots: {selected[-1].snapshot_date} to {selected[0].snapshot_date}")
    if args.dry_run:
        return

    for ref in selected:
        stamp = ref.snapshot_date.strftime("%Y%m%d")
        tag = f"snapshot-{stamp}"
        try:
            release = request_json(f"https://api.github.com/repos/{args.repo}/releases/tags/{tag}", token)
            names = {asset.get("name") for asset in release.get("assets", [])}
            required = {ref.data_path.name, ref.manifest_path.name}
            if required <= names:
                print(f"{tag}: already present")
                continue
            raise RuntimeError(f"{tag} already exists but is missing one or more expected assets; fix it manually before seeding.")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise RuntimeError(f"Failed to inspect {tag}: HTTP {exc.code}") from exc

        release = request_json(f"https://api.github.com/repos/{args.repo}/releases", token, "POST", {
            "tag_name": tag, "name": f"Hugging Face snapshot {stamp}",
            "body": "Validated historical compact snapshot imported for dashboard initialization.", "make_latest": "false",
        })
        upload_url = str(release["upload_url"])
        upload_asset(upload_url, ref.data_path, token)
        upload_asset(upload_url, ref.manifest_path, token)
        print(f"{tag}: published")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
