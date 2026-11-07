"""A minimal Harbor agent that calls the OpenCode Go API on the host.

The built-in OpenCode CLI path bills through the Zen account, which has no
funds in this environment. This agent uses the same OpenCode Zen
OpenAI-compatible endpoint and the Go credential directly, then writes the
task outputs into the container for the Harbor verifier.

It is a Harbor agent: Harbor still creates the task environment, runs this
agent, and verifies the output with the task's tests.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import shlex
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class HostBriefAgent(BaseAgent):
    capabilities = AgentCapabilities()

    @staticmethod
    def name() -> str:
        return "host-brief"

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
        sources = await environment.exec(
            "for f in /data/sources/*.md; do echo; echo \"### $f\"; cat \"$f\"; done"
        )
        if sources.return_code != 0 or not sources.stdout:
            raise RuntimeError(f"could not read source pack: {sources.stderr}")

        prompt = f"""{instruction}

SOURCE PACK CONTENTS (already in /data/sources)
{sources.stdout}

You cannot run shell commands. Return ONLY a JSON object with exactly two keys:
{{"brief_markdown": "<the complete markdown brief>", "findings": {{"findings": [...]}}}}
Do not wrap the JSON in code fences. Do not add commentary outside the JSON.
The brief must be 1,500-2,000 words and use exactly the 10 required level-2 headings.
"""
        content, usage, error = self._call(prompt)
        if not content:
            raise RuntimeError(f"model call failed: {error}")

        text = content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError("model did not return a JSON object")
        obj = json.loads(text[start : end + 1], strict=False)
        brief = obj.get("brief_markdown") or ""
        findings = obj.get("findings")
        if not brief or not isinstance(findings, dict):
            raise RuntimeError("model JSON is missing brief_markdown or findings")

        await self._write(environment, "/output/brief.md", brief)
        await self._write(
            environment, "/output/findings.json", json.dumps(findings, indent=2)
        )

        context.n_input_tokens = usage.get("prompt_tokens")
        context.n_output_tokens = usage.get("completion_tokens")
        context.cost_usd = usage.get("cost") or 0.0
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "brief.md").write_text(brief)
        (self.logs_dir / "findings.json").write_text(json.dumps(findings, indent=2))
        (self.logs_dir / "host_brief.txt").write_text(
            json.dumps(
                {
                    "model": self.model_name,
                    "usage": usage,
                    "error": error,
                    "brief_chars": len(brief),
                    "findings": len(findings.get("findings", [])),
                },
                indent=2,
            )
        )

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
            or "micro1-harbor"
        )
        if not key:
            return None, {}, "OPENCODE_API_KEY is missing"
        payload = json.dumps(
            {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        for attempt in range(2):
            request = urllib.request.Request(
                f"{base}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": "micro1-harbor-brief/1.0",
                    "x-opencode-session": session,
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=1200) as response:
                    data = json.loads(response.read().decode("utf-8"))
                message = (data.get("choices") or [{}])[0].get("message") or {}
                content = message.get("content") or ""
                usage = data.get("usage") or {}
                if content:
                    return content, usage, None
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:300]
                error = f"http_{exc.code}: {body}"
            except Exception as exc:  # noqa: BLE001 - provider boundary
                error = f"{type(exc).__name__}: {exc}"
            time.sleep(2)
        return None, {}, error if "error" in locals() else "empty response"
