#!/usr/bin/env python3
"""Checker for the eight-meeting scheduling task."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("/output/schedule.json")
DEFAULT_GOLD = HERE / "gold.json"
DEFAULT_VERIFIER = Path("/logs/verifier")

SPEC = {
    "M1": {"minutes": 60, "people": ["Alice", "Bob"], "days": ["Mon"], "rooms": ["A"], "window": [(540, 660)]},
    "M2": {"minutes": 90, "people": ["Bob", "Chen"], "days": ["Tue", "Wed"], "rooms": ["B"], "window": [(600, 720)]},
    "M3": {"minutes": 45, "people": ["Alice", "Dana"], "days": ["Wed"], "rooms": ["C"], "window": [(540, 720)]},
    "M4": {"minutes": 60, "people": ["Chen", "Dana"], "days": ["Tue", "Wed"], "rooms": ["A"], "window": [(780, 960)]},
    "M5": {"minutes": 120, "people": ["Alice", "Chen", "Dana"], "days": ["Wed"], "rooms": ["B"], "window": [(780, 960)]},
    "M6": {"minutes": 30, "people": ["Bob", "Dana"], "days": ["Tue"], "rooms": ["C"], "window": [(540, 600)]},
    "M7": {"minutes": 60, "people": ["Alice", "Bob", "Chen", "Dana", "Evan"], "days": ["Wed"], "rooms": ["A"], "window": [(900, 1020)]},
    "M8": {"minutes": 90, "people": ["Alice", "Bob", "Chen"], "days": ["Mon", "Tue"], "rooms": ["C"], "window": [(630, 720), (840, 960)]},
}
LUNCH = (720, 780)
DAY_INDEX = {"Mon": 0, "Tue": 1, "Wed": 2}
DEPS = [("M2", "M6"), ("M8", "M1"), ("M5", "M4"), ("M7", "M5")]


def parse_time(value: Any) -> int | None:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value).strip())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def score(output_path: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    try:
        obj = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "schema", "points": 0, "possible": 5,
                       "note": "valid schedule JSON", "error": f"{type(exc).__name__}: {exc}"})
        return finish(checks, details)

    rows = obj.get("schedule") if isinstance(obj.get("schedule"), list) else []
    checks.append({"name": "schema", "points": 5 if rows else 0, "possible": 5, "note": "schedule list"})

    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("meeting"), str):
            by_id.setdefault(row["meeting"], row)
    ids_ok = set(by_id) == set(SPEC) and len(rows) == len(SPEC)
    checks.append({"name": "all_meetings_once", "points": 15 if ids_ok else 0, "possible": 15,
                   "note": "M1-M8 exactly once", "got": sorted(by_id)})

    intervals: dict[str, tuple[int, int, int]] = {}
    valid_count = 0
    for mid, spec in SPEC.items():
        row = by_id.get(mid)
        if not row:
            continue
        start, end = parse_time(row.get("start")), parse_time(row.get("end"))
        day, room = row.get("day"), row.get("room")
        ok = (
            start is not None
            and end is not None
            and end - start == spec["minutes"]
            and day in spec["days"]
            and room in spec["rooms"]
            and any(a <= start and end <= b for a, b in spec["window"])
        )
        if ok:
            valid_count += 1
            intervals[mid] = (DAY_INDEX[day], start, end)
        details[mid] = {"row": row, "valid": ok}
    checks.append({"name": "meeting_windows", "points": 5 * valid_count, "possible": 40,
                   "note": "duration, day, room, and allowed window"})

    people: dict[str, list[tuple[int, int, int]]] = {}
    rooms: dict[str, list[tuple[int, int, int]]] = {}
    for mid, (day, start, end) in intervals.items():
        for person in SPEC[mid]["people"]:
            people.setdefault(person, []).append((day, start, end))
        room = str(by_id[mid].get("room"))
        rooms.setdefault(room, []).append((day, start, end))
    conflict = False
    for values in list(people.values()) + list(rooms.values()):
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                if values[i][0] == values[j][0] and overlaps(values[i][1:], values[j][1:]):
                    conflict = True
    checks.append({"name": "no_double_booking", "points": 0 if conflict else 20, "possible": 20,
                   "note": "no attendee or room overlap"})

    lunch_ok = all(not overlaps((start, end), LUNCH) for _, start, end in intervals.values())
    checks.append({"name": "lunch_blackout", "points": 10 if lunch_ok else 0, "possible": 10,
                   "note": "12:00-13:00 clear"})

    def after(a: str, b: str) -> bool:
        if a not in intervals or b not in intervals:
            return False
        ad, astart, _ = intervals[a]
        bd, _, bend = intervals[b]
        return ad > bd or (ad == bd and astart >= bend)

    deps_ok = all(after(a, b) for a, b in DEPS)
    checks.append({"name": "dependencies", "points": 10 if deps_ok else 0, "possible": 10,
                   "note": "M2>M6, M8>M1, M5>M4, M7>M5"})
    return finish(checks, details)


def finish(checks: list[dict[str, Any]], details: dict[str, Any], **extra: Any) -> dict[str, Any]:
    points = sum(check["points"] for check in checks)
    possible = sum(check["possible"] for check in checks)
    return {
        "score": round(100.0 * points / possible, 3) if possible else 0.0,
        "reward": round(points / possible, 6) if possible else 0.0,
        "points": round(points, 3),
        "possible": round(possible, 3),
        "checks": checks,
        "details": details,
        **extra,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--verifier", type=Path, default=DEFAULT_VERIFIER)
    args = parser.parse_args()
    result = score(args.output)
    args.verifier.mkdir(parents=True, exist_ok=True)
    (args.verifier / "score.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.verifier / "reward.txt").write_text(f"{result['reward']:.6f}\n")
    print(json.dumps({"score": result["score"], "reward": result["reward"], "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
