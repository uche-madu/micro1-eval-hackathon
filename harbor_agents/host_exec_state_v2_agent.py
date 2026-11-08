"""Harbor agent for the hardened execution-state benchmark.

The model chooses structured operations. The environment owns the persistent
state, the dependency graph, the deterministic faults, and the ledger. The agent
only mediates the conversation and writes the outcome for the verifier.
"""

from __future__ import annotations

import base64
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

from harbor_agents.exec_state_env import ExecStateEnv


class HostExecStateV2Agent(BaseAgent):
    capabilities = AgentCapabilities()

    @staticmethod
    def name() -> str:
        return "host-exec-state-v2"

    def version(self) -> str:
        return "2.0.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        task = json.loads(await self._read(environment, "/data/task.json"))
        env = ExecStateEnv(task)
        report: dict[str, Any] = {}

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": instruction
                + "\n\nYou are the operator. Call exactly one tool per turn. "
                "Dependencies are enforced; an out-of-order call is rejected.",
            },
            {
                "role": "user",
                "content": "Begin. Execute the operations and finish when the target state is reached.",
            },
        ]
        usage_totals: dict[str, int] = {}
        transcript: list[dict[str, Any]] = []
        for step in range(1, 161):
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
            result = env.call(call if isinstance(call, dict) else {})
            observation = json.dumps(result)
            messages.append({"role": "user", "content": observation})
            transcript.append({"step": step, "raw": content, "call": call, "result": result})

        await self._write(environment, "/output/state.json", json.dumps(env.state, indent=2))
        await self._write(environment, "/output/history.json", json.dumps(env.history, indent=2))
        await self._write(environment, "/output/report.json", json.dumps(report, indent=2))
        await self._write(environment, "/output/events.json", json.dumps(transcript, indent=2))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "state.json").write_text(json.dumps(env.state, indent=2))
        (self.logs_dir / "history.json").write_text(json.dumps(env.history, indent=2))
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
            or "micro1-harbor-exec-state-v2"
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
                    "User-Agent": "micro1-harbor-exec-state-v2/2.0",
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
