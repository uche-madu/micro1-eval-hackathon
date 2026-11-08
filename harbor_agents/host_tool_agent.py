"""Harbor agent that lets the model run shell commands in /workspace."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class HostToolAgent(BaseAgent):
    capabilities = AgentCapabilities()

    @staticmethod
    def name() -> str:
        return "host-tool"

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
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": instruction
                + "\n\nYou can run shell commands in /workspace. Respond with exactly one JSON object: "
                '{"tool":"shell","command":"..."} to run a command, or {"final":true} when done. '
                "Do not include commentary outside the JSON.",
            },
            {"role": "user", "content": "Begin. Inspect the workspace and fix pipeline.py."},
        ]
        transcript: list[dict[str, Any]] = []
        usage_totals: dict[str, int] = {}
        for step in range(1, 16):
            content, usage, error = self._call(messages)
            if not content:
                raise RuntimeError(f"step {step} model call failed: {error}")
            messages.append({"role": "assistant", "content": content})
            for key in ("prompt_tokens", "completion_tokens"):
                usage_totals[key] = usage_totals.get(key, 0) + int(usage.get(key) or 0)
            payload = self._extract_json(content)
            if payload.get("final") is True:
                transcript.append({"step": step, "assistant": content, "final": True})
                break
            command = payload.get("command")
            if payload.get("tool") != "shell" or not isinstance(command, str) or not command.strip():
                observation = (
                    'Invalid tool request. Respond with {"tool":"shell","command":"..."} '
                    'or {"final":true}.'
                )
                messages.append({"role": "user", "content": observation})
                transcript.append({"step": step, "assistant": content, "error": observation})
                continue
            result = await environment.exec(command=command, cwd="/workspace", timeout_sec=120)
            output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
            output = output[-4000:]
            observation = f"exit={result.return_code}\n{output}"
            messages.append({"role": "user", "content": observation})
            transcript.append({"step": step, "command": command, "result": observation})

        self.logs_dir.mkdir(parents=True, exist_ok=True)
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
            or "micro1-harbor-tool"
        )
        if not key:
            return None, {}, "OPENCODE_API_KEY is missing"
        payload = json.dumps(
            {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 2000,
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
                    "User-Agent": "micro1-harbor-tool/1.0",
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
