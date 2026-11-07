"""Deterministic grader for the D1-S pilot.

No LLM judge. Structured JSON in, per-item and per-task scores out.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

NUM_RE = re.compile(r"(?<=\d),(?=\d)")
SPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[.,;:!?\"'`()\[\]{}]")
ID_RE = re.compile(r"\b[A-Z]\d{1,3}\b")

VERDICTS = {"SUPPORTED", "SUPPORTED_WITH_QUALIFIER", "CONTRADICTED", "INSUFFICIENT"}
OVERREACH_TAGS = {
    "temporal_overreach",
    "scope_generalization",
    "unsupported_synthesis",
    "draft_as_fact",
    "qualifier_dropped",
    "unsupported_assertion",
    "authority_inversion",
}


def norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = NUM_RE.sub("", text)
    text = PUNCT_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def extract_ids(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        out: set[str] = set()
        for item in value:
            out |= extract_ids(item)
        return out
    return {m.group(0) for m in ID_RE.finditer(str(value).upper())}


def parse_json(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse a model response. Returns (obj, error)."""
    if not raw or not raw.strip():
        return None, "empty_response"
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Prefer the outermost object, then the outermost array.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            candidate = text[start : end + 1]
            try:
                obj = json.loads(candidate, strict=False)
                if isinstance(obj, list):
                    obj = {"items": obj} if opener == "[" else obj
                if isinstance(obj, dict):
                    return obj, None
            except Exception:
                continue
    return None, "invalid_json"


def _evidence_score(model_ids: set[str], accepted_sets: list[list[str]]) -> tuple[float, str]:
    if not accepted_sets:
        return 1.0, "not_required"
    for accepted in accepted_sets:
        gold = set(accepted)
        if model_ids == gold:
            return 1.0, "exact"
        if gold <= model_ids:
            return 0.5, "superset"
    return 0.0, "wrong"


def _answer_matches(model_value: Any, gold_value: Any, accepted: list[Any]) -> tuple[bool, str]:
    model = norm(model_value)
    candidates = [norm(gold_value)] + [norm(item) for item in accepted]
    candidates = [item for item in dict.fromkeys(candidates) if item]
    if model in candidates:
        return True, "exact"
    for candidate in candidates:
        if len(candidate) >= 3 and re.search(
            r"(?<!\w)" + re.escape(candidate) + r"(?!\w)", model
        ):
            return True, "contained"
    return False, "none"


def _qualifier_score(model_qualifier: Any, terms: list[str]) -> tuple[float, bool]:
    if not terms:
        return 1.0, True
    text = norm(model_qualifier)
    ok = all(norm(term) in text for term in terms)
    return (1.0 if ok else 0.0), ok


def _dedupe(values: list[str]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen


def _grade_rows(
    rows: list[dict[str, Any]],
    gold_rows: list[dict[str, Any]],
    *,
    answer_key: str,
    gold_answer_key: str,
) -> dict[str, Any]:
    gold_by_id = {row["id"]: row for row in gold_rows}
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    duplicates: list[str] = []
    extras: list[str] = []

    for row in rows:
        rid = str(row.get("claim_id") or row.get("item_id") or "").strip()
        if not rid:
            extras.append("<missing id>")
            continue
        if rid in seen:
            duplicates.append(rid)
            continue
        seen.add(rid)
        if rid not in gold_by_id:
            extras.append(rid)
            continue
        gold = gold_by_id[rid]
        gold_value = gold["gold"][gold_answer_key]
        model_value = row.get(answer_key)
        answer_ok, answer_match = _answer_matches(
            model_value, gold_value, gold["gold"].get("accepted_answers", [])
        )
        model_ids = extract_ids(row.get("evidence_ids"))
        evidence_score, evidence_kind = _evidence_score(model_ids, gold["gold"]["evidence_sets"])
        qualifier_score, qualifier_ok = _qualifier_score(
            row.get("qualifier"), gold["gold"]["qualifier_terms"]
        )
        score = 0.6 * float(answer_ok) + 0.3 * evidence_score + 0.1 * qualifier_score
        strict = answer_match == "exact" and evidence_kind == "exact" and qualifier_ok

        tags: list[str] = []
        if not answer_ok:
            tags.extend(gold["gold"].get("failure_tags", []))
        if not qualifier_ok:
            tags.append("qualifier_dropped")
        if evidence_kind == "wrong":
            tags.append("evidence_identification")
        if evidence_kind in {"exact", "superset"} and not answer_ok:
            tags.append("evidence_correct_conclusion_wrong")
        if answer_ok and not qualifier_ok:
            tags.append("qualifier_dropped")

        results.append(
            {
                "id": rid,
                "gold": gold_value,
                "model": model_value,
                "answer_ok": answer_ok,
                "answer_match": answer_match,
                "evidence_kind": evidence_kind,
                "evidence_ids": sorted(model_ids),
                "gold_evidence_sets": gold["gold"]["evidence_sets"],
                "qualifier_ok": qualifier_ok,
                "qualifier": row.get("qualifier"),
                "score": round(score, 4),
                "strict": strict,
                "tags": _dedupe(tags),
                "overreach": (not answer_ok)
                and bool(set(tags) & OVERREACH_TAGS),
            }
        )

    missing = [gid for gid in gold_by_id if gid not in seen]
    for gid in missing:
        gold = gold_by_id[gid]
        results.append(
            {
                "id": gid,
                "gold": gold["gold"][gold_answer_key],
                "model": None,
                "answer_ok": False,
                "answer_match": "none",
                "evidence_kind": "wrong",
                "evidence_ids": [],
                "gold_evidence_sets": gold["gold"]["evidence_sets"],
                "qualifier_ok": False,
                "qualifier": None,
                "score": 0.0,
                "strict": False,
                "tags": ["missing_claim"],
                "overreach": False,
            }
        )

    n = len(gold_by_id)
    mean_score = sum(r["score"] for r in results) / n if n else 0.0
    accuracy = sum(1 for r in results if r["answer_ok"]) / n if n else 0.0
    strict = sum(1 for r in results if r["strict"]) / n if n else 0.0
    extra_penalty = min(0.05 * len(extras), 0.20)
    return {
        "n": n,
        "mean_score": round(max(0.0, mean_score - extra_penalty), 4),
        "accuracy": round(accuracy, 4),
        "strict": round(strict, 4),
        "extra_penalty": round(extra_penalty, 4),
        "duplicates": duplicates,
        "extras": extras,
        "missing": missing,
        "rows": results,
    }


def grade_recognition(task: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    rows = obj.get("claims") or obj.get("items") or []
    if isinstance(rows, dict):
        rows = [rows]
    graded = _grade_rows(
        rows,
        task["recognition_claims"],
        answer_key="verdict",
        gold_answer_key="verdict",
    )
    graded["condition"] = "recognition"
    return graded


def grade_production(task: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    rows = obj.get("items") or obj.get("claims") or []
    if isinstance(rows, dict):
        rows = [rows]
    graded = _grade_rows(
        rows,
        task["production_items"],
        answer_key="answer",
        gold_answer_key="answer",
    )
    summary = obj.get("summary") or ""
    summary_norm = norm(summary)
    required = task["summary"]["required_terms"]
    forbidden = task["summary"]["forbidden_phrases"]
    required_ok = all(norm(term) in summary_norm for term in required)
    forbidden_hits = [p for p in forbidden if norm(p) in summary_norm]

    answers = {
        str(row.get("item_id") or "").strip(): norm(row.get("answer"))
        for row in rows
        if isinstance(row, dict)
    }
    inconsistencies: list[dict[str, str]] = []
    for rule in task.get("consistency_rules", []):
        when_ok = True
        for key, values in rule["when"].items():
            accepted = values if isinstance(values, list) else [values]
            if answers.get(key, "") not in {norm(v) for v in accepted}:
                when_ok = False
                break
        if not when_ok:
            continue
        for key, values in rule["forbid"].items():
            rejected = values if isinstance(values, list) else [values]
            if answers.get(key, "") in {norm(v) for v in rejected}:
                inconsistencies.append(
                    {"rule": rule["id"], "item": key, "answer": answers.get(key, "")}
                )
                break

    graded["summary"] = {
        "text": summary,
        "required_ok": required_ok,
        "forbidden_hits": forbidden_hits,
        "score": round(0.5 * float(required_ok) + 0.5 * float(not forbidden_hits), 4),
    }
    graded["inconsistencies"] = inconsistencies
    graded["inconsistency_count"] = len(inconsistencies)
    graded["condition"] = "production"
    return graded


def grade(task: dict[str, Any], condition: str, raw: str) -> dict[str, Any]:
    obj, error = parse_json(raw)
    if obj is None:
        return {
            "condition": condition,
            "parse_error": error,
            "n": len(task["recognition_claims"] if condition == "recognition" else task["production_items"]),
            "mean_score": 0.0,
            "accuracy": 0.0,
            "strict": 0.0,
            "rows": [],
            "summary": None,
            "extras": [],
            "missing": [],
            "duplicates": [],
        }
    if condition == "recognition":
        return grade_recognition(task, obj)
    return grade_production(task, obj)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate graded records by model and condition."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        key = (record["model"], record["condition"])
        grouped.setdefault(key, []).append(record["grade"])

    out: dict[str, Any] = {}
    for (model, condition), grades in sorted(grouped.items()):
        n_items = sum(g["n"] for g in grades)
        correct = sum(round(g["accuracy"] * g["n"]) for g in grades)
        strict = sum(round(g["strict"] * g["n"]) for g in grades)
        overreach = sum(
            1 for g in grades for r in g.get("rows", []) if r.get("overreach")
        )
        signature = sum(
            1
            for g in grades
            for r in g.get("rows", [])
            if "evidence_correct_conclusion_wrong" in r.get("tags", [])
        )
        tags: Counter[str] = Counter()
        for g in grades:
            for r in g.get("rows", []):
                for tag in r.get("tags", []):
                    tags[tag] += 1
        summary_scores = [g["summary"]["score"] for g in grades if g.get("summary")]
        inconsistencies = sum(g.get("inconsistency_count", 0) for g in grades)
        out.setdefault(model, {})[condition] = {
            "calls": len(grades),
            "items": n_items,
            "accuracy": round(correct / n_items, 4) if n_items else 0.0,
            "strict": round(strict / n_items, 4) if n_items else 0.0,
            "overreach": overreach,
            "signature": signature,
            "inconsistencies": inconsistencies,
            "tags": dict(tags),
            "summary_mean": round(sum(summary_scores) / len(summary_scores), 4)
            if summary_scores
            else None,
            "parse_errors": sum(1 for g in grades if g.get("parse_error")),
        }
    return out


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"{'model':34} {'condition':18} {'n':>4} {'acc':>7} {'strict':>7} {'over':>5} {'sig':>4} {'parse':>5} {'sum':>6}",
        "-" * 105,
    ]
    for model, conditions in summary.items():
        for condition, data in conditions.items():
            lines.append(
                f"{model:34} {condition:18} {data['items']:>4} {data['accuracy']:>7.3f} "
                f"{data['strict']:>7.3f} {data['overreach']:>5} {data['signature']:>4} "
                f"{data['parse_errors']:>5} {str(data['summary_mean']):>6}"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--condition", choices=["recognition", "production"], required=True)
    parser.add_argument("--raw", required=True)
    args = parser.parse_args()
    task = json.loads(Path(args.task).read_text())
    raw = Path(args.raw).read_text()
    print(json.dumps(grade(task, args.condition, raw), indent=2))
