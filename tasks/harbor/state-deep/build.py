"""Build the 30-turn deep state-integrity task."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

TURNS = [
    (1, "We are preparing the Q3 EU launch. Baseline: standard retention 24 months; EU retention 12 months; backups 35 days under a separate schedule. Acknowledge briefly."),
    (2, "Amendment A is signed. Effective 1 March 2026, EU retention is 18 months for accounts opened on or after 1 January 2026. Older EU accounts remain at 12 months."),
    (3, "The Board approves a temporary 15-month rule for EU accounts opened before 1 January 2026, effective immediately."),
    (4, "Draft Amendment B proposes 24 months for EU accounts opened on or after 1 January 2026. It is not approved. The trust page and system export show 12 months and are stale."),
    (5, "The Q3 launch is not approved until the trust page and system export are updated and the update is recorded."),
    (6, "March incidents: INC-031 on 2 March, 75 minutes, expired certificate, 12,400 failed transactions. INC-032 on 4 March, 45 minutes, 3,100 failed transactions. The draft postmortem attributes both to the certificate and is not approved. The remediation plan is a draft and is not approved."),
    (7, "Note the current state. Do not answer final questions yet."),
    (8, "The Board approves Draft Amendment B, effective immediately. New-account EU retention is now 24 months. It does not change the old-account rule."),
    (9, "Two corrections: the temporary 15-month old-account rule is withdrawn (old accounts return to 12 months); the 4 March incident was caused by a failed rollback, not the certificate."),
    (10, "Return ONLY JSON: {\"old_eu\":\"...\",\"new_eu\":\"...\",\"draft_b\":\"...\",\"incident_4_march\":\"...\"}."),
    (11, "The Board raises new-account EU retention from 24 to 26 months, effective immediately."),
    (12, "The old-account EU rule is temporarily extended to 16 months, effective immediately."),
    (13, "The 2 March incident duration is corrected from 75 to 80 minutes."),
    (14, "The total failed transactions across both incidents is corrected from 15,500 to 15,600."),
    (15, "The remediation plan is approved."),
    (16, "The trust page is updated and now shows the current EU position."),
    (17, "The system export is updated and now shows the current EU position."),
    (18, "The Q3 launch is approved, subject to the updated records."),
    (19, "The 16-month old-account extension is withdrawn; old accounts remain at 12 months."),
    (20, "Return ONLY JSON: {\"old_eu\":\"...\",\"new_eu\":\"...\",\"draft_b\":\"...\",\"incident_4_march\":\"...\",\"incident_2_march_duration\":\"...\",\"total_transactions\":\"...\",\"remediation\":\"...\",\"launch\":\"...\"}."),
    (21, "The Board revokes the launch approval pending a final audit."),
    (22, "The remediation plan approval is withdrawn; the plan is a draft again."),
    (23, "Draft Amendment B is confirmed effective immediately; it remains in effect."),
    (24, "The 2 March duration is restored to 75 minutes; the 80-minute correction was wrong."),
    (25, "The total failed transactions is restored to 15,500; the 15,600 figure was wrong."),
    (26, "The 4 March cause is confirmed as a failed rollback; no change."),
    (27, "The trust page update is rolled back; it shows 12 months again and is stale."),
    (28, "The system export update is rolled back; it shows 12 months again and is stale."),
    (29, "The old-account EU retention remains 12 months; the 16-month extension is not reinstated."),
    (30, "Return ONLY JSON: {\"old_eu\":\"...\",\"new_eu\":\"...\",\"draft_b\":\"...\",\"incident_4_march\":\"...\",\"incident_2_march_duration\":\"...\",\"total_transactions\":\"...\",\"remediation\":\"...\",\"launch\":\"...\"}."),
]

TURNS_JSON = [{"turn": t, "text": text, "expect": "recall1" if t == 10 else "recall2" if t == 20 else "final" if t == 30 else None} for t, text in TURNS]

GOLD = {
    "final": {
        "old_eu": {"answer": "12 months", "accept": ["12 months", "12"]},
        "new_eu": {"answer": "26 months", "accept": ["26 months", "26"]},
        "draft_b": {"answer": "in effect", "accept": ["in effect", "yes", "effective", "approved"]},
        "incident_4_march": {"answer": "failed rollback", "accept": ["failed rollback", "rollback", "failed rollback of chg-441"]},
        "incident_2_march_duration": {"answer": "75 minutes", "accept": ["75 minutes", "75"]},
        "total_transactions": {"answer": "15500", "accept": ["15500", "15,500"]},
        "remediation": {"answer": "not approved", "accept": ["not approved", "draft", "no"]},
        "launch": {"answer": "not approved", "accept": ["not approved", "no", "revoked", "revoked pending", "revoked pending a final audit"]},
    },
    "recall1": {
        "old_eu": {"answer": "12 months", "accept": ["12 months", "12"]},
        "new_eu": {"answer": "24 months", "accept": ["24 months", "24"]},
        "draft_b": {"answer": "approved", "accept": ["approved", "yes", "in effect"]},
        "incident_4_march": {"answer": "failed rollback", "accept": ["failed rollback", "rollback"]},
    },
    "recall2": {
        "old_eu": {"answer": "12 months", "accept": ["12 months", "12"]},
        "new_eu": {"answer": "26 months", "accept": ["26 months", "26"]},
        "draft_b": {"answer": "approved", "accept": ["approved", "yes", "in effect"]},
        "incident_4_march": {"answer": "failed rollback", "accept": ["failed rollback", "rollback"]},
        "incident_2_march_duration": {"answer": "80 minutes", "accept": ["80 minutes", "80"]},
        "total_transactions": {"answer": "15600", "accept": ["15600", "15,600"]},
        "remediation": {"answer": "approved", "accept": ["approved", "yes"]},
        "launch": {"answer": "approved", "accept": ["approved", "yes"]},
    },
    "stale_values": {
        "new_eu": ["24 months", "24"],
        "incident_2_march_duration": ["80 minutes", "80"],
        "total_transactions": ["15600", "15,600"],
        "remediation": ["approved", "yes"],
        "launch": ["approved", "yes"],
    },
}

REFERENCE = {
    "final": {k: v["answer"] for k, v in GOLD["final"].items()},
    "recall1": {k: v["answer"] for k, v in GOLD["recall1"].items()},
    "recall2": {k: v["answer"] for k, v in GOLD["recall2"].items()},
}


def main():
    d = HERE / "deep"
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    (d / "environment" / "data" / "turns.json").write_text(json.dumps(TURNS_JSON, indent=2) + "\n")
    (d / "instruction.md").write_text("""# Deep state integrity: 30 turns

You are the Chief of Staff at Northwind Cloud Services. This is a 30-turn conversation about the Q3 EU launch and the March incidents.

- The conversation is the current state. Later messages supersede earlier ones.
- Answer each user message. Keep the state; do not reset it.
- When the user asks for JSON, return ONLY the JSON object. Do not wrap it in code fences and do not add commentary.
- Use exact values from the conversation. Do not use outside knowledge.
""")
    (d / "task.toml").write_text('''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/state-deep"
version = "1.0.0"
description = "30-turn state-integrity conversation with late reversals"
authors = [{ name = "micro1-eval-hackathon" }]
keywords = ["state-integrity", "multi-turn", "deep"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 3600.0

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
    print("built state-deep")


if __name__ == "__main__":
    main()
