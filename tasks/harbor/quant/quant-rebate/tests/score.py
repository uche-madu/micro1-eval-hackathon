#!/usr/bin/env python3
"""Score the rebate aggregation task."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output/answer.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")


def number(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def score(output_path: Path, gold: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    try:
        obj = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "schema", "points": 0, "possible": 1,
                       "note": "valid answer JSON", "error": f"{type(exc).__name__}: {exc}"})
        return finish(checks, details)

    valid = isinstance(obj, dict) and "total_rebate_usd" in obj and "total_net_units" in obj
    checks.append({"name": "schema", "points": 1 if valid else 0, "possible": 1, "note": "answer JSON"})
    if not valid:
        return finish(checks, details)

    rebate = number(obj.get("total_rebate_usd"))
    rebate_ok = rebate is not None and abs(rebate - gold["total_rebate_usd"]) < 0.01
    checks.append({"name": "total_rebate", "points": 50 if rebate_ok else 0, "possible": 50,
                   "note": f"expected {gold['total_rebate_usd']}"})
    details["total_rebate"] = {"model": obj.get("total_rebate_usd"), "answer": gold["total_rebate_usd"], "ok": rebate_ok}

    units = number(obj.get("total_net_units"))
    units_ok = units is not None and abs(units - gold["total_net_units"]) < 0.01
    checks.append({"name": "total_net_units", "points": 30 if units_ok else 0, "possible": 30,
                   "note": f"expected {gold['total_net_units']}"})
    details["total_net_units"] = {"model": obj.get("total_net_units"), "answer": gold["total_net_units"], "ok": units_ok}

    excluded = obj.get("excluded_accounts")
    excluded_ok = isinstance(excluded, list) and sorted(str(x) for x in excluded) == sorted(gold["excluded_accounts"])
    checks.append({"name": "excluded_accounts", "points": 20 if excluded_ok else 0, "possible": 20,
                   "note": f"expected {gold['excluded_accounts']}"})
    details["excluded_accounts"] = {"model": excluded, "answer": gold["excluded_accounts"], "ok": excluded_ok}
    return finish(checks, details)


def finish(checks: list[dict[str, Any]], details: dict[str, Any], **extra: Any) -> dict[str, Any]:
    points = sum(check["points"] for check in checks)
    possible = sum(check["possible"] for check in checks)
    return {
        "score": round(100.0 * points / possible, 3) if possible else 0.0,
        "reward": round(points / possible, 6) if possible else 0.0,
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
        "details": details,
        **extra,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--verifier", type=Path, default=DEFAULT_VERIFIER)
    args = parser.parse_args()
    gold = json.loads(args.gold.read_text())
    result = score(args.output, gold)
    args.verifier.mkdir(parents=True, exist_ok=True)
    (args.verifier / "score.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.verifier / "reward.txt").write_text(f"{result['reward']:.6f}\n")
    print(json.dumps({"score": result["score"], "reward": result["reward"],
                      "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
