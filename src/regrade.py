"""Regrade a saved run against the current task gold. No model calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.grader import format_summary, grade, summarize

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    records = []
    for line in args.run.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except Exception:
            continue
        task = json.loads((TASKS / f"{record['task']}.json").read_text())
        record["grade"] = grade(
            task,
            "recognition" if record["condition"] == "recognition" else "production",
            record.get("raw") or "",
        )
        records.append(record)

    summary = summarize(records)
    out = args.out or args.run.with_name(args.run.stem + "_regraded.json")
    out.write_text(
        json.dumps({"run_id": out.stem, "summary": summary, "records": records}, indent=2),
        encoding="utf-8",
    )
    print(format_summary(summary))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
