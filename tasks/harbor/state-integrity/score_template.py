#!/usr/bin/env python3
"""Deterministic scorer for the 10-turn state-integrity tasks."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output/answers.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")


def norm(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("\u2019", "'").replace("\u2013", " ").replace("\u2014", " ")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def matches(value: Any, accepted: list[str]) -> bool:
    text = norm(value)
    return any(norm(item) in text for item in accepted)


def is_stale(value: Any, stale: list[str]) -> bool:
    text = norm(value)
    return any(text == norm(item) or text.startswith(norm(item) + " ") for item in stale)


def score(output_path: Path, gold: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {"final": {}, "recall": {}, "stale_fields": []}

    def add(name: str, points: float, possible: float, note: str, **extra: Any) -> None:
        checks.append({"name": name, "points": round(points, 3), "possible": possible, "note": note, **extra})

    try:
        obj = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        add("schema", 0, 5, "valid answers JSON", error=f"{type(exc).__name__}: {exc}")
        return finish(checks, details)

    valid = (
        isinstance(obj, dict)
        and isinstance(obj.get("final"), dict)
        and isinstance(obj.get("recall"), dict)
    )
    add("schema", 5 if valid else 0, 5, "final and recall objects")
    if not valid:
        return finish(checks, details)

    final_correct = 0
    for q, spec in gold["final"].items():
        ok = matches(obj["final"].get(q), spec["accept"])
        final_correct += int(ok)
        details["final"][q] = {"model": obj["final"].get(q), "answer": spec["answer"], "ok": ok}
    add("final_answers", 10 * final_correct, 60, "6 final questions x 10")

    recall_correct = 0
    for key, spec in gold["recall"].items():
        ok = matches(obj["recall"].get(key), spec["accept"])
        recall_correct += int(ok)
        details["recall"][key] = {"model": obj["recall"].get(key), "answer": spec["answer"], "ok": ok}
    add("recall_probe", 5 * recall_correct, 20, "4 recall fields x 5")

    stale = []
    for q, values in gold["stale_values"].items():
        if is_stale(obj["final"].get(q), values):
            stale.append(q)
    details["stale_fields"] = stale
    details["dissociation"] = recall_correct == len(gold["recall"]) and bool(stale)
    update_points = max(0.0, 20.0 - 5.0 * len(stale))
    add("update_application", update_points, 20, "5-point penalty per final answer using a superseded state",
        stale=stale)

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
