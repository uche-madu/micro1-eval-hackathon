#!/usr/bin/env python3
"""Collect execution-state trial results from one or more Harbor job dirs.

Usage:
    python3 collect.py jobs/exec_qwen_pilot jobs/exec_qwen_main
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    rows = []
    for job in sys.argv[1:]:
        job_dir = Path(job)
        config = {}
        cfg_path = job_dir / "config.json"
        if cfg_path.exists():
            config = json.loads(cfg_path.read_text())
        model = ""
        agents = config.get("agents")
        if isinstance(agents, list) and agents:
            model = agents[0].get("model_name", "")
        for trial in sorted(job_dir.iterdir()):
            if not trial.is_dir() or "__" not in trial.name:
                continue
            score_path = trial / "verifier" / "score.json"
            if not score_path.exists():
                continue
            score = json.loads(score_path.read_text())
            metrics = score.get("metrics", {})
            rows.append(
                {
                    "job": job_dir.name,
                    "trial": trial.name,
                    "score": score.get("score"),
                    "dupes": metrics.get("duplicate_ops"),
                    "missing": metrics.get("missing_fields"),
                    "abandoned": metrics.get("abandoned_failures"),
                    "dep_ok": metrics.get("dependency_ok"),
                    "false_complete": metrics.get("false_completion"),
                    "reads": metrics.get("reads"),
                    "retry_ok": metrics.get("retried_after_clean_ok"),
                    "retry_amb": metrics.get("retried_after_ambiguous"),
                    "retry_err": metrics.get("retried_after_precommit_error"),
                }
            )
        if model:
            for row in rows:
                if row["job"] == job_dir.name:
                    row["model"] = model
    if not rows:
        print("no trials found")
        return
    header = ["job", "trial", "score", "dupes", "missing", "abandoned", "dep_ok", "false_complete", "reads", "retry_ok", "retry_amb", "retry_err"]
    print(" | ".join(header))
    print(" | ".join("---" for _ in header))
    for row in rows:
        print(" | ".join(str(row.get(key, "")) for key in header))


if __name__ == "__main__":
    main()
