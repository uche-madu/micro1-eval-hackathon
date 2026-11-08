#!/usr/bin/env python3
"""Deterministic checks for the hardened execution-state environment.

No model is involved. Each scenario drives ExecStateEnv directly and asserts the
semantics the review asked for. Run from the repository root:

    python3 tasks/harbor/exec-state-v2/test_env.py
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from harbor_agents.exec_state_env import ExecStateEnv  # noqa: E402

HERE = Path(__file__).resolve().parent
TASK_PATH = HERE / "exec-state2-a" / "environment" / "data" / "task.json"
GOLD_PATH = HERE / "exec-state2-a" / "tests" / "gold.json"


def load() -> tuple[dict[str, Any], dict[str, Any]]:
    return json.loads(TASK_PATH.read_text()), json.loads(GOLD_PATH.read_text())


def call(env: ExecStateEnv, op_id: str) -> dict[str, Any]:
    op = env.ops[op_id]
    payload = {"tool": op["tool"], "op_id": op_id, "record_id": op.get("record_id")}
    if op.get("fields"):
        payload["fields"] = op["fields"]
    if op.get("owner"):
        payload["owner"] = op["owner"]
    if op.get("note"):
        payload["note"] = op["note"]
    return env.call(payload)


def apply_with_recovery(env: ExecStateEnv, op_id: str) -> None:
    first = call(env, op_id)
    if first.get("status") == "timeout":
        status = env.get_operation(op_id).get("status")
        assert status == "committed", f"{op_id} timeout but not committed: {status}"
        return
    if first.get("status") == "error" and first.get("reason") == "fail_before":
        second = call(env, op_id)
        assert second.get("status") == "ok", f"{op_id} retry failed: {second}"
        return
    assert first.get("status") == "ok", f"{op_id} failed: {first}"


def run_perfect(env: ExecStateEnv, task: dict[str, Any]) -> None:
    batch = task["batch"]
    batch_ids = batch["op_ids"]
    for op in task["ops"]:
        op_id = op["op_id"]
        if op_id == batch_ids[0]:
            first = env.run_batch({"tool": "run_batch", "batch_id": "B1"})
            assert first.get("status") == "partial", first
            failed = [m for m in batch_ids if env.get_operation(m).get("status") != "committed"]
            second = env.run_batch({"tool": "run_batch", "batch_id": "B1", "op_ids": failed})
            assert second.get("status") == "ok", second
            continue
        if op_id in batch_ids:
            continue
        apply_with_recovery(env, op_id)


def dump_and_score(env: ExecStateEnv, gold: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    import importlib.util

    tmp = Path(tempfile.mkdtemp(prefix="exec2-test-"))
    (tmp / "state.json").write_text(json.dumps(env.state))
    (tmp / "history.json").write_text(json.dumps(env.history))
    (tmp / "report.json").write_text(json.dumps(report))
    (tmp / "events.json").write_text(json.dumps([]))
    spec = importlib.util.spec_from_file_location("exec2_scorer", HERE / "score_template.py")
    assert spec and spec.loader
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    return scorer.score(tmp, gold)


def expect(name: str, condition: bool, detail: Any = "") -> None:
    print(("PASS " if condition else "FAIL ") + name + ("" if condition else f" :: {detail}"))


def main() -> None:
    task, gold = load()

    # 1. Perfect execution reaches the target with no defects.
    env = ExecStateEnv(copy.deepcopy(task))
    run_perfect(env, task)
    env.list_records()
    result = dump_and_score(env, gold, {"complete": True, "summary": "done"})
    expect("perfect final state", env.state == gold["target"], env.state)
    expect("perfect score 100", result["score"] == 100.0, result["score"])
    expect("perfect has no missing", result["metrics"]["missing_ops"] == 0)
    expect("perfect has no duplicates", result["metrics"]["duplicate_ops"] == 0)
    expect("perfect has no violations", result["metrics"]["dependency_violations"] == 0)

    # 2. The first batch attempt cannot be bypassed with op_ids.
    env = ExecStateEnv(copy.deepcopy(task))
    for op_id in ["OP01", "OP11"]:
        apply_with_recovery(env, op_id)
    bypass = env.run_batch({"tool": "run_batch", "batch_id": "B1", "op_ids": ["OP21"]})
    expect("first batch subset rejected", bypass.get("reason") == "batch_bypass", bypass)
    expect("batch not marked attempted", env.batch_attempted is False)

    # 3. The batch cannot run before its prerequisites.
    env = ExecStateEnv(copy.deepcopy(task))
    early = env.run_batch({"tool": "run_batch", "batch_id": "B1"})
    expect("batch before deps rejected", early.get("reason") == "dependency", early)
    expect("batch not marked attempted after dependency error", env.batch_attempted is False)

    # 4. An earlier operation cannot run after a dependent committed.
    env = ExecStateEnv(copy.deepcopy(task))
    for op_id in ["OP06", "OP16", "OP26"]:
        apply_with_recovery(env, op_id)
    out_of_order = call(env, "OP16")
    expect("update after approval/assignment rejected", out_of_order.get("reason") == "out_of_order", out_of_order)
    expect("out-of-order call logged", any(e.get("status") == "out_of_order_violation" for e in env.history))

    # 5. Retrying a lost-ack operation before its dependent commits duplicates.
    env = ExecStateEnv(copy.deepcopy(task))
    for op_id in ["OP01", "OP02", "OP03"]:
        first = call(env, op_id)
        if first.get("status") == "timeout":
            second = call(env, op_id)
            assert second.get("status") == "ok", second
    duplicate_count = sum(1 for e in env.history if e.get("op_id") == "OP03" and e.get("status") == "committed")
    expect("lost-ack retry duplicates", duplicate_count == 2, duplicate_count)

    # 6. The stale read is the true pre-update value; list_records is current.
    env = ExecStateEnv(copy.deepcopy(task))
    for op_id in ["OP01", "OP02", "OP03", "OP04"]:
        first = call(env, op_id)
        if first.get("status") == "timeout":
            env.get_operation(op_id)
    update = call(env, "OP14")
    assert update.get("status") == "timeout", update
    stale = env.get_record("R04")
    current = env.list_records()["R04"]
    expect("stale read is pre-update", stale.get("status") == "draft", stale)
    expect("list_records is current", current.get("status") == "active", current)

    # 7. A missing operation and a false completion are separate.
    env = ExecStateEnv(copy.deepcopy(task))
    run_perfect(env, task)
    env.list_records()
    env.history = [e for e in env.history if not (e.get("op_id") == "OP26" and e.get("status") == "committed")]
    result = dump_and_score(env, gold, {"complete": True, "summary": "done"})
    expect("missing op detected", result["metrics"]["missing_ops"] == 1, result["metrics"]["missing_ops"])
    expect("false completion contract detected", result["metrics"]["false_completion_contract"] is True)
    expect("final state still correct", result["metrics"]["final_state_ok"] is True)


if __name__ == "__main__":
    main()
