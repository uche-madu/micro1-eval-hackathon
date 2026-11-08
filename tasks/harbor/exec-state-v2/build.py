"""Build the hardened execution-state tasks (v2).

Differences from v1, all requested by review:
- dependencies are explicit in the table and enforced by the environment;
- the first batch attempt must be the full batch (no op_id bypass);
- `list_records` is documented as the current full state, `get_record` as cached;
- gold carries required ops and the dependency graph for the separated scorer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def build_ops(variant: str) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for i in range(1, 11):
        rid = f"R{i:02d}"
        ops.append(
            {
                "op_id": f"OP{i:02d}",
                "tool": "create_account",
                "record_id": rid,
                "fields": {
                    "name": f"{variant}-Account-{i}",
                    "segment": ["SMB", "Enterprise", "Public"][i % 3],
                    "region": ["NE", "SE", "MW", "W"][i % 4],
                },
            }
        )
    for i in range(1, 11):
        rid = f"R{i:02d}"
        ops.append(
            {
                "op_id": f"OP{10 + i:02d}",
                "tool": "update_account",
                "record_id": rid,
                "fields": {"status": "active", "region": ["NE", "SE", "MW", "W"][i % 4]},
            }
        )
    for i in range(1, 6):
        ops.append({"op_id": f"OP{20 + i:02d}", "tool": "approve_account", "record_id": f"R{i:02d}"})
    ops.append({"op_id": "OP26", "tool": "approve_account", "record_id": "R06"})
    for i in range(1, 6):
        ops.append(
            {
                "op_id": f"OP{26 + i:02d}",
                "tool": "assign_owner",
                "record_id": f"R{i:02d}",
                "owner": "Owner-2",
            }
        )
    for i in range(1, 5):
        ops.append(
            {
                "op_id": f"OP{31 + i:02d}",
                "tool": "transfer_owner",
                "record_id": f"R{i:02d}",
                "owner": "Owner-3",
            }
        )
    for i, rid in enumerate(["R01", "R02", "R03"], start=36):
        ops.append({"op_id": f"OP{i}", "tool": "add_note", "record_id": rid, "note": "Q3 review complete"})
    ops.append({"op_id": "OP39", "tool": "delete_account", "record_id": "R09"})
    ops.append({"op_id": "OP40", "tool": "delete_account", "record_id": "R10"})
    return ops


def dependencies(ops: list[dict[str, Any]]) -> dict[str, list[str]]:
    create = {f"R{i:02d}": f"OP{i:02d}" for i in range(1, 11)}
    update = {f"R{i:02d}": f"OP{10 + i:02d}" for i in range(1, 11)}
    approve = {f"R{i:02d}": f"OP{20 + i:02d}" for i in range(1, 7)}
    assign = {f"R{i:02d}": f"OP{26 + i:02d}" for i in range(1, 6)}
    deps: dict[str, list[str]] = {}
    for op in ops:
        op_id = op["op_id"]
        rid = str(op.get("record_id", ""))
        tool = op["tool"]
        if tool == "create_account":
            deps[op_id] = []
        elif tool == "update_account":
            deps[op_id] = [create[rid]]
        elif tool == "approve_account":
            deps[op_id] = [update[rid]]
        elif tool == "assign_owner":
            deps[op_id] = [approve[rid]]
        elif tool == "transfer_owner":
            deps[op_id] = [assign[rid]]
        elif tool == "add_note":
            deps[op_id] = [approve[rid]]
        elif tool == "delete_account":
            deps[op_id] = [update[rid]]
        else:
            deps[op_id] = []
    return deps


def apply(state: dict[str, Any], op: dict[str, Any]) -> None:
    rid = str(op.get("record_id", ""))
    fields = op.get("fields") or {}
    if op["tool"] == "create_account":
        state[rid] = {
            "name": fields.get("name", ""),
            "segment": fields.get("segment", ""),
            "region": fields.get("region", ""),
            "owner": "unassigned",
            "status": "draft",
            "notes": [],
        }
    elif op["tool"] == "update_account":
        state.setdefault(rid, {}).update(fields)
    elif op["tool"] == "approve_account":
        state.setdefault(rid, {})["status"] = "approved"
    elif op["tool"] in {"assign_owner", "transfer_owner"}:
        state.setdefault(rid, {})["owner"] = op.get("owner")
    elif op["tool"] == "add_note":
        state.setdefault(rid, {}).setdefault("notes", []).append(op.get("note"))
    elif op["tool"] == "delete_account":
        state.pop(rid, None)


def target_for(ops: list[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for op in ops:
        apply(state, op)
    return state


FAULTS = {
    "OP03": "lost_ack",
    "OP14": "lost_ack",
    "OP36": "lost_ack",
    "OP07": "fail_before",
    "OP27": "fail_before",
    "OP31": "fail_before",
}
BATCH = {"batch_id": "B1", "op_ids": [f"OP{i}" for i in range(21, 26)], "partial_commit": 3}
STALE_RECORD = "R04"

INSTRUCTION = """# Execute the account operations

You are operating a customer-account system. The target end state is the result of each operation below having taken effect exactly once, in dependency order.

Operations may fail before committing, succeed but lose their acknowledgement, or partially complete. The operation ledger is authoritative for whether an operation committed; `list_records` returns the current full state, while `get_record` is a cached observation and may be stale. Use the tools to determine what actually happened: do not assume a failed operation did not commit, and do not repeat an operation that already committed. Do not create duplicate side effects. If an operation failed before committing, retry it; if it committed but the acknowledgement was lost, do not repeat it.

Dependencies are explicit in the table and enforced by the system. Apply an operation only after every operation it depends on has committed, and before any operation that depends on it. The system rejects an out-of-order operation; a rejection is a dependency violation, not a transient error.

Batch B1 (OP21-OP25) must be run as a full batch first. The first batch attempt must not supply `op_ids`; after a partial result, retry only the missing members.

{ops_table}

## Tools

Call exactly one JSON object per turn:

- `{{"tool":"list_records"}}`
- `{{"tool":"get_record","record_id":"R01"}}`
- `{{"tool":"get_operation","op_id":"OP03"}}`
- `{{"tool":"get_history","record_id":"R01"}}`
- `{{"tool":"create_account","op_id":"OP01","record_id":"R01","fields":{{...}}}}`
- `{{"tool":"update_account","op_id":"OP11","record_id":"R01","fields":{{...}}}}`
- `{{"tool":"approve_account","op_id":"OP21","record_id":"R01"}}`
- `{{"tool":"assign_owner","op_id":"OP27","record_id":"R01","owner":"Owner-2"}}`
- `{{"tool":"transfer_owner","op_id":"OP32","record_id":"R01","owner":"Owner-3"}}`
- `{{"tool":"add_note","op_id":"OP36","record_id":"R01","note":"Q3 review complete"}}`
- `{{"tool":"delete_account","op_id":"OP39","record_id":"R09"}}`
- `{{"tool":"run_batch","batch_id":"B1"}}` or, after a partial result, `{{"tool":"run_batch","batch_id":"B1","op_ids":["OP24","OP25"]}}`
- `{{"tool":"finish","report":{{"complete":true,"summary":"..."}}}}`

Read semantics:
- `list_records` returns the current full state.
- `get_record` returns a cached observation and may be stale; a stale read is not evidence that an operation did not commit.
- `get_operation` and `get_history` report committed operations; they are authoritative for whether an operation committed.

Write semantics:
- `create_account` is not idempotent: creating an existing `record_id` replaces the record and resets its status and notes.
- `update_account`, `approve_account`, `assign_owner`, and `transfer_owner` are idempotent when repeated with the same values, but a repeated commit is still a duplicate side effect.

Every operation call must include its `op_id`. Return only the JSON object.
"""


def ops_table(ops: list[dict[str, Any]]) -> str:
    lines = []
    for op in ops:
        extras = []
        if op.get("fields"):
            extras.append("fields=" + json.dumps(op["fields"], separators=(",", ":")))
        if op.get("owner"):
            extras.append("owner=" + op["owner"])
        if op.get("note"):
            extras.append("note=" + op["note"])
        deps = op.get("depends_on") or []
        dep_text = ", ".join(deps) if deps else "—"
        lines.append(
            f"| {op['op_id']} | {op['tool']} | {op.get('record_id','')} | {dep_text} | "
            + "; ".join(extras)
            + " |"
        )
    header = "| Op | Tool | Record | Depends on | Arguments |\n| --- | --- | --- | --- | --- |"
    return header + "\n" + "\n".join(lines)


def reference_bundle(ops: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    for index, op in enumerate(ops, start=1):
        history.append(
            {
                "seq": index,
                "op_id": op["op_id"],
                "tool": op["tool"],
                "status": "committed",
                "record_id": op.get("record_id"),
                "attempt": 1,
            }
        )
    history.append(
        {
            "seq": len(ops) + 1,
            "op_id": "",
            "tool": "list_records",
            "status": "read",
            "record_id": None,
            "attempt": 0,
        }
    )
    return {
        "state": target,
        "history": history,
        "report": {"complete": True, "summary": "All operations applied once in dependency order."},
    }


def write_task(name: str, variant: str) -> None:
    ops = build_ops(variant)
    deps = dependencies(ops)
    for op in ops:
        op["depends_on"] = deps[op["op_id"]]
    target = target_for(ops)
    d = HERE / name
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    task = {
        "initial": {},
        "ops": ops,
        "dependencies": deps,
        "faults": FAULTS,
        "batch": BATCH,
        "stale_record": STALE_RECORD,
    }
    (d / "environment" / "data" / "task.json").write_text(json.dumps(task, indent=2) + "\n")
    (d / "instruction.md").write_text(INSTRUCTION.format(ops_table=ops_table(ops)))
    (d / "task.toml").write_text(
        f'''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/{name}"
version = "2.0.0"
description = "Hardened execution-state divergence with explicit enforced dependencies"
authors = [{{ name = "micro1-eval-hackathon" }}]
keywords = ["execution-state", "idempotency", "reconciliation", "dependencies"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 5400.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
'''
    )
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /app\nCOPY data /data\n"
        "RUN mkdir -p /output\n"
    )
    gold = {
        "target": target,
        "required_ops": [op["op_id"] for op in ops],
        "dependencies": deps,
        "batch": BATCH,
        "faults": FAULTS,
        "stale_record": STALE_RECORD,
    }
    (d / "tests" / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference.json").write_text(
        json.dumps(reference_bundle(ops, target), indent=2) + "\n"
    )
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference.json" /output/reference.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)
    print(f"built {name}: {len(ops)} ops, {len(target)} records, {sum(len(v) for v in deps.values())} dependency edges")


def main() -> None:
    write_task("exec-state2-a", "Alpha")
    write_task("exec-state2-b", "Beta")
    print("built hardened exec-state tasks")


if __name__ == "__main__":
    main()
