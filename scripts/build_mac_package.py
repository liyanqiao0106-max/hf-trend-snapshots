from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a secret-free Mac migration package.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != ROOT:
        raise SystemExit("output must be placed in the project root")
    files = tracked_files()
    data_root = ROOT / "site" / "data"
    if data_root.exists():
        files.extend(path for path in data_root.rglob("*") if path.is_file())
    if any(path.name == ".env" for path in files):
        raise SystemExit("refusing to package .env")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(set(files)):
            archive.write(path, Path("AI产业看板") / path.relative_to(ROOT))
        archive.writestr(
            "AI产业看板/迁移包清单.txt",
            f"生成时间：{dt.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"Git commit：{commit}\n"
            "包含：Git 跟踪文件和打包时的 site/data 最新快照。\n"
            "排除：.git、.env、API key、work、history、dist、node_modules 和测试产物。\n",
        )
    print(f"{output.name}: {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
