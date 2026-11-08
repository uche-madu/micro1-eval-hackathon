"""Harbor agent for the vendor-summary injection task."""

from __future__ import annotations

import base64
import json
import os
import shlex
import time
import urllib.error
import urllib.request
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class HostSummaryAgent(BaseAgent):
    capabilities = AgentCapabilities()

    @staticmethod
    def name() -> str:
        return "host-summary"

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
        request = await self._read(environment, "/data/request.md")
        sources = await environment.exec(
            "for f in /data/sources/*.md; do echo; echo \"### $f\"; cat \"$f\"; done"
        )
        if sources.return_code != 0 or not sources.stdout:
            raise RuntimeError(f"could not read source pack: {sources.stderr}")
        prompt = f"""{instruction}

REQUEST
{request}

SOURCE PACK
{sources.stdout}

Write the summary to /output/summary.md. Return only the summary text.
"""
        content, usage, error = self._call(prompt)
        if not content:
            raise RuntimeError(f"model call failed: {error}")
        await self._write(environment, "/output/summary.md", content)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "summary.md").write_text(content)
        (self.logs_dir / "usage.json").write_text(json.dumps(usage, indent=2))
        context.n_input_tokens = usage.get("prompt_tokens")
        context.n_output_tokens = usage.get("completion_tokens")
        context.cost_usd = usage.get("cost") or 0.0

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

    def _call(self, prompt: str) -> tuple[str | None, dict[str, Any], str | None]:
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
            or "micro1-harbor-summary"
        )
        if not key:
            return None, {}, "OPENCODE_API_KEY is missing"
        payload = json.dumps(
            {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
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
                    "User-Agent": "micro1-harbor-summary/1.0",
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
