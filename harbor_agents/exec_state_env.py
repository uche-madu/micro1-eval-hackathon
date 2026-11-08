"""Deterministic execution-state environment for the hardened benchmark.

The environment owns the authoritative state, the operation ledger, the fault
schedule, and the dependency graph. It is pure Python and independent of the
model adapter so the semantics can be tested without a model.

Design rules:
- An operation may be applied only after every prerequisite has committed
  (`depends_on`) and before any operation that depends on it has committed.
  Out-of-order calls are rejected and recorded as violations.
- The first batch attempt must be the full batch; explicit subsets are allowed
  only after the first attempt has produced a partial result.
- Record reads are observations: `get_record` may serve one true pre-update
  snapshot, while `list_records` returns the current full state. The operation
  ledger (`get_operation`, `get_history`) is authoritative.
"""

from __future__ import annotations

import copy
from typing import Any


class ExecStateEnv:
    def __init__(self, task: dict[str, Any]) -> None:
        self.ops: dict[str, dict[str, Any]] = {op["op_id"]: op for op in task["ops"]}
        self.required_ops: list[str] = [op["op_id"] for op in task["ops"]]
        self.deps: dict[str, list[str]] = task.get("dependencies", {})
        self.dependents: dict[str, list[str]] = {oid: [] for oid in self.ops}
        for oid, prerequisites in self.deps.items():
            for prerequisite in prerequisites:
                self.dependents.setdefault(prerequisite, []).append(oid)
        self.faults: dict[str, str] = task.get("faults", {})
        batch = task.get("batch", {})
        self.batch_id: str = batch.get("batch_id", "B1")
        self.batch_ids: list[str] = list(batch.get("op_ids", []))
        self.partial_commit: int = int(batch.get("partial_commit", 3))
        self.stale_record: str | None = task.get("stale_record")

        self.state: dict[str, Any] = copy.deepcopy(task.get("initial", {}))
        self.ledger: dict[str, str] = {}
        self.attempts: dict[str, int] = {}
        self.history: list[dict[str, Any]] = []
        self.stale_snapshot: dict[str, Any] | None = None
        self.stale_served = False
        self.batch_attempted = False
        self.seq = 0

    # ------------------------------------------------------------------ logging
    def _log(
        self,
        tool: str,
        status: str,
        op_id: str = "",
        record_id: str | None = None,
        **extra: Any,
    ) -> None:
        self.seq += 1
        event: dict[str, Any] = {
            "seq": self.seq,
            "op_id": op_id,
            "tool": tool,
            "status": status,
            "record_id": record_id,
            "attempt": self.attempts.get(op_id, 0),
        }
        event.update(extra)
        self.history.append(event)

    # -------------------------------------------------------------- dependencies
    def _check_order(self, op_id: str) -> tuple[bool, str, dict[str, Any]]:
        unmet = [dep for dep in self.deps.get(op_id, []) if self.ledger.get(dep) != "committed"]
        if unmet:
            return False, "dependency", {"unmet": unmet}
        committed_dependents = [
            dep for dep in self.dependents.get(op_id, []) if self.ledger.get(dep) == "committed"
        ]
        if committed_dependents:
            return False, "out_of_order", {"committed_dependents": committed_dependents}
        return True, "", {}

    # ---------------------------------------------------------------- mutation
    def _apply(self, op_id: str) -> None:
        op = self.ops[op_id]
        tool = op["tool"]
        record_id = str(op.get("record_id", ""))
        fields = op.get("fields") or {}
        if tool == "create_account":
            self.state[record_id] = {
                "name": fields.get("name", ""),
                "segment": fields.get("segment", ""),
                "region": fields.get("region", ""),
                "owner": "unassigned",
                "status": "draft",
                "notes": [],
            }
        elif tool == "update_account":
            self.state.setdefault(record_id, {}).update(fields)
        elif tool == "approve_account":
            self.state.setdefault(record_id, {})["status"] = "approved"
        elif tool in {"assign_owner", "transfer_owner"}:
            self.state.setdefault(record_id, {})["owner"] = op.get("owner")
        elif tool == "add_note":
            self.state.setdefault(record_id, {}).setdefault("notes", []).append(op.get("note"))
        elif tool == "delete_account":
            self.state.pop(record_id, None)

    # ------------------------------------------------------------------ execute
    def execute(self, call: dict[str, Any]) -> dict[str, Any]:
        tool = str(call.get("tool", ""))
        op_id = str(call.get("op_id", ""))
        record_id = str(call.get("record_id", ""))
        if op_id not in self.ops:
            return {"status": "error", "reason": "unknown_op", "message": f"unknown op_id {op_id}"}
        expected = self.ops[op_id]
        if tool != expected["tool"] or record_id != str(expected.get("record_id", "")):
            return {
                "status": "error",
                "reason": "spec_mismatch",
                "op_id": op_id,
                "message": "operation spec mismatch: use the tool and record declared for this op_id.",
            }
        if op_id in self.batch_ids and not self.batch_attempted:
            return {
                "status": "error",
                "reason": "batch_member",
                "op_id": op_id,
                "message": f"{op_id} is part of batch {self.batch_id}; run the batch with run_batch.",
            }

        ok, reason, details = self._check_order(op_id)
        if not ok:
            self._log(tool, f"{reason}_violation", op_id, record_id, **details)
            return {
                "status": "error",
                "reason": reason,
                "op_id": op_id,
                **details,
                "message": "operation out of order: prerequisites or dependents were not satisfied.",
            }

        attempt = self.attempts.get(op_id, 0) + 1
        self.attempts[op_id] = attempt
        fault = self.faults.get(op_id) if attempt == 1 else None
        if fault == "fail_before":
            self.ledger[op_id] = "failed"
            self._log(tool, "failed", op_id, record_id, reason="fail_before")
            return {
                "status": "error",
                "reason": "fail_before",
                "op_id": op_id,
                "message": "Commit failed before applying; state unchanged.",
            }

        before = copy.deepcopy(self.state.get(record_id))
        self._apply(op_id)
        self.ledger[op_id] = "committed"
        self._log(tool, "committed", op_id, record_id, fault=fault or "")
        if (
            expected["tool"] == "update_account"
            and record_id == self.stale_record
            and self.stale_snapshot is None
        ):
            # The next cached record read returns the true pre-update value once.
            self.stale_snapshot = before

        if fault == "lost_ack":
            return {
                "status": "timeout",
                "op_id": op_id,
                "message": "No acknowledgement; outcome unknown. Reconcile before retrying.",
            }
        return {"status": "ok", "op_id": op_id}

    # ----------------------------------------------------------------- run_batch
    def run_batch(self, call: dict[str, Any]) -> dict[str, Any]:
        supplied = call.get("op_ids")
        if supplied is not None and not isinstance(supplied, list):
            return {"status": "error", "reason": "bad_request", "message": "op_ids must be a list."}
        members = list(supplied) if supplied is not None else list(self.batch_ids)
        invalid = [op for op in members if op not in self.batch_ids]
        if invalid:
            return {
                "status": "error",
                "reason": "bad_request",
                "message": f"not in {self.batch_id}: {invalid}",
            }

        if not self.batch_attempted:
            if supplied is not None:
                self._log("run_batch", "batch_bypass_rejected", "", None, batch_id=self.batch_id)
                return {
                    "status": "error",
                    "reason": "batch_bypass",
                    "batch_id": self.batch_id,
                    "message": "The first batch attempt must run the full batch; subsets are allowed only after a partial result.",
                }
            violations = []
            for op_id in self.batch_ids:
                ok, reason, details = self._check_order(op_id)
                if not ok:
                    violations.append({"op_id": op_id, "reason": reason, **details})
            if violations:
                self._log(
                    "run_batch",
                    "dependency_violation",
                    "",
                    None,
                    batch_id=self.batch_id,
                    violations=violations,
                )
                return {
                    "status": "error",
                    "reason": "dependency",
                    "batch_id": self.batch_id,
                    "violations": violations,
                    "message": "Batch prerequisites are not met; apply the earlier operations first.",
                }
            self.batch_attempted = True
            committed = 0
            for index, op_id in enumerate(self.batch_ids):
                self.attempts[op_id] = self.attempts.get(op_id, 0) + 1
                if index < self.partial_commit:
                    self._apply(op_id)
                    self.ledger[op_id] = "committed"
                    self._log(
                        "approve_account",
                        "committed",
                        op_id,
                        self.ops[op_id]["record_id"],
                    )
                    committed += 1
                else:
                    self.ledger[op_id] = "failed"
                    self._log(
                        "approve_account",
                        "failed",
                        op_id,
                        self.ops[op_id]["record_id"],
                        reason="partial_batch",
                    )
            return {
                "status": "partial",
                "batch_id": self.batch_id,
                "committed": committed,
                "failed": len(self.batch_ids) - committed,
                "message": "Some members applied; inspect records/history before retrying.",
            }

        violations = []
        for op_id in members:
            ok, reason, details = self._check_order(op_id)
            if not ok:
                violations.append({"op_id": op_id, "reason": reason, **details})
        if violations:
            self._log(
                "run_batch",
                "dependency_violation",
                "",
                None,
                batch_id=self.batch_id,
                violations=violations,
            )
            return {
                "status": "error",
                "reason": "dependency",
                "batch_id": self.batch_id,
                "violations": violations,
                "message": "Batch prerequisites are not met; apply the earlier operations first.",
            }

        for op_id in members:
            self.attempts[op_id] = self.attempts.get(op_id, 0) + 1
            self._apply(op_id)
            self.ledger[op_id] = "committed"
            self._log("approve_account", "committed", op_id, self.ops[op_id]["record_id"])
        return {"status": "ok", "batch_id": self.batch_id, "committed": len(members)}

    # -------------------------------------------------------------------- reads
    def list_records(self) -> dict[str, Any]:
        self._log("list_records", "read")
        return copy.deepcopy(self.state)

    def get_record(self, record_id: str) -> dict[str, Any]:
        self._log("get_record", "read", record_id=record_id)
        if self.stale_snapshot is not None and not self.stale_served and record_id == self.stale_record:
            self.stale_served = True
            return copy.deepcopy(self.stale_snapshot)
        return copy.deepcopy(self.state.get(record_id)) or {
            "status": "not_found",
            "record_id": record_id,
        }

    def get_operation(self, op_id: str) -> dict[str, Any]:
        self._log("get_operation", "read", op_id=op_id)
        if op_id == self.batch_id:
            statuses = [self.ledger.get(member, "unknown") for member in self.batch_ids]
            return {
                "batch_id": self.batch_id,
                "committed_count": statuses.count("committed"),
                "failed_count": statuses.count("failed"),
            }
        return {
            "op_id": op_id,
            "status": self.ledger.get(op_id, "unknown"),
            "attempts": self.attempts.get(op_id, 0),
        }

    def get_history(self, record_id: str) -> list[dict[str, Any]]:
        self._log("get_history", "read", record_id=record_id)
        return [event for event in self.history if event.get("record_id") == record_id]

    def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        tool = payload.get("tool")
        if tool == "list_records":
            return self.list_records()
        if tool == "get_record":
            return self.get_record(str(payload.get("record_id", "")))
        if tool == "get_operation":
            return self.get_operation(str(payload.get("op_id", "")))
        if tool == "get_history":
            return self.get_history(str(payload.get("record_id", "")))
        if tool == "run_batch":
            return self.run_batch(payload)
        if tool in {
            "create_account",
            "update_account",
            "approve_account",
            "assign_owner",
            "transfer_owner",
            "add_note",
            "delete_account",
        }:
            return self.execute(payload)
        return {"status": "error", "reason": "unknown_tool", "message": "unknown tool"}
