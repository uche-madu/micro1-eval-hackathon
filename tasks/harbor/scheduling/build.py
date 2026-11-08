"""Build the meeting-scheduling constraint task."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

PROBLEM = """# Schedule the Q3 audit review

Schedule eight meetings over Monday, Tuesday, and Wednesday, 09:00-17:00. Lunch is 12:00-13:00 and no meeting may overlap it. Rooms are A, B, and C; no room and no attendee may be double-booked. All times are local.

| Meeting | Duration | Attendees | Allowed day(s) | Allowed room(s) | Allowed window |
|---|---:|---|---|---|---|
| M1 | 60 | Alice, Bob | Mon | A | 09:00-11:00 |
| M2 | 90 | Bob, Chen | Tue or Wed | B | 10:00-12:00 |
| M3 | 45 | Alice, Dana | Wed | C | 09:00-12:00 |
| M4 | 60 | Chen, Dana | Tue or Wed | A | 13:00-16:00 |
| M5 | 120 | Alice, Chen, Dana | Wed | B | 13:00-16:00 |
| M6 | 30 | Bob, Dana | Tue | C | 09:00-10:00 |
| M7 | 60 | Alice, Bob, Chen, Dana, Evan | Wed | A | 15:00-17:00 |
| M8 | 90 | Alice, Bob, Chen | Mon or Tue | C | 10:30-12:00 or 14:00-16:00 |

Additional constraints:
- M2 must start after M6 ends.
- M8 must start after M1 ends.
- M5 must start after M4 ends.
- M7 must start after M5 ends.
- Meetings may not be split.

Return ONLY JSON:
```json
{"schedule": [{"meeting": "M1", "day": "Mon", "start": "09:00", "end": "10:00", "room": "A"}]}
```
Use 24-hour times. Every meeting must appear exactly once.
"""

REFERENCE = {"schedule": [
    {"meeting": "M1", "day": "Mon", "start": "09:00", "end": "10:00", "room": "A"},
    {"meeting": "M8", "day": "Mon", "start": "10:30", "end": "12:00", "room": "C"},
    {"meeting": "M6", "day": "Tue", "start": "09:00", "end": "09:30", "room": "C"},
    {"meeting": "M2", "day": "Tue", "start": "10:00", "end": "11:30", "room": "B"},
    {"meeting": "M4", "day": "Tue", "start": "13:00", "end": "14:00", "room": "A"},
    {"meeting": "M3", "day": "Wed", "start": "09:00", "end": "09:45", "room": "C"},
    {"meeting": "M5", "day": "Wed", "start": "13:00", "end": "15:00", "room": "B"},
    {"meeting": "M7", "day": "Wed", "start": "15:30", "end": "16:30", "room": "A"},
]}


def main():
    d = HERE / "schedule-audit"
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    (d / "environment" / "data" / "problem.md").write_text(PROBLEM)
    (d / "instruction.md").write_text(PROBLEM)
    (d / "task.toml").write_text('''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/schedule-audit"
version = "1.0.0"
description = "Eight-meeting constraint scheduling"
authors = [{ name = "micro1-eval-hackathon" }]
keywords = ["planning", "constraints", "scheduling"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 900.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
''')
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /app\nCOPY data /data\nRUN mkdir -p /output\n"
    )
    (d / "tests" / "gold.json").write_text(json.dumps({"reference": REFERENCE}, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference_schedule.json").write_text(json.dumps(REFERENCE, indent=2) + "\n")
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference_schedule.json" /output/schedule.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)
    print("built schedule-audit")


if __name__ == "__main__":
    main()
