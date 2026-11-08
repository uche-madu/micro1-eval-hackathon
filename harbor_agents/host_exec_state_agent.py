"""Harbor agent for execution-state divergence.

The model chooses structured operations. The agent owns the persistent state,
applies the deterministic fault schedule, exposes read/reconciliation tools, and
writes the authoritative state, history, and report for the verifier.
"""

from __future__ import annotations

import base64
import copy
import json
import os
import re
import shlex
import time
import urllib.error
import urllib.request
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class HostExecStateAgent(BaseAgent):
    capabilities = AgentCapabilities()

    @staticmethod
    def name() -> str:
        return "host-exec-state"

    def version(self) -> str:
        return "1.0.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        task = json.loads(await self._read(environment, "/data/task.json"))
        ops = {op["op_id"]: op for op in task["ops"]}
        faults = task.get("faults", {})
        batch = task.get("batch", {})
        batch_ids = batch.get("op_ids", [])
        batch_id = batch.get("batch_id", "B1")
        partial_commit = int(batch.get("partial_commit", 3))
        stale = task.get("stale", {})

        state: dict[str, Any] = copy.deepcopy(task.get("initial", {}))
        history: list[dict[str, Any]] = []
        attempts: dict[str, int] = {}
        ledger: dict[str, str] = {}
        report: dict[str, Any] = {}
        stale_snapshot: dict[str, Any] = {}
        stale_served: set[str] = set()
        batch_attempted = False

        def log(op_id: str, tool: str, status: str, record_id: str | None = None) -> None:
            history.append({"op_id": op_id, "tool": tool, "status": status,
                            "record_id": record_id, "attempt": attempts.get(op_id, 0)})

        def apply(op_id: str, tool: str, record_id: str, fields: dict[str, Any] | None = None,
                  owner: str | None = None, note: str | None = None) -> None:
            fields = fields or {}
            if tool == "create_account":
                state[record_id] = {
                    "name": fields.get("name", ""),
                    "segment": fields.get("segment", ""),
                    "region": fields.get("region", ""),
                    "owner": "unassigned",
                    "status": "draft",
                    "notes": [],
                }
            elif tool == "update_account":
                state.setdefault(record_id, {}).update(fields)
            elif tool == "approve_account":
                state.setdefault(record_id, {})["status"] = "approved"
            elif tool in {"assign_owner", "transfer_owner"}:
                state.setdefault(record_id, {})["owner"] = owner
            elif tool == "add_note":
                state.setdefault(record_id, {}).setdefault("notes", []).append(note)
            elif tool == "delete_account":
                state.pop(record_id, None)

        def execute(op_id: str, tool: str, record_id: str, fields: dict[str, Any] | None = None,
                    owner: str | None = None, note: str | None = None) -> dict[str, Any]:
            nonlocal batch_attempted
            if op_id not in ops:
                return {"status": "error", "message": f"unknown op_id {op_id}"}
            expected = ops[op_id]
            if tool != expected["tool"] or record_id != str(expected.get("record_id", "")):
                return {"status": "error", "op_id": op_id,
                        "message": "operation spec mismatch: use the tool and record declared for this op_id."}
            # Apply the declared operation, not caller-supplied field values, so the
            # final state can only be reached by executing the operation ledger.
            fields = expected.get("fields")
            owner = expected.get("owner")
            note = expected.get("note")
            if op_id in batch_ids and not batch_attempted and tool != "run_batch":
                return {"status": "error", "message": "OP21-OP25 are batch B1; use run_batch."}
            attempt = attempts.get(op_id, 0) + 1
            attempts[op_id] = attempt
            fault = faults.get(op_id) if attempt == 1 else None
            if fault == "fail_before":
                ledger[op_id] = "failed"
                log(op_id, tool, "failed", record_id)
                return {"status": "error", "op_id": op_id,
                        "message": "Commit failed before applying; state unchanged."}
            before = copy.deepcopy(state.get(record_id))
            apply(op_id, tool, record_id, fields, owner, note)
            ledger[op_id] = "committed"
            log(op_id, tool, "committed", record_id)
            if tool == "update_account" and record_id in stale and record_id not in stale_snapshot:
                # A cached read after this update will return the true pre-update
                # snapshot once: a genuinely stale observation, not a fabricated one.
                stale_snapshot[record_id] = before
            if fault == "lost_ack":
                return {"status": "timeout", "op_id": op_id,
                        "message": "No acknowledgement; outcome unknown. Reconcile before retrying."}
            return {"status": "ok", "op_id": op_id}

        def run_batch(op_ids: list[str] | None) -> dict[str, Any]:
            nonlocal batch_attempted
            members = op_ids or batch_ids
            invalid = [op for op in members if op not in batch_ids]
            if invalid:
                return {"status": "error", "message": f"not in {batch_id}: {invalid}"}
            if not batch_attempted and op_ids is None:
                batch_attempted = True
                committed = 0
                for idx, op_id in enumerate(batch_ids):
                    attempts[op_id] = attempts.get(op_id, 0) + 1
                    if idx < partial_commit:
                        op = ops[op_id]
                        apply(op_id, "approve_account", op["record_id"])
                        ledger[op_id] = "committed"
                        log(op_id, "approve_account", "committed", op["record_id"])
                        committed += 1
                    else:
                        ledger[op_id] = "failed"
                        log(op_id, "approve_account", "failed", ops[op_id]["record_id"])
                return {"status": "partial", "batch_id": batch_id,
                        "committed": committed, "failed": len(batch_ids) - committed,
                        "message": "Some members applied; inspect records/history before retrying."}
            batch_attempted = True
            for op_id in members:
                op = ops[op_id]
                attempts[op_id] = attempts.get(op_id, 0) + 1
                apply(op_id, "approve_account", op["record_id"])
                ledger[op_id] = "committed"
                log(op_id, "approve_account", "committed", op["record_id"])
            return {"status": "ok", "batch_id": batch_id, "committed": len(members)}

        def snapshot(record_id: str) -> dict[str, Any] | None:
            if record_id in stale_snapshot and record_id not in stale_served and record_id in state:
                stale_served.add(record_id)
                return copy.deepcopy(stale_snapshot[record_id])
            return copy.deepcopy(state.get(record_id))

        messages: list[dict[str, str]] = [
            {"role": "system", "content": instruction + "\n\nYou are the operator. Call one tool per turn."},
            {"role": "user", "content": "Begin. Execute the operations and finish when the target state is reached."},
        ]
        usage_totals: dict[str, int] = {}
        transcript: list[dict[str, Any]] = []
        for step in range(1, 121):
            content, usage, error = self._call(messages)
            if not content:
                raise RuntimeError(f"step {step} model call failed: {error}")
            messages.append({"role": "assistant", "content": content})
            for key in ("prompt_tokens", "completion_tokens"):
                usage_totals[key] = usage_totals.get(key, 0) + int(usage.get(key) or 0)
            call = self._extract_json(content)
            tool = call.get("tool")
            if tool == "finish":
                report = call.get("report") if isinstance(call.get("report"), dict) else {}
                transcript.append({"step": step, "raw": content, "call": call, "result": "finish"})
                break
            if tool == "list_records":
                log("", "list_records", "read")
                result: Any = copy.deepcopy(state)
            elif tool == "get_record":
                rid = str(call.get("record_id", ""))
                log("", "get_record", "read", rid)
                result = snapshot(rid) or {"status": "not_found", "record_id": rid}
            elif tool == "get_history":
                rid = str(call.get("record_id", ""))
                log("", "get_history", "read", rid)
                result = [event for event in history if event.get("record_id") == rid]
            elif tool == "get_operation":
                op_id = str(call.get("op_id", ""))
                log("", "get_operation", "read")
                if op_id == batch_id:
                    statuses = [ledger.get(op, "unknown") for op in batch_ids]
                    result = {"batch_id": batch_id, "committed_count": statuses.count("committed"),
                              "failed_count": statuses.count("failed")}
                else:
                    result = {"op_id": op_id, "status": ledger.get(op_id, "unknown"),
                              "attempts": attempts.get(op_id, 0)}
            elif tool == "run_batch":
                result = run_batch(call.get("op_ids"))
                log("", "run_batch", "read")
            elif tool in {"create_account", "update_account", "approve_account", "assign_owner",
                          "transfer_owner", "add_note", "delete_account"}:
                op_id = str(call.get("op_id", ""))
                record_id = str(call.get("record_id", ""))
                fields = call.get("fields") if isinstance(call.get("fields"), dict) else {}
                owner = call.get("owner")
                note = call.get("note")
                if tool == "transfer_owner" and ledger.get(ops[op_id].get("depends_on", "")) != "committed":
                    result = {"status": "error", "op_id": op_id,
                              "message": "dependency not committed; retry the prerequisite first."}
                    log(op_id, tool, "failed", record_id)
                else:
                    result = execute(op_id, tool, record_id, fields, owner, note)
            else:
                result = {"status": "error", "message": "unknown tool"}
                log("", str(tool), "error")
            observation = json.dumps(result)
            messages.append({"role": "user", "content": observation})
            transcript.append({"step": step, "raw": content, "call": call, "result": result})

        await self._write(environment, "/output/state.json", json.dumps(state, indent=2))
        await self._write(environment, "/output/history.json", json.dumps(history, indent=2))
        await self._write(environment, "/output/report.json", json.dumps(report, indent=2))
        await self._write(environment, "/output/events.json", json.dumps(transcript, indent=2))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "state.json").write_text(json.dumps(state, indent=2))
        (self.logs_dir / "history.json").write_text(json.dumps(history, indent=2))
        (self.logs_dir / "report.json").write_text(json.dumps(report, indent=2))
        (self.logs_dir / "transcript.json").write_text(json.dumps(transcript, indent=2))
        (self.logs_dir / "usage.json").write_text(json.dumps(usage_totals, indent=2))
        context.n_input_tokens = usage_totals.get("prompt_tokens")
        context.n_output_tokens = usage_totals.get("completion_tokens")
        context.cost_usd = 0.0

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        text = content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {}
        try:
            obj = json.loads(text[start : end + 1], strict=False)
            return obj if isinstance(obj, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    async def _read(self, environment: BaseEnvironment, path: str) -> str:
        result = await environment.exec(f"cat {path}")
        if result.return_code != 0 or not result.stdout:
            raise RuntimeError(f"could not read {path}: {result.stderr}")
        return result.stdout

    async def _write(self, environment: BaseEnvironment, path: str, content: str) -> None:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        result = await environment.exec(
            f"mkdir -p /output && printf %s {shlex.quote(encoded)} | base64 -d > {path}"
        )
        if result.return_code != 0:
            raise RuntimeError(f"could not write {path}: {result.stderr}")

    def _call(self, messages: list[dict[str, str]]) -> tuple[str | None, dict[str, Any], str | None]:
        key = (
            self._extra_env.get("OPENCODE_API_KEY")
            or self._extra_env.get("OPENCODE_GO_API_KEY")
            or os.environ.get("OPENCODE_API_KEY")
            or os.environ.get("OPENCODE_GO_API_KEY")
        )
        base = (
            self._extra_env.get("OPENCODE_BASE_URL")
            or os.environ.get("OPENCODE_BASE_URL")
            or "https://opencode.ai/zen/v1"
        ).rstrip("/")
        session = (
            self._extra_env.get("OPENCODE_SESSION")
            or os.environ.get("OPENCODE_SESSION")
            or "micro1-harbor-exec-state"
        )
        if not key:
            return None, {}, "OPENCODE_API_KEY is missing"
        payload = json.dumps(
            {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 1200,
                "messages": messages,
            }
        ).encode("utf-8")
        error = ""
        for attempt in range(2):
            request = urllib.request.Request(
                f"{base}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": "micro1-harbor-exec-state/1.0",
                    "x-opencode-session": session,
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=600) as response:
                    data = json.loads(response.read().decode("utf-8"))
                message = (data.get("choices") or [{}])[0].get("message") or {}
                content = message.get("content") or ""
                usage = data.get("usage") or {}
                if content:
                    return content, usage, None
                error = "empty content"
            except urllib.error.HTTPError as exc:
                error = f"http_{exc.code}: {exc.read().decode('utf-8', errors='replace')[:300]}"
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
            time.sleep(2)
        return None, {}, error or "empty response"
