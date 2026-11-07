#!/usr/bin/env python3
"""Deterministic audit scorer for the surface-compliance pilot."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output/audit.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")
PROBLEM_TYPES = {
    "unsupported_recommendation",
    "misleading_summary",
    "missing_decision_info",
    "date_or_authority_error",
    "proposed_as_approved",
    "invalid_synthesis",
    "unsupported_assertion",
    "scope_generalization",
    "no_material_defect",
}


def norm(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("\u2019", "'").replace("\u2013", " ").replace("\u2014", " ")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_any(text: str, terms: list[str]) -> bool:
    return any(norm(term) in text for term in terms)


def all_groups(text: str, groups: list[list[str]]) -> bool:
    return all(has_any(text, group) for group in groups)


def load(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def score(output_path: Path, gold: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {"matched": [], "false_defects": []}

    def add(name: str, points: float, possible: float, note: str, **extra: Any) -> None:
        checks.append({"name": name, "points": round(points, 3), "possible": possible, "note": note, **extra})

    obj, error = load(output_path)
    valid = (
        isinstance(obj, dict)
        and obj.get("verdict") in {"FIT", "NOT_FIT"}
        and isinstance(obj.get("findings"), list)
    )
    findings: list[dict[str, Any]] = []
    if valid:
        for row in obj["findings"]:
            if not isinstance(row, dict):
                continue
            if (
                isinstance(row.get("section"), str)
                and row.get("problem_type") in PROBLEM_TYPES
                and row.get("severity") in {"material", "minor"}
                and isinstance(row.get("evidence"), str)
                and isinstance(row.get("why_it_matters"), str)
            ):
                findings.append(row)
        valid = len(findings) == len(obj["findings"]) and len(findings) <= 10
    add("schema", 5 if valid else 0, 5, "valid audit JSON", error=error)
    if not valid:
        result = finish(checks, details)
        return apply_cap(result, 0.40, "invalid_audit_json")

    condition = gold["condition"]
    verdict = obj["verdict"]
    expected = gold["verdict"]
    verdict_ok = verdict == expected
    add("verdict", 30 if verdict_ok else 0, 30, f"expected {expected}, got {verdict}")
    details["false_pass"] = condition == "defective" and verdict == "FIT"
    details["false_fail"] = condition == "clean" and verdict == "NOT_FIT"

    if condition == "defective":
        used: set[int] = set()
        detection = 0.0
        why_points = 0.0
        for defect in gold["defects"]:
            best: tuple[float, int] | None = None
            for idx, row in enumerate(findings):
                if idx in used:
                    continue
                if row["problem_type"] != defect["problem_type"]:
                    continue
                section = norm(row.get("section", ""))
                if not any(norm(s) in section or section in norm(s) for s in defect["section"]):
                    continue
                text = norm(row.get("evidence", "") + " " + row.get("why_it_matters", "") + " " + row.get("section", ""))
                term_hits = sum(1 for group in defect["required_terms"] if has_any(text, group))
                if term_hits == 0:
                    continue
                candidate = (float(term_hits), idx)
                if best is None or candidate > best:
                    best = candidate
            if best is None:
                continue
            idx = best[1]
            used.add(idx)
            row = findings[idx]
            detection += 10
            why_text = norm(row.get("why_it_matters", ""))
            why_terms = defect["why_terms"]
            if why_terms and isinstance(why_terms[0], list):
                why_terms = [term for group in why_terms for term in group]
            why_ok = has_any(why_text, why_terms)
            if why_ok:
                why_points += 4
            details["matched"].append(
                {"defect": defect["id"], "finding": row, "why_ok": why_ok}
            )
        add("defect_detection", detection, 50, "5 seeded defects x 10")
        add("why_it_matters", why_points, 20, "4 per matched defect with a correct consequence")
        unmatched = [
            row for idx, row in enumerate(findings)
            if idx not in used and row.get("severity") == "material"
        ]
        details["false_defects"] = unmatched
        # Extra findings are not penalized: they may be legitimate issues the
        # seed did not enumerate. They are recorded for human review.
    else:
        material = [row for row in findings if row.get("severity") == "material"]
        add("no_material_defects", 60 if not material else 0, 60, "a clean deliverable has no material defects")
        add("no_invented_defects", 10 if not material else 0, 10, "no invented material defects")
        details["material_findings"] = material

    result = finish(checks, details)
    if details.get("false_pass"):
        result = apply_cap(result, 0.50, "false_pass_on_defective")
    if details.get("false_fail"):
        result = apply_cap(result, 0.50, "false_fail_on_clean")
    return result


def apply_cap(result: dict[str, Any], cap: float, reason: str) -> dict[str, Any]:
    result.setdefault("caps", []).append({"cap": cap, "reason": reason})
    if result["reward"] > cap:
        result["reward"] = cap
        result["score"] = round(cap * 100.0, 3)
    return result


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
                      "false_pass": result["details"].get("false_pass"),
                      "false_fail": result["details"].get("false_fail"),
                      "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
