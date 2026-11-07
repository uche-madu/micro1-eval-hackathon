"""Re-grade saved Harbor audit outputs against the current scorer. No model calls."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "tasks" / "harbor" / "audit"


def load_scorer(task: str):
    path = AUDIT / task / "tests" / "score.py"
    spec = importlib.util.spec_from_file_location(f"score_{task.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    records = []
    for trial in sorted(args.job.iterdir()):
        if not trial.is_dir():
            continue
        task = trial.name.split("__")[0]
        output = trial / "agent" / "audit.json"
        if not output.exists():
            records.append({"task": task, "trial": trial.name, "error": "missing_audit"})
            continue
        gold = json.loads((AUDIT / task / "tests" / "gold.json").read_text())
        module = load_scorer(task)
        result = module.score(output, gold)
        result["task"] = task
        result["trial"] = trial.name
        records.append(result)

    groups = defaultdict(list)
    for record in records:
        if "error" in record:
            continue
        condition = "clean" if record["task"].endswith("clean") else "defective"
        groups[(args.model, condition)].append(record)

    summary = {}
    for (model, condition), items in grouped(groups):
        n = len(items)
        summary.setdefault(model, {})[condition] = {
            "n": n,
            "mean_score": round(sum(r["score"] for r in items) / n, 2),
            "pass_rate": round(sum(1 for r in items if r["reward"] >= 1.0) / n, 3),
            "false_pass_rate": round(
                sum(1 for r in items if r["details"].get("false_pass")) / n, 3
            ),
            "false_fail_rate": round(
                sum(1 for r in items if r["details"].get("false_fail")) / n, 3
            ),
            "mean_defects_matched": round(
                sum(len(r["details"].get("matched", [])) for r in items) / n, 2
            ),
            "mean_false_defects": round(
                sum(len(r["details"].get("false_defects", [])) for r in items) / n, 2
            ),
            "schema_failures": sum(1 for r in items if r["points"] == 0),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"model": args.model, "summary": summary, "records": records}, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


def grouped(groups):
    for key in sorted(groups):
        yield key, groups[key]


if __name__ == "__main__":
    main()
