#!/usr/bin/env python3
"""Collect hardened execution-state results from Harbor job dirs.

Usage: python3 collect.py jobs/exec2_qwen_30 [jobs/exec2_gpt_30 ...]
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
        cfg = job_dir / "config.json"
        if cfg.exists():
            config = json.loads(cfg.read_text())
        agents = config.get("agents")
        model = agents[0].get("model_name", "") if isinstance(agents, list) and agents else ""
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
                    "model": model,
                    "score": score.get("score"),
                    "final_ok": metrics.get("final_state_ok"),
                    "incorrect": metrics.get("incorrect_fields"),
                    "missing": metrics.get("missing_ops"),
                    "dupes": metrics.get("duplicate_ops"),
                    "dep_viol": metrics.get("dependency_violations"),
                    "false_state": metrics.get("false_completion_state"),
                    "false_contract": metrics.get("false_completion_contract"),
                    "reads": metrics.get("reads"),
                    "final_read": metrics.get("read_after_last_write"),
                    "retry_ok": metrics.get("retried_after_clean_ok"),
                    "retry_amb": metrics.get("retried_after_ambiguous"),
                    "retry_err": metrics.get("retried_after_precommit_error"),
                }
            )
    if not rows:
        print("no trials found")
        return
    header = ["job", "trial", "score", "final_ok", "incorrect", "missing", "dupes", "dep_viol",
              "false_state", "false_contract", "reads", "final_read", "retry_ok", "retry_amb", "retry_err"]
    print(" | ".join(header))
    print(" | ".join("---" for _ in header))
    for row in rows:
        print(" | ".join(str(row.get(key, "")) for key in header))


if __name__ == "__main__":
    main()
