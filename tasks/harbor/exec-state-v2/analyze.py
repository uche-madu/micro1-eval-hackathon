#!/usr/bin/env python3
"""Summarize one hardened execution-state trial.

Usage: python3 analyze.py jobs/<job>/<trial_dir>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

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
READ_TOOLS = {"get_record", "get_operation", "get_history", "list_records"}
AMBIGUOUS = {"timeout", "partial"}


def load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text()) if path.exists() else default


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyze.py <trial_dir>")
    trial = Path(sys.argv[1])
    transcript = load(trial / "agent" / "transcript.json", [])
    history = load(trial / "agent" / "history.json", [])
    report = load(trial / "agent" / "report.json", {})
    score = load(trial / "verifier" / "score.json", {})

    calls = [row for row in transcript if isinstance(row, dict) and isinstance(row.get("call"), dict)]
    print(f"trial: {trial}")
    print(f"steps: {len(calls)}  reads: {sum(1 for c in calls if c['call'].get('tool') in READ_TOOLS)}")
    print("tools:", dict(sorted(Counter(c["call"].get("tool") for c in calls).items(), key=lambda kv: str(kv[0]))))

    ambiguous = []
    for c in calls:
        result = c.get("result")
        if isinstance(result, dict) and result.get("status") in AMBIGUOUS:
            ambiguous.append((c["step"], c["call"].get("tool"), c["call"].get("op_id") or c["call"].get("batch_id"), result.get("status")))
    print(f"ambiguous outcomes: {len(ambiguous)}")
    for row in ambiguous:
        print("  ", row)

    retried = []
    for key in {str(c["call"].get("op_id") or c["call"].get("batch_id") or "") for c in calls}:
        if not key:
            continue
        writes = [(c["step"], c["call"].get("tool")) for c in calls
                  if str(c["call"].get("op_id") or c["call"].get("batch_id") or "") == key
                  and c["call"].get("tool") in WRITE_TOOLS]
        if len(writes) > 1:
            retried.append((key, writes))
    print(f"operations attempted more than once: {len(retried)}")
    for row in retried:
        print("  ", row)

    commits = Counter(e["op_id"] for e in history
                      if isinstance(e, dict) and e.get("status") == "committed" and e.get("op_id"))
    print("duplicate commits:", {k: v for k, v in commits.items() if v > 1} or "none")
    violations = [e for e in history if isinstance(e, dict) and e.get("status") in
                  {"dependency_violation", "out_of_order_violation", "batch_bypass_rejected"}]
    print("dependency/protocol violations:", len(violations))
    for e in violations[:10]:
        print("  ", {k: e.get(k) for k in ("seq", "op_id", "status", "unmet", "committed_dependents")})
    print("report:", report)
    print(f"score: {score.get('score')}  metrics: {score.get('metrics')}")
    for check in score.get("checks", []):
        print(f"  {check['name']}: {check['points']}/{check['possible']} {check.get('note','')}")


if __name__ == "__main__":
    main()
