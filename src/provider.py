"""Minimal OpenRouter client. Standard library only."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


class OpenCodeZen:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://opencode.ai/zen/v1",
        session: str = "micro1-d1s-pilot",
    ):
        if not api_key:
            raise ValueError("OPENCODE_API_KEY is missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = session

    def _post(self, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "micro1-eval-pilot/1.0",
            "X-Title": "micro1-d1s-pilot",
        }
        if self.session:
            headers["x-opencode-session"] = self.session
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def chat(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 6000,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        attempts: list[dict[str, Any]] = []
        content: str | None = None
        error: str | None = None
        response: dict[str, Any] | None = None
        started = time.time()
        for attempt in range(2):
            attempt_started = time.time()
            try:
                response = self._post(payload)
                choice = (response.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                content = message.get("content")
                if not content:
                    # Some providers put the text in a reasoning field; record it,
                    # but treat an empty content field as a provider error.
                    content = message.get("reasoning") or ""
                error = None if content else "empty_content"
            except urllib.error.HTTPError as exc:
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                except Exception:
                    detail = ""
                error = f"http_{exc.code}: {detail}"
            except Exception as exc:  # noqa: BLE001 - provider boundary
                error = f"{type(exc).__name__}: {exc}"
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "latency_s": round(time.time() - attempt_started, 3),
                    "error": error,
                }
            )
            if content:
                break
            time.sleep(1.5)
        usage = (response or {}).get("usage") or {}
        return {
            "content": content,
            "model": model,
            "usage": usage,
            "cost": usage.get("cost"),
            "latency_s": round(time.time() - started, 3),
            "attempts": attempts,
            "error": None if content else (error or "unknown_error"),
            "provider_response_id": (response or {}).get("id"),
        }

    def models(self) -> list[str]:
        request = urllib.request.Request(
            f"{self.base_url}/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [m["id"] for m in data.get("data", [])]
