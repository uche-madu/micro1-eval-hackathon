"""Build the 10-turn state-integrity tasks (short vs long context)."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

BASE_TURNS = [
    (1, "We are preparing the Q3 EU launch for Northwind Cloud Services. Baseline: standard retention is 24 months; EU retention is 12 months; backups are retained for 35 days under a separate schedule. Acknowledge the baseline briefly. Do not answer final questions yet."),
    (2, "Amendment A is signed. Effective 1 March 2026, EU retention is 18 months for accounts opened on or after 1 January 2026. Accounts opened before that date remain at 12 months. Note the change."),
    (3, "The Board has approved a temporary 15-month retention rule for EU accounts opened before 1 January 2026, effective immediately. Apply it to the old-account cohort. The rule is temporary."),
    (4, "Draft Amendment B proposes 24 months for EU accounts opened on or after 1 January 2026. It is not approved. The public trust page and the system-of-record export still show 12 months and are stale. The Data Protection Officer says not to rely on the export until it is updated."),
    (5, "The Q3 launch is not approved until the trust page and the system export are updated and the update is recorded. This is a precondition. Note it."),
    (6, "For the March incidents: INC-031 on 2 March, 75 minutes, expired certificate, 12,400 failed transactions. INC-032 on 4 March, 45 minutes, 3,100 failed transactions. The draft postmortem attributes both to the certificate; it is not approved. The remediation plan is a draft and is not approved."),
    (7, "Before the final questions, return ONLY JSON with the current state: {\"old_eu\":\"...\",\"new_eu\":\"...\",\"draft_b\":\"...\",\"incident_4_march\":\"...\"}."),
    (8, "The Board has now approved Draft Amendment B, effective immediately. For EU accounts opened on or after 1 January 2026, retention is now 24 months. It does not change the old-account rule. Apply the update."),
    (9, "Two corrections. First, the temporary 15-month rule for old EU accounts is withdrawn; old accounts remain at 12 months. Second, the 4 March incident was caused by a failed rollback of CHG-441, not the certificate. Apply both corrections."),
    (10, "Return ONLY JSON with the final answers: {\"Q1\":\"old EU retention\",\"Q2\":\"new EU retention\",\"Q3\":\"is Draft B in effect?\",\"Q4\":\"4 March cause\",\"Q5\":\"is the launch approved?\",\"Q6\":\"is the remediation plan approved?\"}."),
]

PAD = [
    "Earlier in the week the launch working group reviewed the account migration checklist. The discussion covered support coverage, the training schedule for the regional teams, and the order in which markets will be enabled. No decision was taken on the retention position. The group asked for a short summary at the next meeting and for the open actions to be tracked in the usual place. This background does not change any rule stated above.",
    "The commercial team also walked through the Q3 pipeline and the account-tier migration plan. Most of the discussion was about sequencing, owner assignments, and the support rota for the first two weeks after launch. The team noted that the operational readiness review is separate from the retention decision and that the two should not be conflated in the Board pack. No new retention rule was agreed in that discussion.",
    "The programme office circulated a short note on the launch checklist. It covers the support model, the escalation path, the customer communication plan, and the rollback procedure for the migration. The note is operational and does not restate the retention schedule. The programme office asked for the checklist to be kept separate from the legal position so that the Board can see which items are decision-bearing.",
    "The legal and compliance teams met to review the document pack. They discussed how the Board paper should distinguish approved instruments from drafts, exports, and informal notes. The meeting did not change any date or authority. The teams asked for the final memo to make the source of each statement clear and to avoid treating an operational record as a controlling instrument.",
    "The launch readiness review covered the customer-facing checklist and the internal approval path. The group noted that the operational records are maintained by different teams and that the review should not assume they are current without a specific confirmation. The review did not make a launch decision. It asked for the decision to be brought back once the record owners confirm the position.",
    "The incident review group met separately to discuss the March timeline. The group reviewed the incident log, the customer impact numbers, and the draft postmortem. The discussion focused on the difference between an approved incident record and a draft narrative. No new cause was agreed in that meeting. The group asked for the final memo to rely on the approved timelines and the audit note.",
    "The programme office also asked for a short recap of the current state before the final decision. This is a housekeeping request so that the Board pack and the conversation record agree. The recap is not a new decision. The group asked for the recap to be expressed as a compact JSON object so that it can be compared with the final answers later.",
    "The Board secretariat confirmed the meeting sequence and the papers for the next session. The secretariat noted that the Board can approve an instrument and still leave an operational precondition outstanding; the two are separate decisions. The secretariat asked for the final memo to distinguish them. No operational record was updated as part of the meeting preparation.",
    "The programme office circulated two late corrections after the meeting. The first concerned a temporary rule that had been introduced earlier and was now withdrawn. The second concerned an incident cause that had been stated incorrectly in the draft narrative. The corrections are recorded in the conversation; the earlier statements are superseded. The office asked for the final answers to reflect the corrections rather than the earlier state.",
    "The Board pack is now closed. The secretariat asked for the final answers in the requested JSON shape, with no commentary outside the object. The pack should reflect the latest state of the conversation, not an earlier snapshot. The secretariat will compare the final answers with the recap provided earlier; any difference should be explained by a later update, not by a change of interpretation.",
]


def long_text(index: int, text: str) -> str:
    return text + "\n\n" + PAD[index]


def write_task(name, turns, gold, reference):
    d = HERE / name
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    (d / "environment" / "data" / "turns.json").write_text(json.dumps(turns, indent=2) + "\n")
    (d / "instruction.md").write_text("""# Multi-turn state integrity

You are the Chief of Staff at Northwind Cloud Services. This is a multi-turn conversation about the Q3 EU launch and the March incidents.

- The conversation is the current state. Later messages supersede earlier ones.
- Answer each user message. Keep the state in mind; do not reset it.
- When the user asks for JSON, return ONLY the JSON object. Do not wrap it in code fences and do not add commentary.
- Use exact values from the conversation. Do not use outside knowledge.
""")
    (d / "task.toml").write_text(f'''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/{name}"
version = "1.0.0"
description = "10-turn state-integrity conversation"
authors = [{{ name = "micro1-eval-hackathon" }}]
keywords = ["state-integrity", "multi-turn", "recall-compliance"]

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
    (d / "tests" / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference_answers.json").write_text(json.dumps(reference, indent=2) + "\n")
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference_answers.json" /output/answers.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)


GOLD = {
    "final": {
        "Q1": {"answer": "12 months", "accept": ["12 months", "12"]},
        "Q2": {"answer": "24 months", "accept": ["24 months", "24"]},
        "Q3": {"answer": "yes", "accept": ["yes"]},
        "Q4": {"answer": "failed rollback", "accept": ["failed rollback", "rollback", "failed rollback of chg-441", "rollback failure"]},
        "Q5": {"answer": "no", "accept": ["no"]},
        "Q6": {"answer": "no", "accept": ["no"]},
    },
    "recall": {
        "old_eu": {"answer": "15 months", "accept": ["15 months", "15"]},
        "new_eu": {"answer": "18 months", "accept": ["18 months", "18"]},
        "draft_b": {"answer": "not approved", "accept": ["not approved", "no"]},
        "incident_4_march": {"answer": "certificate (per draft)", "accept": ["certificate", "certificate (per draft)", "cert"]},
    },
    "stale_values": {
        "Q1": ["15 months", "15"],
        "Q2": ["18 months", "18"],
        "Q3": ["no"],
        "Q4": ["certificate", "certificate (per draft)", "cert"],
    },
}

REFERENCE = {
    "final": {q: v["answer"] for q, v in GOLD["final"].items()},
    "recall": {k: v["answer"] for k, v in GOLD["recall"].items()},
}


def turns_for(long: bool):
    rows = []
    for i, (num, text) in enumerate(BASE_TURNS):
        rows.append({"turn": num, "text": long_text(i, text) if long else text})
    return rows


def main():
    write_task("state-short", turns_for(False), GOLD, REFERENCE)
    write_task("state-long", turns_for(True), GOLD, REFERENCE)
    print("built state-short and state-long")


if __name__ == "__main__":
    main()
