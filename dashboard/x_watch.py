from __future__ import annotations

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .common import ROOT, SCHEMA_VERSION, utc_now, write_json


SHANGHAI = ZoneInfo("Asia/Shanghai")
STATUS_RE = re.compile(r"^https://x\.com/([A-Za-z0-9_]+)/status/(\d+)$")
HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
SESSION = "ai-dashboard-x-watch"
READ_POSTS = r'''(() => {
  const primary = document.querySelector('[data-testid="primaryColumn"]');
  const body = primary?.innerText || '';
  const count = label => { const m=(label||'').match(/^[\d,]+/); return m?Number(m[0].replaceAll(',','')):null; };
  const rows = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).map(article => {
    const stamp = article.querySelector('time');
    const url = stamp?.closest('a')?.href || '';
    return {
      url,
      author: new URL(url || location.href).pathname.split('/')[1] || '',
      text: article.querySelector('[data-testid="tweetText"]')?.innerText || '',
      created_at: stamp?.getAttribute('datetime') || '',
      likes: count(article.querySelector('[data-testid="like"], [data-testid="unlike"]')?.getAttribute('aria-label')),
      views: count(article.querySelector('a[href$="/analytics"]')?.getAttribute('aria-label'))
    };
  }).filter(row => row.url && row.text);
  return {
    url: location.href,
    rows,
    empty: /No results for|没有.*结果|未找到.*结果/i.test(body),
    error: /Something went wrong|出了点问题|Rate limit exceeded|超出.*限制/i.test(body)
  };
})()'''


class ParagraphText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "p":
            self.depth += 1
        elif tag == "br" and self.depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.parts.append(data)


def load_watchlist(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or ROOT / "config/x_watchlist.json"
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    accounts = payload.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise ValueError("X 账号清单为空")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for account in accounts:
        handle = str(account.get("handle", "")).lstrip("@").strip()
        key = handle.lower()
        if not HANDLE_RE.fullmatch(handle):
            raise ValueError(f"无效 X handle: {handle}")
        if key in seen:
            raise ValueError(f"重复 X handle: {handle}")
        seen.add(key)
        result.append({
            "name": str(account.get("name") or handle),
            "handle": handle,
            "category": str(account.get("category") or "未分组"),
            "focus": str(account.get("focus") or ""),
            "priority": bool(account.get("priority")),
        })
    return result


def opencli_path() -> str:
    command = shutil.which("opencli")
    if command:
        return command
    bundled = ROOT / "work/node-runtime/opencli-command/opencli"
    if bundled.exists():
        return str(bundled)
    raise RuntimeError("找不到 opencli；请先安装并运行 opencli doctor")


def browser(command: str, *args: str, timeout: int = 70) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [opencli_path(), "browser", SESSION, command, *args],
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def browser_search(query: str, limit: int) -> tuple[list[dict[str, Any]], str, str]:
    url = "https://x.com/search?" + urllib.parse.urlencode({"q": query, "src": "typed_query", "f": "live"})
    found: dict[str, dict[str, Any]] = {}
    for attempt in range(2):
        try:
            opened = browser("open", url)
            if opened.returncode:
                code = "bridge_required" if opened.returncode == 69 else "error"
                return [], code, "无法通过 OpenCLI 打开 X 搜索页"
            browser("wait", "selector", 'article[data-testid="tweet"]', "--timeout", "18000")
            browser("state")
            stagnant = 0
            for _ in range(35):
                result = browser("eval", READ_POSTS)
                if result.returncode:
                    break
                payload = json.loads(result.stdout)
                if "/i/flow/login" in payload.get("url", ""):
                    return [], "auth_required", "主 Chrome 的 X 登录已失效"
                before = len(found)
                for row in payload.get("rows", []):
                    found[row["url"]] = row
                if payload.get("empty") or len(found) >= limit:
                    return list(found.values())[:limit], "ok", ""
                if payload.get("error") and not found:
                    break
                stagnant = stagnant + 1 if len(found) == before else 0
                if stagnant >= 3:
                    break
                browser("scroll", "down", "--amount", "1100")
                time.sleep(1)
            if found:
                return list(found.values())[:limit], "ok", ""
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
            pass
        if attempt == 0:
            time.sleep(2)
    return [], "error", "X 搜索页未返回动态，也未显示明确的空结果"


def oembed_text(url: str, timeout: int = 12) -> str | None:
    endpoint = "https://publish.twitter.com/oembed?" + urllib.parse.urlencode({
        "url": url, "omit_script": "true", "dnt": "true",
    })
    request = urllib.request.Request(endpoint, headers={"User-Agent": "AI-Industry-X-Watch/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())
    parser = ParagraphText()
    parser.feed(str(payload.get("html") or ""))
    text = html.unescape("".join(parser.parts)).strip()
    return re.sub(r"\n{3,}", "\n\n", text) or None


def enrich(row: dict[str, Any]) -> None:
    for attempt in range(2):
        try:
            text = oembed_text(row["url"])
            row["oembed_status"] = "ok" if text else "unavailable"
            if text and len(text) > len(row["text"]):
                row["text"] = text
                row["text_source"] = "oembed"
            return
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            if attempt == 0:
                time.sleep(0.8)
    row["oembed_status"] = "unavailable"


def save_payload(payload: dict[str, Any]) -> None:
    write_json(ROOT / "site/data/x-watch/latest.json", payload)
    # This account-only snapshot is the explicitly publishable static source
    # consumed by GitHub Pages; the broader local data directory stays ignored.
    write_json(ROOT / "site/x-watch/latest.json", payload)


def update_manifest(payload: dict[str, Any]) -> None:
    for filename in ("manifest.json", "inventory.json"):
        path = ROOT / "site/data" / filename
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {"schema_version": SCHEMA_VERSION, "modules": {}}
        modules = manifest.setdefault("modules", {})
        record = {
            "module": "x-watch", "dataset": payload["dataset"], "status": payload["status"],
            "rows": len(payload["rows"]), "last_success_at_utc": payload["generated_at_utc"],
            "snapshot_date": payload["snapshot_date"], "path": "data/x-watch/latest.json",
        }
        modules["x-watch"] = record
        if isinstance(manifest.get("sources"), list):
            manifest["sources"] = [item for item in manifest["sources"] if item.get("module") != "x-watch"] + [record]
        manifest["generated_at_utc"] = utc_now()
        manifest["snapshot_date"] = max(str(manifest.get("snapshot_date") or ""), payload["snapshot_date"])
        write_json(path, manifest)


def collect(days: int = 7, per_search: int = 100) -> dict[str, Any]:
    accounts = load_watchlist()
    now = dt.datetime.now(SHANGHAI)
    cutoff = now - dt.timedelta(days=days)
    account_map = {item["handle"].lower(): item for item in accounts}
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "dataset": "x_industry_watch",
        "status": "running",
        "generated_at_utc": utc_now(),
        "collected_at": now.isoformat(timespec="seconds"),
        "finished_at": None,
        "snapshot_date": now.date().isoformat(),
        "days": days,
        "after": cutoff.date().isoformat(),
        "accounts_count": len(accounts),
        "accounts": accounts,
        "priority_accounts_count": sum(item["priority"] for item in accounts),
        "checked_accounts": [],
        "failed_accounts": [],
        "no_activity_accounts": [],
        "returned_accounts_count": 0,
        "per_account_limit": per_search,
        "warnings": [],
        "rows": [],
        "methodology": "使用用户配置的 X 账号清单，经主 Chrome 登录态逐账号只读搜索普通 X 页面；仅查看精确近七天范围，排除回复和原生转帖，校验作者、状态链接和发布时间，去重后使用官方公开 oEmbed 复核。每个账号最多采集 100 条近七天动态；无结果账号显示本期无动态，查询失败账号单独标记。",
    }
    output = ROOT / "site/data/x-watch/latest.json"
    if output.exists():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
            if previous.get("rows"):
                stamp = now.strftime("%Y%m%d-%H%M%S")
                write_json(ROOT / f"history/x-watch/{stamp}.json", previous)
        except ValueError:
            pass
    save_payload(payload)
    candidates: dict[str, dict[str, Any]] = {}
    try:
        for offset, account in enumerate(accounts):
            query = f"from:{account['handle']} since:{cutoff.date().isoformat()} -filter:nativeretweets -filter:replies"
            rows, status, error = browser_search(query, per_search)
            print(f"account {offset + 1}/{len(accounts)} @{account['handle']}: {len(rows)} posts, {status}", flush=True)
            handles = {account["handle"].lower()}
            if status == "ok":
                payload["checked_accounts"].append(account["handle"])
            else:
                payload["failed_accounts"].append(account["handle"])
                payload["warnings"].append({"accounts": [account["handle"]], "status": status, "message": error})
                if status in ("auth_required", "bridge_required"):
                    payload["status"] = status
                    break
            for item in rows:
                match = STATUS_RE.fullmatch(str(item.get("url") or "").split("?")[0])
                text = str(item.get("text") or "").strip()
                if not match or not text or match.group(1).lower() not in handles:
                    continue
                try:
                    published = dt.datetime.fromisoformat(str(item.get("created_at") or "").replace("Z", "+00:00"))
                except ValueError:
                    continue
                if published.tzinfo is None:
                    published = published.replace(tzinfo=dt.timezone.utc)
                if published < cutoff or published > now + dt.timedelta(minutes=5):
                    continue
                account = account_map[match.group(1).lower()]
                url = f"https://x.com/{account['handle']}/status/{match.group(2)}"
                candidates[url] = {
                    "url": url, "handle": account["handle"], "account_name": account["name"],
                    "category": account["category"], "focus": account["focus"], "priority": account["priority"],
                    "text": text, "published_at": published.astimezone(SHANGHAI).isoformat(timespec="seconds"),
                    "likes": item.get("likes"), "views": item.get("views"),
                    "text_source": "chrome_dom", "oembed_status": "pending",
                }
            payload["rows"] = sorted(candidates.values(), key=lambda row: row["published_at"], reverse=True)
            payload["returned_accounts_count"] = len({row["handle"].lower() for row in payload["rows"]})
            save_payload(payload)
            time.sleep(0.4)
        present = {row["handle"].lower() for row in payload["rows"]}
        failed = {handle.lower() for handle in payload["failed_accounts"]}
        payload["no_activity_accounts"] = [
            {"name": item["name"], "handle": item["handle"], "category": item["category"]}
            for item in accounts if item["handle"].lower() not in present | failed
        ]
        if payload["status"] == "running":
            for index, row in enumerate(payload["rows"], 1):
                enrich(row)
                if index % 10 == 0:
                    print(f"oEmbed validation {index}/{len(payload['rows'])}", flush=True)
                    save_payload(payload)
            payload["status"] = "partial" if payload["failed_accounts"] else ("ok" if payload["rows"] else "empty")
    finally:
        try:
            browser("close", timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            pass
    payload["generated_at_utc"] = utc_now()
    payload["finished_at"] = dt.datetime.now(SHANGHAI).isoformat(timespec="seconds")
    save_payload(payload)
    if payload["status"] in ("ok", "partial", "empty"):
        update_manifest(payload)
    return payload


def retry_failed() -> dict[str, Any]:
    path = ROOT / "site/data/x-watch/latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    accounts = load_watchlist()
    account_map = {item["handle"].lower(): item for item in accounts}
    collected = dt.datetime.fromisoformat(payload["collected_at"])
    cutoff = collected - dt.timedelta(days=int(payload.get("days", 7)))
    failed = list(payload.get("failed_accounts", []))
    resolved: set[str] = set()
    existing_urls = {row["url"] for row in payload.get("rows", [])}
    try:
        for handle in failed:
            account = account_map.get(handle.lower())
            if not account:
                continue
            query = f"from:{account['handle']} since:{cutoff.date().isoformat()} -filter:nativeretweets -filter:replies"
            rows, status, error = browser_search(query, int(payload.get("per_account_limit", 100)))
            print(f"retry @{account['handle']}: {len(rows)} posts, {status}", flush=True)
            if status != "ok":
                continue
            resolved.add(handle.lower())
            payload["failed_accounts"] = [item for item in payload["failed_accounts"] if item.lower() != handle.lower()]
            if not any(item.lower() == handle.lower() for item in payload["checked_accounts"]):
                payload["checked_accounts"].append(account["handle"])
            for item in rows:
                match = STATUS_RE.fullmatch(str(item.get("url") or "").split("?")[0])
                if not match or match.group(1).lower() != account["handle"].lower() or not str(item.get("text") or "").strip():
                    continue
                try:
                    published = dt.datetime.fromisoformat(str(item.get("created_at") or "").replace("Z", "+00:00"))
                except ValueError:
                    continue
                if published.tzinfo is None:
                    published = published.replace(tzinfo=dt.timezone.utc)
                if published < cutoff or published > collected + dt.timedelta(minutes=5):
                    continue
                url = f"https://x.com/{account['handle']}/status/{match.group(2)}"
                if url in existing_urls:
                    continue
                existing_urls.add(url)
                payload["rows"].append({
                    "url": url, "handle": account["handle"], "account_name": account["name"],
                    "category": account["category"], "focus": account["focus"], "priority": account["priority"],
                    "text": str(item["text"]).strip(), "published_at": published.astimezone(SHANGHAI).isoformat(timespec="seconds"),
                    "likes": item.get("likes"), "views": item.get("views"),
                    "text_source": "chrome_dom", "oembed_status": "pending",
                })
        payload["rows"].sort(key=lambda row: row["published_at"], reverse=True)
        for row in payload["rows"]:
            if row.get("oembed_status") == "pending":
                enrich(row)
        present = {row["handle"].lower() for row in payload["rows"]}
        failed_set = {handle.lower() for handle in payload.get("failed_accounts", [])}
        payload["no_activity_accounts"] = [
            {"name": item["name"], "handle": item["handle"], "category": item["category"]}
            for item in accounts if item["handle"].lower() not in present | failed_set
        ]
        payload["returned_accounts_count"] = len(present)
        payload["status"] = "partial" if payload["failed_accounts"] else ("ok" if payload["rows"] else "empty")
        payload["finished_at"] = dt.datetime.now(SHANGHAI).isoformat(timespec="seconds")
        payload["generated_at_utc"] = utc_now()
        payload["warnings"] = [
            warning for warning in payload.get("warnings", [])
            if not ({str(handle).lower() for handle in warning.get("accounts", [])} & resolved)
        ]
        save_payload(payload)
        if payload["status"] in ("ok", "partial", "empty"):
            update_manifest(payload)
        return payload
    finally:
        try:
            browser("close", timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect the local Chrome-backed X watchlist snapshot.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--per-account", type=int, default=100)
    parser.add_argument("--retry-failed", action="store_true", help="只重试最近快照中的失败账号")
    args = parser.parse_args()
    if min(args.days, args.per_account) < 1:
        parser.error("days 与 per-account 必须大于 0")
    payload = retry_failed() if args.retry_failed else collect(args.days, args.per_account)
    print(json.dumps({
        "status": payload["status"], "rows": len(payload["rows"]),
        "accounts": len(payload["checked_accounts"]), "watchlist": payload["accounts_count"],
    }, ensure_ascii=False), flush=True)
    if payload["status"] not in ("ok", "partial", "empty"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
