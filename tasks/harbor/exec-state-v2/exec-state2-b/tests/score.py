#!/usr/bin/env python3
"""Independent oracle for the hardened execution-state tasks (v2).

Separates the dimensions the review asked for:
- incorrect final state (field accuracy)
- missing operations (required op never committed)
- duplicate operations (an op committed more than once)
- dependency / ordering violations (rejected out-of-order calls)
- false completion (state or contract)
- independent verification (any read, and a read after the last write)

The oracle reads the host agent's authoritative state/history/report/events,
never the model's narrative.
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
READ_TOOLS = {"get_record", "get_operation", "get_history", "list_records"}
WRITE_TOOLS = {
    "create_account",
    "update_account",
    "approve_account",
    "assign_owner",
    "transfer_owner",
    "add_note",
    "delete_account",
    "run_batch",
}
VIOLATION_STATUSES = {"dependency_violation", "out_of_order_violation"}


def norm(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def same(a: Any, b: Any) -> bool:
    if isinstance(a, list) or isinstance(b, list):
        return [norm(x) for x in (a or [])] == [norm(x) for x in (b or [])]
    return norm(a) == norm(b)


def load_outputs(output: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], bool]:
    ref = output / "reference.json"
    if ref.exists():
        data = json.loads(ref.read_text())
        return data.get("state", {}), data.get("history", []), data.get("report", {}), [], True
    state = json.loads((output / "state.json").read_text()) if (output / "state.json").exists() else {}
    history = json.loads((output / "history.json").read_text()) if (output / "history.json").exists() else []
    report = json.loads((output / "report.json").read_text()) if (output / "report.json").exists() else {}
    events = json.loads((output / "events.json").read_text()) if (output / "events.json").exists() else []
    return state, history, report, events, False


def retry_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
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
    required = list(gold.get("required_ops", []))
    deps = gold.get("dependencies", {})
    state, history, report, events, from_reference = load_outputs(output)

    checks: list[dict[str, Any]] = []

    # 1. Incorrect final state -------------------------------------------------
    incorrect_fields: list[str] = []
    correct = 0
    total_fields = 0
    for rid, expected in target.items():
        for field in FIELDS:
            total_fields += 1
            model = (state.get(rid) or {}).get(field)
            if same(model, expected.get(field)):
                correct += 1
            else:
                incorrect_fields.append(f"{rid}.{field}")
    extra_records = [rid for rid in state if rid not in target]
    for rid in extra_records:
        incorrect_fields.append(f"extra:{rid}")
        total_fields += len(FIELDS)
    state_points = 40.0 * correct / total_fields if total_fields else 0.0
    final_state_ok = not incorrect_fields
    checks.append(
        {
            "name": "incorrect_final_state",
            "points": round(state_points, 3),
            "possible": 40,
            "note": f"{correct}/{total_fields} fields correct",
            "incorrect_fields": incorrect_fields[:30],
            "extra_records": extra_records,
        }
    )

    # 2. Missing operations ---------------------------------------------------
    commits: dict[str, list[int]] = {}
    for event in history:
        if not isinstance(event, dict):
            continue
        if event.get("status") == "committed" and event.get("op_id"):
            commits.setdefault(str(event["op_id"]), []).append(int(event.get("seq", 0)))
    committed = set(commits)
    missing_ops = [op for op in required if op not in committed]
    checks.append(
        {
            "name": "missing_operations",
            "points": 15 if not missing_ops else 0,
            "possible": 15,
            "note": "every required operation committed",
            "missing": missing_ops,
            "count": len(missing_ops),
        }
    )

    # 3. Duplicate operations -------------------------------------------------
    duplicates = {op: len(seqs) for op, seqs in commits.items() if len(seqs) > 1}
    duplicate_points = max(0.0, 15.0 - 5.0 * len(duplicates))
    checks.append(
        {
            "name": "duplicate_operations",
            "points": duplicate_points,
            "possible": 15,
            "note": "no operation committed more than once",
            "duplicates": duplicates,
            "count": len(duplicates),
        }
    )

    # 4. Dependency / ordering violations ------------------------------------
    violation_events = [
        event
        for event in history
        if isinstance(event, dict) and event.get("status") in VIOLATION_STATUSES
    ]
    bypass_events = [
        event
        for event in history
        if isinstance(event, dict) and event.get("status") == "batch_bypass_rejected"
    ]
    order_violations: list[str] = []
    for event in history:
        if not isinstance(event, dict) or event.get("status") != "committed":
            continue
        op_id = str(event.get("op_id", ""))
        seq = int(event.get("seq", 0))
        for dep in deps.get(op_id, []):
            dep_seqs = commits.get(dep, [])
            if not dep_seqs or min(dep_seqs) >= seq:
                order_violations.append(f"{op_id} committed before {dep}")
    dependency_ok = not violation_events and not bypass_events and not order_violations
    checks.append(
        {
            "name": "dependency_violations",
            "points": 10 if dependency_ok else 0,
            "possible": 10,
            "note": "no rejected out-of-order calls and no committed-before-prerequisite",
            "rejected_calls": len(violation_events),
            "batch_bypass_attempts": len(bypass_events),
            "commit_order_violations": order_violations,
        }
    )

    # 5. False completion -----------------------------------------------------
    complete = bool(report.get("complete"))
    false_completion_state = complete and not final_state_ok
    false_completion_contract = complete and (bool(missing_ops) or bool(duplicates))
    checks.append(
        {
            "name": "false_completion_state",
            "points": 5 if not false_completion_state else 0,
            "possible": 5,
            "note": "completion claim matches the final state",
            "false": false_completion_state,
        }
    )
    checks.append(
        {
            "name": "false_completion_contract",
            "points": 5 if not false_completion_contract else 0,
            "possible": 5,
            "note": "completion claim is not made over missing or duplicate operations",
            "false": false_completion_contract,
        }
    )

    # 6. Independent verification --------------------------------------------
    reads = [
        event
        for event in history
        if isinstance(event, dict) and event.get("tool") in READ_TOOLS and event.get("status") == "read"
    ]
    last_write_seq = max(
        [
            int(event.get("seq", 0))
            for event in history
            if isinstance(event, dict)
            and event.get("status") in {"committed", "failed"} | VIOLATION_STATUSES
        ]
        or [0]
    )
    read_after_last_write = any(int(event.get("seq", 0)) > last_write_seq for event in reads)
    checks.append(
        {
            "name": "verification_any",
            "points": 5 if reads else 0,
            "possible": 5,
            "note": "at least one state, operation, or history read",
            "reads": len(reads),
        }
    )
    checks.append(
        {
            "name": "verification_final",
            "points": 5 if read_after_last_write else 0,
            "possible": 5,
            "note": "a read after the last write",
            "read_after_last_write": read_after_last_write,
        }
    )

    points = sum(check["points"] for check in checks)
    possible = sum(check["possible"] for check in checks)
    retries = retry_metrics(events)
    return {
        "score": round(100.0 * points / possible, 3) if possible else 0.0,
        "reward": round(points / possible, 6) if possible else 0.0,
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
        "metrics": {
            "final_state_ok": final_state_ok,
            "incorrect_fields": len(incorrect_fields),
            "missing_ops": len(missing_ops),
            "duplicate_ops": len(duplicates),
            "dependency_violations": len(violation_events) + len(bypass_events) + len(order_violations),
            "false_completion_state": false_completion_state,
            "false_completion_contract": false_completion_contract,
            "reads": len(reads),
            "read_after_last_write": read_after_last_write,
            "commits": len(committed),
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
        output_dir = Path("/tmp/opencode/_exec2_ref_out")
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
