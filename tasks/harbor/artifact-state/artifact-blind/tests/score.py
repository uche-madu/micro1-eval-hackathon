#!/usr/bin/env python3
"""Score the blind artifact-state task."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output/answers.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")


def same(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) is bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return str(a).strip().lower() == str(b).strip().lower()


def score(output_path: Path, gold: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {"final": {}, "probe": {}, "stale_fields": []}
    try:
        obj = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "schema", "points": 0, "possible": 1,
                       "note": "valid answers JSON", "error": f"{type(exc).__name__}: {exc}"})
        return finish(checks, details)

    final = obj.get("final") if isinstance(obj.get("final"), dict) else {}
    probe = obj.get("probe") if isinstance(obj.get("probe"), dict) else {}
    if not final or not probe:
        checks.append({"name": "schema", "points": 0, "possible": 1, "note": "final and probe objects"})
        return finish(checks, details)
    checks.append({"name": "schema", "points": 1, "possible": 1, "note": "final and probe objects"})

    fields = list(gold["final"])
    final_ok = 0
    for key in fields:
        ok = same(final.get(key), gold["final"][key])
        final_ok += int(ok)
        details["final"][key] = {"model": final.get(key), "answer": gold["final"][key], "ok": ok}
    checks.append({"name": "final_config", "points": 70 * final_ok / len(fields), "possible": 70,
                   "note": "11 fields in the final artifact"})

    probe_ok = 0
    for key in fields:
        ok = same(probe.get(key), gold["probe"][key])
        probe_ok += int(ok)
        details["probe"][key] = {"model": probe.get(key), "answer": gold["probe"][key], "ok": ok}
    checks.append({"name": "probe_config", "points": 10 * probe_ok / len(fields), "possible": 10,
                   "note": "11 fields at turn 10"})

    stale = []
    for key in fields:
        if not same(gold["final"][key], gold["probe"][key]) and same(final.get(key), gold["probe"][key]):
            stale.append(key)
    details["stale_fields"] = stale
    details["dissociation"] = probe_ok == len(fields) and bool(stale)
    checks.append({"name": "update_application", "points": max(0.0, 20.0 - 2.5 * len(stale)), "possible": 20,
                   "note": "2.5-point penalty per field that kept the turn-10 value", "stale": stale})
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
                      "dissociation": result["details"].get("dissociation"),
                      "stale_fields": result["details"].get("stale_fields"),
                      "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
