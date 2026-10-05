from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

from .common import ROOT, SCHEMA_VERSION, archive, percentile, utc_now, write_json
from .news import collect_news
from .prices import collect_gpu, collect_models
from .storage import bundle, restore, select_spaced
from .storage_market import collect_storage
from .usage import collect_usage


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def add_model_history(payload: dict[str, Any], previous: dict[str, Any] | None, day: str) -> None:
    old = (previous or {}).get("model_history") or {}
    history: dict[str, list[dict[str, Any]]] = {}
    for row in payload["rows"]:
        points = list(old.get(row["id"], []))[-89:]
        points = [point for point in points if point.get("date") != day]
        points.append({"date": day, "input": row.get("input_usd_per_million"), "output": row.get("output_usd_per_million")})
        history[row["id"]] = points
    payload["model_history"] = history


def add_gpu_history(payload: dict[str, Any], previous: dict[str, Any] | None, day: str) -> None:
    old = (previous or {}).get("price_history") or {}
    groups: dict[str, list[float]] = {}
    for row in payload["rows"]:
        key = "|".join([row.get("provider", ""), row.get("gpu", ""), row.get("billing", "")])
        if row.get("usd_per_gpu_hour") is not None:
            groups.setdefault(key, []).append(float(row["usd_per_gpu_hour"]))
    history: dict[str, list[dict[str, Any]]] = {}
    for key, values in groups.items():
        points = [point for point in old.get(key, []) if point.get("date") != day][-89:]
        points.append({"date": day, "p25": percentile(values, .25), "median": percentile(values, .5), "p75": percentile(values, .75), "sample_count": len(values)})
        history[key] = points
    payload["price_history"] = history


def collect_hugging_face(day: str, history: Path, dist: Path, raw_paths: list[Path], reuse_hf: Path | None) -> dict[str, Any]:
    from collector import collect
    from weekly_dashboard import build_payload, load_snapshot, local_snapshot_refs, validate_payload

    if reuse_hf:
        candidates = list(reuse_hf.glob("models_*.csv.gz"))
        if len(candidates) != 1:
            raise ValueError("重用目录必须恰好有一个快照")
        data = candidates[0]
        manifest = reuse_hf / ("manifest_" + data.name[7:15] + ".json")
    else:
        data, manifest = collect(dist, snapshot_day=dt.date.fromisoformat(day))
    for path in (data, manifest):
        target = history / path.name
        shutil.copyfile(path, target)
        raw_paths.append(target)
    refs = local_snapshot_refs(history)
    selected = select_spaced(refs)
    if len(selected) < 3:
        raise ValueError("周下载加速度需要当前、约7日前、约14日前三期有效快照")
    payload = build_payload([load_snapshot(refs[value]) for value in selected])
    validate_payload(payload)
    payload.update(schema_version=SCHEMA_VERSION, snapshot_date=day, as_of=day, status="ok",
        methodology="累计下载量快照差分；完整历史模型最多450个，历史不足的观察模型最多50个。非七日间隔按实际天数折算。")
    payload.setdefault("sources", [{"name": "Hugging Face Hub official API", "url": "https://huggingface.co/api/models", "status": "ok", "tier": 1}])
    return payload


def collect_github(day: str, history: Path, raw_paths: list[Path], previous: dict[str, Any] | None, translator: Any) -> dict[str, Any]:
    from github_collector import collect
    from github_dashboard import build_payload, validate

    output = history / f"github_snapshot_{day.replace('-', '')}.json"
    collect(output, date_value=day, token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"), no_readme=True)
    raw_paths.append(output)
    payload = build_payload(json.loads(output.read_text(encoding="utf-8")))
    payload["rows"] = [row for row in payload["rows"] if not row["domain"].startswith("非AI")]
    payload["count"] = len(payload["rows"])
    if not payload["rows"]:
        raise ValueError("本期未识别 AI 相关项目")
    old = {row.get("full_name"): row for row in (previous or {}).get("rows", [])}
    for rank, row in enumerate(payload["rows"], 1):
        row["weekly_rank"] = rank
        before = old.get(row["full_name"])
        row["stars_net_change"] = row["stars"] - before["stars"] if before and isinstance(before.get("stars"), int) and isinstance(row.get("stars"), int) else None
        if translator and row.get("description_raw"):
            try:
                from .news import excerpt
                row["use_case_zh"] = "主要用于" + row["domain"] + "；简介：" + translator(excerpt(row["description_raw"], "en"))
                row["use_case_translation_status"] = "machine"
            except Exception:
                row["use_case_translation_status"] = "pending"
    payload.update(schema_version=SCHEMA_VERSION, dataset="github_ai_ecosystem", snapshot_date=day, as_of=day,
        sources=[{"name": "GitHub Trending + REST API", "url": "https://github.com/trending", "status": "ok", "tier": 1}],
        comparison_snapshot_date=(previous or {}).get("snapshot_date"),
        methodology="Trending 候选、官方仓库信息与 Stars 快照净变化；首次观察没有净变化，不将缺失值写成0。")
    payload["status"] = "partial" if any(row.get("use_case_translation_status") == "pending" for row in payload["rows"]) else "ok"
    validate(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="liyanqiao0106-max/hf-trend-snapshots")
    parser.add_argument("--skip-restore", action="store_true")
    parser.add_argument("--reuse-hf", type=Path)
    parser.add_argument("--scope", choices=("daily", "weekly", "all"), default="all")
    args = parser.parse_args()
    day = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    config = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
    history, dist = ROOT / "history", ROOT / "dist"
    history.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    statuses: list[dict[str, Any]] = []
    archives: list[dict[str, Any]] = []
    raw_paths: list[Path] = []
    if not args.skip_restore:
        try:
            restore(args.repo, ROOT, history, day, os.environ.get("GH_TOKEN"))
        except Exception as exc:
            statuses.append({"module": "restore", "status": "error", "error": str(exc), "rows": 0})
            if not (ROOT / "site/data").exists():
                raise RuntimeError("无法恢复历史看板；暂停发布") from exc
    # Restore may have populated the checkout from the most recent Release.
    # Read the manifest afterwards so a daily run retains weekly-only modules
    # (and vice versa) when both workflows publish on the same day.
    existing_manifest = read_json(ROOT / "site/data/manifest.json") or read_json(ROOT / "site/data/inventory.json") or {}

    def run(name: str, function: Callable[[dict[str, Any] | None], dict[str, Any]]) -> dict[str, Any] | None:
        path = ROOT / "site/data" / name / "latest.json"
        previous = read_json(path)
        try:
            payload = function(previous)
            if not isinstance(payload.get("rows"), list):
                raise ValueError("JSON rows 契约错误")
            write_json(path, payload)
            metadata = archive(dist, day, payload["dataset"], payload)
            archives.append(metadata)
            statuses.append({"module": name, "dataset": payload["dataset"], "status": payload.get("status", "ok"),
                "rows": len(payload["rows"]), "last_success_at_utc": payload["generated_at_utc"],
                "snapshot_date": payload.get("snapshot_date", day), "path": f"data/{name}/latest.json"})
            return payload
        except Exception as exc:
            statuses.append({"module": name, "status": "stale" if previous else "unavailable", "error": str(exc),
                "last_success_at_utc": (previous or {}).get("generated_at_utc"), "rows": len((previous or {}).get("rows", [])),
                "path": f"data/{name}/latest.json"})
            return previous

    translator = None
    if config.get("translation", {}).get("provider") not in (None, "pending"):
        try:
            from .translation import make_translator
            translator = make_translator(config["translation"], history / "translation-cache.json")
        except Exception as exc:
            statuses.append({"module": "translation", "status": "error", "error": str(exc), "rows": 0})

    if args.scope in ("daily", "all"):
        news = run("news", lambda previous: collect_news(day, config, translator, previous))
        def models(previous: dict[str, Any] | None) -> dict[str, Any]:
            payload = collect_models(day)
            add_model_history(payload, previous, day)
            return payload
        run("models", models)
        def gpu(previous: dict[str, Any] | None) -> dict[str, Any]:
            payload = collect_gpu(day, config["gpu_skus"])
            add_gpu_history(payload, previous, day)
            return payload
        gpu_payload = run("gpu", gpu)
        run("storage", lambda previous: collect_storage(day, gpu_payload, previous))

    if args.scope in ("weekly", "all"):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            try:
                from scripts.verify_openrouter import load_local_key
                key = load_local_key()
            except Exception:
                key = None
        run("token", lambda previous: collect_usage(day, key) if key else (_ for _ in ()).throw(ValueError("OPENROUTER_API_KEY 未配置")))
        run("hugging-face", lambda previous: collect_hugging_face(day, history, dist, raw_paths, args.reuse_hf))
        run("github", lambda previous: collect_github(day, history, raw_paths, previous, translator))

    if translator is not None:
        translator.save()
        if hasattr(translator, "finish"):
            try:
                translator.finish()
            except Exception as exc:
                statuses.append({"module": "translation-budget", "status": "error", "error": str(exc), "rows": 0})
        raw_paths.append(history / "translation-cache.json")

    # Keep status entries for modules untouched by this scope.
    previous_sources = existing_manifest.get("modules") or {item.get("module"): item for item in existing_manifest.get("sources", [])}
    current_names = {item.get("module") for item in statuses}
    legacy_aliases = {"token-usage": "token", "token-prices": "models", "gpu-prices": "gpu", "memory": "storage"}
    for name, item in previous_sources.items() if isinstance(previous_sources, dict) else []:
        target = legacy_aliases.get(name, name)
        if target and target not in current_names:
            statuses.append({**item, "module": target})
            current_names.add(target)
    modules = {item["module"]: item for item in statuses if item.get("module")}
    manifest = {"schema_version": SCHEMA_VERSION, "generated_at_utc": utc_now(), "snapshot_date": day,
        "schedule": config["schedule"], "scope": args.scope, "modules": modules, "terms": config["terms"],
        "history_days": config["history_days"], "translation_provider": config.get("translation", {}).get("provider", "pending")}
    write_json(ROOT / "site/data/manifest.json", manifest)
    write_json(ROOT / "site/data/inventory.json", {**manifest, "sources": list(modules.values()), "archives": archives})
    archive_path = bundle(ROOT, dist, day, raw_paths + [dist / item["file"] for item in archives])
    print(json.dumps({"bundle_bytes": archive_path.stat().st_size, "scope": args.scope, "sources": statuses}, ensure_ascii=True), flush=True)
    if not any(item.get("status") in ("ok", "partial", "stale") for item in statuses):
        raise RuntimeError("没有可发布的数据来源")


if __name__ == "__main__":
    main()
