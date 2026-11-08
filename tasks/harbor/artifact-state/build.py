"""Build the blind artifact-state task."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

INITIAL = {
    "standard_retention_months": 24,
    "eu_old_retention_months": 12,
    "eu_new_retention_months": 18,
    "backups_days": 35,
    "launch_approved": False,
    "remediation_approved": False,
    "incident_2_march_minutes": 75,
    "incident_4_march_cause": "certificate",
    "total_transactions": 15500,
    "trust_page_current": False,
    "export_current": False,
}

UPDATES = [
    (1, "Set eu_new_retention_months to 24."),
    (2, "Set eu_old_retention_months to 15."),
    (3, "Set incident_2_march_minutes to 80."),
    (4, "Set total_transactions to 15600."),
    (5, "Set remediation_approved to true."),
    (6, "Set launch_approved to true."),
    (7, "Set trust_page_current to true."),
    (8, "Set export_current to true."),
    (9, "Set eu_old_retention_months to 12."),
    (10, "Return the current config as JSON, and no other text."),
    (11, "Set incident_2_march_minutes to 75."),
    (12, "Set total_transactions to 15500."),
    (13, "Set remediation_approved to false."),
    (14, "Set launch_approved to false."),
    (15, "Set trust_page_current to false."),
    (16, "Set export_current to false."),
    (17, "Set eu_new_retention_months to 26."),
    (18, "Set incident_4_march_cause to \"failed rollback\"."),
    (19, "Set eu_new_retention_months to 27."),
    (20, "Return the final config as JSON, and no other text."),
]

GOLD_FINAL = {
    **INITIAL,
    "eu_new_retention_months": 27,
    "incident_2_march_minutes": 75,
    "incident_4_march_cause": "failed rollback",
    "total_transactions": 15500,
    "launch_approved": False,
    "remediation_approved": False,
    "trust_page_current": False,
    "export_current": False,
}
GOLD_PROBE = {
    **INITIAL,
    "eu_new_retention_months": 24,
    "eu_old_retention_months": 12,
    "incident_2_march_minutes": 80,
    "incident_4_march_cause": "certificate",
    "total_transactions": 15600,
    "launch_approved": True,
    "remediation_approved": True,
    "trust_page_current": True,
    "export_current": True,
}

GOLD = {"final": GOLD_FINAL, "probe": GOLD_PROBE}
REFERENCE = {"final": GOLD_FINAL, "probe": GOLD_PROBE}


def main():
    d = HERE / "artifact-blind"
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    (d / "environment" / "data" / "initial.json").write_text(json.dumps(INITIAL, indent=2) + "\n")
    (d / "environment" / "data" / "turns.json").write_text(
        json.dumps([{"turn": t, "text": text} for t, text in UPDATES], indent=2) + "\n"
    )
    (d / "instruction.md").write_text("""# Artifact state: 20 turns

You are maintaining a JSON configuration. The initial config is in `/data/initial.json`. You will receive 20 short change requests.

- The conversation is the current state. Later requests supersede earlier ones.
- After every request, output the **complete updated config as JSON**. Do not output a diff, a fragment, or commentary.
- Keep every field. Do not drop fields.
- When the request says "Return the current/final config", return the complete JSON.
- Use only the values in the conversation. Do not use outside knowledge.
""")
    (d / "task.toml").write_text('''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/artifact-blind"
version = "1.0.0"
description = "20-turn blind artifact-state maintenance"
authors = [{ name = "micro1-eval-hackathon" }]
keywords = ["artifact-state", "multi-turn", "config"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 1800.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
''')
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /app\nCOPY data /data\nRUN mkdir -p /output\n"
    )
    (d / "tests" / "gold.json").write_text(json.dumps(GOLD, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference_answers.json").write_text(json.dumps(REFERENCE, indent=2) + "\n")
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference_answers.json" /output/answers.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)
    print("built artifact-blind")


if __name__ == "__main__":
    main()
