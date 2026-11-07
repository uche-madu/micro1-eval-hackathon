#!/usr/bin/env python3
"""Deterministic scorer for the board-brief Harbor task.

Writes /logs/verifier/reward.txt (float 0-1) and score.json.
No LLM judge.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_BRIEF = Path("/output/brief.md")
DEFAULT_FINDINGS = Path("/output/findings.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_SOURCES = HERE / "sources.json"
DEFAULT_OUT = Path("/logs/verifier")

NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
HEAD_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
FID_RE = re.compile(r"\bF(\d{1,2})\b")
SID_RE = re.compile(r"\b([DI]\d{1,2})\b")


def norm(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u2013", " ")
        .replace("\u2014", " ")
        .replace("\u2212", " ")
    )
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_any(text: str, terms: list[str]) -> bool:
    return any(norm(term) in text for term in terms)


def all_groups(text: str, groups: list[list[str]]) -> bool:
    return all(has_any(text, group) for group in groups)


def numbers_in(text: str) -> set[str]:
    return {match.rstrip(".").replace(",", "") for match in NUM_RE.findall(text)}


def contains_claim(text: str, phrase: str) -> bool:
    """True only for an asserted phrase, not a negated or rejected one."""
    needle = norm(phrase)
    hay = norm(text)
    start = 0
    while True:
        idx = hay.find(needle, start)
        if idx < 0:
            return False
        window = hay[max(0, idx - 60) : idx + len(needle) + 60]
        negation = re.search(
            r"\b(not|no|never|cannot|rather than|instead of|does not|did not|unsupported|rejected|incorrect|false)\b",
            window,
        )
        if not negation:
            return True
        start = idx + len(needle)


def load_json(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 - output boundary
        return None, f"{type(exc).__name__}: {exc}"


def score(brief_path: Path, findings_path: Path, gold: dict[str, Any], sources: dict[str, str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {"findings": {}, "forbidden_hits": [], "unknown_numbers": []}

    def add(name: str, points: float, possible: float, note: str, **extra: Any) -> None:
        checks.append(
            {"name": name, "points": round(points, 3), "possible": possible, "note": note, **extra}
        )

    brief = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    outputs_ok = bool(brief.strip()) and findings_path.exists()
    add("outputs_exist", 3 if outputs_ok else 0, 3, "both output files exist and are non-empty")
    if not outputs_ok:
        return finish(checks, details)

    obj, error = load_json(findings_path)
    rows: list[dict[str, Any]] = []
    schema_ok = False
    if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
        rows = [row for row in obj["findings"] if isinstance(row, dict)]
        required_fields = ("finding_id", "statement", "evidence_ids", "qualifier")
        schema_ok = len(rows) == len(obj["findings"]) and all(
            all(field in row for field in required_fields)
            and isinstance(row.get("evidence_ids"), list)
            and isinstance(row.get("statement"), str)
            and isinstance(row.get("qualifier"), str)
            for row in rows
        )
    add("json_schema", 3 if schema_ok else 0, 3, "findings object with the required fields", error=error)

    ids = [str(row.get("finding_id", "")) for row in rows]
    expected_ids = [f"F{i}" for i in range(1, gold["finding_count"] + 1)]
    count_ok = len(rows) == gold["finding_count"]
    ids_ok = sorted(ids) == sorted(expected_ids) and len(set(ids)) == len(ids)
    add("finding_count", 3 if count_ok else 0, 3, f"exactly {gold['finding_count']} findings")
    add("finding_ids", 3 if ids_ok else 0, 3, "F1 through F13 exactly once")

    words = len(WORD_RE.findall(brief))
    low, high = gold["word_count"]
    word_ok = low <= words <= high
    add("word_count", 5 if word_ok else 0, 5, f"{words} words; required {low}-{high}")

    headings = HEAD_RE.findall(brief)
    heading_norm = [norm(h) for h in headings]
    section_hits = 0
    for group in gold["sections"]:
        if any(any(norm(term) in heading for term in group) for heading in heading_norm):
            section_hits += 1
    exact_sections = len(headings) == len(gold["sections"])
    section_points = 8 * section_hits / len(gold["sections"]) + (2 if exact_sections else 0)
    add(
        "sections",
        section_points,
        10,
        f"{section_hits}/{len(gold['sections'])} required headings; {len(headings)} level-2 headings",
    )

    prose_ids = {f"F{match}" for match in FID_RE.findall(brief)}
    missing_ids = [fid for fid in expected_ids if fid not in prose_ids]
    add("prose_finding_ids", 5 * (len(expected_ids) - len(missing_ids)) / len(expected_ids), 5,
        "every finding ID appears in the prose", missing=missing_ids)

    prose_sources = set(SID_RE.findall(brief))
    by_id = {str(row.get("finding_id", "")): row for row in rows}
    citation_missing: list[str] = []
    for fid, gold_finding in gold["findings"].items():
        row = by_id.get(fid, {})
        accepted = gold_finding["evidence_any"]
        model_ids = {str(x) for x in row.get("evidence_ids", [])}
        cited = any(set(one) <= prose_sources for one in accepted) or bool(
            model_ids & prose_sources
        )
        if not cited:
            citation_missing.append(fid)
    add("citations", 5 * (len(expected_ids) - len(citation_missing)) / len(expected_ids), 5,
        "each finding's evidence appears in the prose", missing=citation_missing)

    finding_points = 0.0
    for fid, gold_finding in gold["findings"].items():
        row = by_id.get(fid, {})
        text = norm(str(row.get("statement", "")) + " " + str(row.get("qualifier", "")))
        qual_text = norm(str(row.get("qualifier", "")))
        facts_ok = all_groups(text, gold_finding["required_groups"])
        evidence_ok = any(
            set(one) <= {str(x) for x in row.get("evidence_ids", [])}
            for one in gold_finding["evidence_any"]
        )
        qualifier_ok = all_groups(qual_text, gold_finding["qualifier_groups"])
        points = (2 if facts_ok else 0) + (1 if evidence_ok else 0) + (1 if qualifier_ok else 0)
        finding_points += points
        details["findings"][fid] = {
            "points": points,
            "facts_ok": facts_ok,
            "evidence_ok": evidence_ok,
            "qualifier_ok": qualifier_ok,
            "statement": row.get("statement", ""),
            "qualifier": row.get("qualifier", ""),
        }
    add("findings", finding_points, 52, "13 findings x (facts 2, evidence 1, qualifier 1)")

    hits = [phrase for phrase in gold["forbidden_phrases"] if contains_claim(brief, phrase)]
    details["forbidden_hits"] = hits
    add("no_forbidden_overclaims", 8 * (1 - len(hits) / len(gold["forbidden_phrases"])), 8,
        "no prohibited overclaim", hits=hits)

    allowed = set(gold.get("allowed_numbers_extra", []))
    for text in sources.values():
        allowed |= numbers_in(text)
    unknown = sorted(numbers_in(brief) - allowed)
    details["unknown_numbers"] = unknown
    add("no_invented_numbers", 5 if not unknown else 0, 5,
        "every number in the brief appears in the source pack", unknown=unknown)

    banned = re.findall(r"\b(eval|evaluation|grader|gold|reference solution|test case|harbor)\b", brief, re.I)
    add("no_eval_leakage", 3 if not banned else 0, 3, "no evaluation/grader language", hits=banned)

    consistency_ok = schema_ok and len(set(ids)) == len(ids) and not hits
    add("consistency", 5 if consistency_ok else 0, 5,
        "no duplicate finding IDs and no contradictory overclaim")

    result = finish(checks, details, words=words, headings=len(headings))
    if hits:
        result = apply_cap(result, 0.60, "prohibited_overclaim")
    if not schema_ok:
        result = apply_cap(result, 0.50, "invalid_findings_schema")
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
    score_value = round(100.0 * points / possible, 3) if possible else 0.0
    reward = round(points / possible, 6) if possible else 0.0
    return {
        "score": score_value,
        "reward": reward,
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
        "details": details,
        **extra,
    }


def write_result(result: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "score.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out_dir / "reward.txt").write_text(f"{result['reward']:.6f}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", type=Path, default=DEFAULT_BRIEF)
    parser.add_argument("--findings", type=Path, default=DEFAULT_FINDINGS)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    sources = json.loads(args.sources.read_text(encoding="utf-8"))

    if args.selftest:
        fixture_dir = HERE / "fixtures"
        reference = score(fixture_dir / "reference" / "brief.md",
                          fixture_dir / "reference" / "findings.json", gold, sources)
        bad = score(fixture_dir / "bad_overclaim" / "brief.md",
                    fixture_dir / "bad_overclaim" / "findings.json", gold, sources)
        malformed = score(fixture_dir / "bad_malformed" / "brief.md",
                          fixture_dir / "bad_malformed" / "findings.json", gold, sources)
        print(json.dumps({
            "reference": reference["score"],
            "bad_overclaim": bad["score"],
            "bad_malformed": malformed["score"],
        }, indent=2))
        if reference["reward"] < 1.0:
            print("SELFTEST FAIL: reference did not score 1.0", file=sys.stderr)
            raise SystemExit(1)
        if bad["reward"] >= 0.8 or malformed["reward"] > 0.5:
            print("SELFTEST FAIL: bad output was not rejected", file=sys.stderr)
            raise SystemExit(1)
        print("SELFTEST OK")
        return

    result = score(args.brief, args.findings, gold, sources)
    write_result(result, args.out_dir)
    print(json.dumps({"score": result["score"], "reward": result["reward"],
                      "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
