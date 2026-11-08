#!/usr/bin/env python3
"""Score the pipeline fix against a held-out CSV."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
WORKSPACE = Path("/workspace")
GOLD = json.loads((HERE / "gold.json").read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finish(checks: list[dict[str, Any]]) -> dict[str, Any]:
    points = sum(c["points"] for c in checks)
    possible = sum(c["possible"] for c in checks)
    return {
        "score": round(100.0 * points / possible, 3) if possible else 0.0,
        "reward": round(points / possible, 6) if possible else 0.0,
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
    }


def main() -> None:
    checks: list[dict[str, Any]] = []
    data = WORKSPACE / "data" / "orders.csv"
    pipeline = WORKSPACE / "pipeline.py"
    out = WORKSPACE / "out"
    holdout = HERE / "holdout.csv"

    checks.append({"name": "pipeline_exists", "points": 10 if pipeline.exists() else 0,
                   "possible": 10, "note": "/workspace/pipeline.py exists"})
    intact = data.exists() and sha(data) == GOLD.get("visible_sha256")
    checks.append({"name": "input_intact", "points": 20 if intact else 0,
                   "possible": 20, "note": "data/orders.csv not modified"})

    if not pipeline.exists():
        result = finish(checks)
        (Path("/logs/verifier")).mkdir(parents=True, exist_ok=True)
        (Path("/logs/verifier/reward.txt")).write_text(f"{result['reward']:.6f}\n")
        (Path("/logs/verifier/score.json")).write_text(json.dumps(result, indent=2) + "\n")
        return

    original = data.read_bytes() if data.exists() else b""
    run_ok = False
    output: dict[str, Any] = {}
    try:
        shutil.copyfile(holdout, data)
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["python3", "pipeline.py"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60,
        )
        run_ok = proc.returncode == 0
        summary_path = out / "summary.json"
        if summary_path.exists():
            output = json.loads(summary_path.read_text())
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "run_error", "points": 0, "possible": 1, "note": f"{type(exc).__name__}: {exc}"})
    finally:
        data.write_bytes(original)

    checks.append({"name": "run_exit_zero", "points": 20 if run_ok else 0,
                   "possible": 20, "note": "pipeline exits 0 on held-out data"})
    expected = GOLD["holdout"]
    try:
        total_ok = abs(float(output.get("total_completed_usd", -1)) - expected["total_completed_usd"]) < 0.01
    except (TypeError, ValueError):
        total_ok = False
    checks.append({"name": "total", "points": 25 if total_ok else 0, "possible": 25,
                   "note": f"expected {expected['total_completed_usd']}"})
    customers_ok = output.get("unique_completed_customers") == expected["unique_completed_customers"]
    checks.append({"name": "customers", "points": 25 if customers_ok else 0, "possible": 25,
                   "note": f"expected {expected['unique_completed_customers']}"})

    result = finish(checks)
    verifier = Path("/logs/verifier")
    verifier.mkdir(parents=True, exist_ok=True)
    (verifier / "score.json").write_text(json.dumps(result, indent=2) + "\n")
    (verifier / "reward.txt").write_text(f"{result['reward']:.6f}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
