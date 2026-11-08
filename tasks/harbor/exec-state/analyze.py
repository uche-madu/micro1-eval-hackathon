#!/usr/bin/env python3
"""Summarize one execution-state trial from a Harbor job directory.

Reads the agent transcript/state/history and the verifier score, then prints the
execution facts the report needs: which operations were attempted more than once,
whether a read preceded a retry after an ambiguous outcome, fault responses seen,
and the final completion claim.

Usage:
    python3 analyze.py jobs/<job>/<trial_dir>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

AMBIGUOUS = ("timeout", "partial")
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

    calls: list[dict[str, Any]] = [
        row for row in transcript if isinstance(row, dict) and isinstance(row.get("call"), dict)
    ]
    print(f"trial: {trial}")
    print(f"steps: {len(calls)}  reads: {sum(1 for c in calls if c['call'].get('tool') in READ_TOOLS)}")

    tool_counts = Counter(c["call"].get("tool") for c in calls)
    print("tools:", dict(sorted(tool_counts.items(), key=lambda kv: str(kv[0]))))

    ambiguous: list[dict[str, Any]] = []
    for c in calls:
        result = c.get("result")
        if isinstance(result, dict) and result.get("status") in AMBIGUOUS:
            ambiguous.append({"step": c["step"], "call": c["call"], "result": result})
    print(f"ambiguous outcomes: {len(ambiguous)}")
    for a in ambiguous:
        print(f"  step {a['step']}: {a['call'].get('tool')} {a['call'].get('op_id') or a['call'].get('batch_id')} -> {a['result'].get('status')}")

    # For each ambiguous op, did the agent read before its next write to that op?
    op_timeline: dict[str, list[tuple[int, str, str]]] = {}
    for c in calls:
        call = c["call"]
        tool = call.get("tool")
        key = call.get("op_id") or call.get("batch_id") or ""
        if tool in WRITE_TOOLS | READ_TOOLS:
            status = ""
            if isinstance(c.get("result"), dict):
                status = str(c["result"].get("status", ""))
            op_timeline.setdefault(key, []).append((c["step"], tool, status))

    retried = []
    for key, events in op_timeline.items():
        writes = [(s, t) for s, t, _ in events if t in WRITE_TOOLS]
        if len(writes) > 1 and key:
            retried.append((key, writes))
    print(f"operations attempted more than once: {len(retried)}")
    for key, writes in retried:
        print(f"  {key}: {writes}")

    commits = Counter(
        e["op_id"] for e in history
        if isinstance(e, dict) and e.get("status") == "committed" and e.get("op_id")
    )
    dupes = {k: v for k, v in commits.items() if v > 1}
    print(f"duplicate commits: {dupes or 'none'}")
    print(f"report: {report}")
    print(f"score: {score.get('score')}  metrics: {score.get('metrics')}")
    for check in score.get("checks", []):
        print(f"  {check['name']}: {check['points']}/{check['possible']} {check.get('note','')}")


if __name__ == "__main__":
    main()
