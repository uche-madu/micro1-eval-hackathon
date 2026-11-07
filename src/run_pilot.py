"""Run the D1-S pilot.

Usage:
  python -m src.run_pilot --dry-run
  python -m src.run_pilot --models openai/gpt-6.1-terra ... --trials 3
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from src.grader import format_summary, grade, summarize
from src.prompts import production_open_prompt, production_prompt, recognition_prompt
from src.provider import OpenCodeZen, load_env
from src.reference import production_reference, recognition_reference

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "runs"
RAW_DIR = RUNS_DIR / "raw"
RESULTS_DIR = ROOT / "results"

DEFAULT_MODELS = [
    "opencode-go/gpt-6-luna",
    "opencode-go/gemini-4-argon",
    "opencode-go/claude-haiku-5-5",
    "opencode-go/qwen3.8-flash",
]
DEFAULT_TRIALS = {
    "recognition": 2,
    "production": 3,
    "production_open": 3,
    "oracle": 1,
    "oracle_competing": 1,
    "procedure": 1,
}


def slug(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", model).strip("_")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_tasks(task_ids: list[str]) -> list[dict[str, Any]]:
    tasks = []
    for task_id in task_ids:
        path = TASKS_DIR / f"{task_id}.json"
        if not path.exists():
            raise SystemExit(f"missing task file: {path}")
        tasks.append(json.loads(path.read_text(encoding="utf-8")))
    return tasks


def build_prompt(task: dict[str, Any], condition: str) -> str:
    if condition == "recognition":
        return recognition_prompt(task)
    if condition == "production":
        return production_prompt(task)
    if condition == "production_open":
        return production_open_prompt(task)
    if condition == "oracle":
        return production_prompt(task, oracle=True)
    if condition == "oracle_competing":
        return production_prompt(task, oracle=True, competing=True)
    if condition == "procedure":
        return production_prompt(task, procedure=True)
    raise ValueError(f"unknown condition: {condition}")


def reference_for(task: dict[str, Any], condition: str) -> str:
    if condition == "recognition":
        return recognition_reference(task)
    return production_reference(task)


def grade_condition(task: dict[str, Any], condition: str, raw: str) -> dict[str, Any]:
    return grade(task, "recognition" if condition == "recognition" else "production", raw)


def completed_keys(path: Path) -> set[tuple[str, str, str, int]]:
    keys: set[tuple[str, str, str, int]] = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except Exception:
            continue
        keys.add(
            (
                record.get("model", ""),
                record.get("task", ""),
                record.get("condition", ""),
                int(record.get("trial", 0)),
            )
        )
    return keys


def run_one(
    client: OpenCodeZen | None,
    task: dict[str, Any],
    condition: str,
    model: str,
    trial: int,
    run_id: str,
    dry_run: bool,
    max_tokens: int = 6000,
) -> dict[str, Any]:
    prompt = build_prompt(task, condition)
    if dry_run:
        raw = reference_for(task, condition)
        response = {
            "content": raw,
            "usage": {},
            "cost": None,
            "latency_s": 0.0,
            "attempts": [],
            "error": None,
            "provider_response_id": "reference",
        }
    else:
        assert client is not None
        response = client.chat(model, prompt, max_tokens=max_tokens)
        raw = response["content"] or ""

    graded = grade_condition(task, condition, raw)
    record = {
        "run_id": run_id,
        "timestamp": now(),
        "model": model,
        "task": task["task_id"],
        "condition": condition,
        "trial": trial,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "raw_chars": len(raw),
        "raw": raw,
        "usage": response.get("usage") or {},
        "cost": response.get("cost"),
        "latency_s": response.get("latency_s"),
        "attempts": response.get("attempts") or [],
        "provider_error": response.get("error"),
        "grade": graded,
    }

    raw_path = RAW_DIR / run_id / f"{task['task_id']}_{condition}_{slug(model)}_t{trial}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(
            {
                "prompt": prompt,
                "raw": raw,
                "model": model,
                "task": task["task_id"],
                "condition": condition,
                "trial": trial,
                "response": response,
                "grade": graded,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=["T1", "T2"])
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["recognition", "production", "production_open", "oracle", "oracle_competing", "procedure"],
        choices=["recognition", "production", "production_open", "oracle", "oracle_competing", "procedure"],
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--trials", type=int, default=None)
    parser.add_argument("--max-calls", type=int, default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-tag", default=None)
    args = parser.parse_args()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = args.output_tag or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RUNS_DIR / f"pilot_{run_id}.jsonl"
    done = completed_keys(out_path)
    tasks = load_tasks(args.tasks)

    client = None
    if not args.dry_run:
        env = load_env(ROOT / ".env")
        client = OpenCodeZen(
            env.get("OPENCODE_API_KEY", ""),
            env.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1"),
            env.get("OPENCODE_SESSION", "micro1-d1s-pilot"),
        )

    jobs: list[tuple[dict[str, Any], str, str, int]] = []
    for task in tasks:
        for condition in args.conditions:
            trials = args.trials if args.trials is not None else DEFAULT_TRIALS[condition]
            for model in args.models:
                for trial in range(1, trials + 1):
                    if (model, task["task_id"], condition, trial) in done:
                        continue
                    jobs.append((task, condition, model, trial))
    if args.max_calls is not None:
        jobs = jobs[: args.max_calls]
    if not jobs:
        print("nothing to do; all requested jobs already recorded")
        return

    print(f"run_id={run_id} jobs={len(jobs)}")
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_one, client, task, condition, model, trial, run_id, args.dry_run, args.max_tokens): (
                task["task_id"],
                condition,
                model,
                trial,
            )
            for task, condition, model, trial in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # noqa: BLE001 - keep the run alive
                record = {
                    "run_id": run_id,
                    "timestamp": now(),
                    "model": key[2],
                    "task": key[0],
                    "condition": key[1],
                    "trial": key[3],
                    "raw": "",
                    "provider_error": f"{type(exc).__name__}: {exc}",
                    "grade": {
                        "condition": key[1],
                        "parse_error": "harness_exception",
                        "n": 0,
                        "accuracy": 0.0,
                        "strict": 0.0,
                        "mean_score": 0.0,
                        "rows": [],
                    },
                }
            records.append(record)
            with out_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            status = record["grade"].get("accuracy")
            err = record.get("provider_error") or record["grade"].get("parse_error") or ""
            print(f"  {key[0]} {key[1]:16} {key[2]:32} t{key[3]} acc={status} {err}")

    # Reload every record for this run, including resumed ones.
    all_records = []
    for line in out_path.read_text(encoding="utf-8").splitlines():
        try:
            all_records.append(json.loads(line))
        except Exception:
            continue
    summary = summarize(all_records)
    result_path = RESULTS_DIR / f"pilot_results_{run_id}.json"
    result_path.write_text(
        json.dumps({"run_id": run_id, "summary": summary, "records": all_records}, indent=2),
        encoding="utf-8",
    )
    print()
    print(format_summary(summary))
    print(f"\nwrote {out_path}")
    print(f"wrote {result_path}")


if __name__ == "__main__":
    main()
