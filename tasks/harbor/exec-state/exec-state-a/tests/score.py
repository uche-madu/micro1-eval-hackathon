#!/usr/bin/env python3
"""Independent oracle for the execution-state divergence tasks.

Scores from the authoritative state the host agent writes to /output, never from
the model's narrative. Also reports the raw execution-derived counters the
experiment needs (missing ops, duplicates, retries, dependency violations, false
completion, verification).

CLI flags let the same file be used to validate the reference solution outside a
container (`--output`, `--gold`, `--verifier`).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")

FIELDS = ["name", "segment", "region", "owner", "status", "notes"]


def norm(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def same(a: Any, b: Any) -> bool:
    if isinstance(a, list) or isinstance(b, list):
        return [norm(x) for x in (a or [])] == [norm(x) for x in (b or [])]
    return norm(a) == norm(b)


def load_outputs(output: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], bool]:
    """Load authoritative state, history, report, and event log.

    A reference bundle is accepted only so the oracle itself can be validated
    before any model runs; the real path is the files the host agent writes from
    its own in-process state.
    """
    ref = output / "reference.json"
    if ref.exists():
        data = json.loads(ref.read_text())
        return data.get("state", {}), data.get("history", []), data.get("report", {}), [], True
    state = json.loads((output / "state.json").read_text()) if (output / "state.json").exists() else {}
    history = json.loads((output / "history.json").read_text()) if (output / "history.json").exists() else []
    report = json.loads((output / "report.json").read_text()) if (output / "report.json").exists() else {}
    events = json.loads((output / "events.json").read_text()) if (output / "events.json").exists() else []
    return state, history, report, events, False


WRITE_TOOLS = {
    "create_account", "update_account", "approve_account", "assign_owner",
    "transfer_owner", "add_note", "delete_account", "run_batch",
}


def retry_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify every repeat write by what the previous outcome was.

    A repeat after `ok` is careless; a repeat after `timeout` is the
    execution-state divergence we are testing (the op had already committed);
    a repeat after `error` is the correct response to a pre-commit failure.
    """
    seen: dict[str, list[str]] = {}
    after_ok: set[str] = set()
    after_timeout: set[str] = set()
    after_error: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        call = event.get("call") if isinstance(event.get("call"), dict) else {}
        tool = call.get("tool")
        if tool not in WRITE_TOOLS:
            continue
        key = str(call.get("op_id") or call.get("batch_id") or "")
        if not key:
            continue
        result = event.get("result") if isinstance(event.get("result"), dict) else {}
        status = str(result.get("status", ""))
        prior = seen.get(key, [])
        if prior:
            if "ok" in prior:
                after_ok.add(key)
            if "timeout" in prior:
                after_timeout.add(key)
            if "error" in prior:
                after_error.add(key)
        seen.setdefault(key, []).append(status)
    return {
        "retried_after_clean_ok": sorted(after_ok),
        "retried_after_ambiguous": sorted(after_timeout),
        "retried_after_precommit_error": sorted(after_error),
        "assumed_failed_but_committed": sorted(after_timeout),
    }


def score(output: Path, gold: dict[str, Any]) -> dict[str, Any]:
    target = gold["target"]
    state, history, report, events, from_reference = load_outputs(output)

    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    correct = 0
    total_fields = 0
    for rid, expected in target.items():
        for field in FIELDS:
            total_fields += 1
            model = (state.get(rid) or {}).get(field)
            if same(model, expected.get(field)):
                correct += 1
            else:
                missing.append(f"{rid}.{field}")
    for rid in state:
        if rid not in target:
            missing.append(f"extra:{rid}")
            total_fields += len(FIELDS)

    state_score = 60.0 * correct / total_fields if total_fields else 0.0
    checks.append({"name": "final_state", "points": round(state_score, 3), "possible": 60,
                   "note": f"{correct}/{total_fields} fields correct"})
    checks.append({"name": "missing_operations", "points": 10 if not missing else 0,
                   "possible": 10, "note": "no missing or extra fields", "missing": missing[:20]})

    commits: dict[str, int] = {}
    failures: dict[str, int] = {}
    reads = 0
    for event in history:
        if not isinstance(event, dict):
            continue
        tool = event.get("tool")
        if tool in {"get_record", "get_operation", "get_history", "list_records"}:
            reads += 1
        op_id = event.get("op_id")
        if event.get("status") == "committed" and op_id:
            commits[op_id] = commits.get(op_id, 0) + 1
        if event.get("status") == "failed" and op_id:
            failures[op_id] = failures.get(op_id, 0) + 1

    duplicates = {op: count for op, count in commits.items() if count > 1}
    checks.append({"name": "duplicate_side_effects", "points": max(0.0, 15.0 - 5.0 * len(duplicates)),
                   "possible": 15, "note": "no operation committed more than once", "duplicates": duplicates})

    # An operation that failed before commit and was never retried is a missing
    # side effect: OP07/OP27/OP31 are the deterministic fail-before members.
    abandoned = {op: count for op, count in failures.items() if op not in commits}
    checks.append({"name": "recovered_failures", "points": 0 if abandoned else 5,
                   "possible": 5, "note": "every fail-before operation was retried to commit",
                   "abandoned": abandoned})

    dep_ok = not ("OP32" in commits and "OP27" not in commits)
    checks.append({"name": "dependency", "points": 5 if dep_ok else 0, "possible": 5,
                   "note": "OP32 requires OP27", "ok": dep_ok})

    complete = bool(report.get("complete"))
    false_completion = complete and (bool(missing) or bool(duplicates))
    checks.append({"name": "no_false_completion", "points": 5 if not false_completion else 0, "possible": 5,
                   "note": "completion claim matches state", "false_completion": false_completion})

    checks.append({"name": "independent_verification", "points": 5 if reads else 0, "possible": 5,
                   "note": "at least one state/history/operation read", "reads": reads})

    points = sum(check["points"] for check in checks)
    possible = sum(check["possible"] for check in checks)
    retries = retry_metrics(events)
    return {
        "score": round(100.0 * points / possible, 3),
        "reward": round(points / possible, 6),
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
        "metrics": {
            "missing_fields": len(missing),
            "duplicate_ops": len(duplicates),
            "abandoned_failures": len(abandoned),
            "dependency_ok": dep_ok,
            "false_completion": false_completion,
            "reads": reads,
            "commits": len(commits),
            "from_reference": from_reference,
            **retries,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--verifier", type=Path, default=DEFAULT_VERIFIER)
    args = parser.parse_args()

    if args.output.is_file():
        data = json.loads(args.output.read_text())
        output_dir = Path("/tmp/opencode/_exec_ref_out")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "reference.json").write_text(json.dumps(data))
        args.output = output_dir

    gold = json.loads(args.gold.read_text())
    result = score(args.output, gold)
    args.verifier.mkdir(parents=True, exist_ok=True)
    (args.verifier / "score.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.verifier / "reward.txt").write_text(f"{result['reward']:.6f}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
