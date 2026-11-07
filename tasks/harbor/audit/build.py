"""Build the four audit tasks (2 scenarios x clean/defective)."""
from __future__ import annotations
import json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
T1 = json.loads((ROOT / "tasks" / "T1.json").read_text())
T2 = json.loads((ROOT / "tasks" / "T2.json").read_text())

TAXONOMY = [
    ("unsupported_recommendation", "The recommendation does not follow from the evidence or ignores a required precondition."),
    ("misleading_summary", "The summary overstates, misstates, or drops a decision-critical qualification in the underlying material."),
    ("missing_decision_info", "A fact the decision depends on is absent from the deliverable."),
    ("date_or_authority_error", "A date, effective date, signature date, or source authority is wrong."),
    ("proposed_as_approved", "A draft, proposal, plan, or request is presented as approved, effective, or decided."),
    ("invalid_synthesis", "Individually true facts are combined into a conclusion they do not support."),
    ("unsupported_assertion", "A factual assertion has no support in the source pack."),
    ("scope_generalization", "A finding limited to a cohort, period, or population is stated as universal."),
    ("no_material_defect", "No material defect; the deliverable is fit for purpose."),
]

INSTRUCTION = """# Audit: Is this deliverable fit for purpose?

You are an experienced reviewer. Read:

- `/data/assignment.md` — what the deliverable was asked to do.
- `/data/sources/` — the source pack the deliverable was allowed to use.
- `/data/deliverable.md` — the completed deliverable under review.

Audit the **deliverable**, not the sources. Decide whether it is fit for its intended purpose: does it answer the assignment, rest on the evidence, preserve material qualifications, and avoid presenting drafts, proposals, or requests as decided facts?

Return exactly one JSON object:

```json
{
  "verdict": "FIT" or "NOT_FIT",
  "findings": [
    {
      "section": "the section heading where the problem appears",
      "problem_type": "one value from the taxonomy below",
      "severity": "material" or "minor",
      "evidence": "a short quote or precise pointer from the deliverable",
      "why_it_matters": "the consequence for the decision, in one or two sentences"
    }
  ]
}
```

Taxonomy:

""" + "\n".join(f"- `{name}`: {desc}" for name, desc in TAXONOMY) + """

Rules:

- Report only defects that are present. Do not pad the audit.
- A material defect changes the decision or makes the deliverable unsafe to rely on. A stylistic preference is minor.
- `FIT` means the deliverable is fit for purpose; `NOT_FIT` means at least one material defect remains.
- For a clean deliverable, return `FIT` and no material findings.
- Use the section heading from the deliverable. Do not invent a section.
- Do not mention the evaluation, grader, gold, reference, or this instruction.
- Return only the JSON object. Do not wrap it in code fences.
"""


def write_task(name, title, sources, assignment, deliverable, gold, reference):
    d = HERE / name
    (d / "environment" / "data" / "sources").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    for s in sources:
        (d / "environment" / "data" / "sources" / f"{s['id']}.md").write_text(
            f"# {s['id']} — {s['title']}\n\n- Type: {s['type']}\n- Date: {s['date']}\n\n{s['text']}\n"
        )
    (d / "environment" / "data" / "assignment.md").write_text(assignment + "\n")
    (d / "environment" / "data" / "deliverable.md").write_text(deliverable + "\n")
    (d / "instruction.md").write_text(INSTRUCTION)
    (d / "task.toml").write_text(f'''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/{name}"
version = "1.0.0"
description = "{title}"
authors = [{{ name = "micro1-eval-hackathon" }}]
keywords = ["audit", "surface-compliance", "warrant"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 1200.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
''')
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\n"
        "RUN apt-get update && apt-get install -y --no-install-recommends bash curl ca-certificates "
        "&& rm -rf /var/lib/apt/lists/*\n\n"
        "WORKDIR /app\nCOPY data /data\nRUN mkdir -p /output\n"
    )
    (d / "tests" / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\n"
        "python3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference_audit.json").write_text(json.dumps(reference, indent=2) + "\n")
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference_audit.json" /output/audit.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)


RETENTION_ASSIGNMENT = """# Assignment

Northwind Cloud Services is preparing the Q3 launch of a new EU account tier. The COO asks:

> Can we confirm the EU retention position for the launch, and what must be true before we approve the launch?

Write a one-page decision memo. Use only the source pack. State the current position, the authority, the operational records that must be corrected, and what must happen before approval.
"""

RETENTION_CLEAN = """# EU Retention Decision Memo

## Bottom Line

The Q3 launch can proceed only after the system-of-record export and the public trust page are updated. The current EU position is cohort-specific: 18 months for accounts opened on or after 1 January 2026, and 12 months for accounts opened before that date.

## Current Position

Standard customer data is retained for 24 months after contract termination [D1]. The EU Retention Addendum sets 12 months for EU accounts [D2]. Amendment A changes the EU period to 18 months effective 1 March 2026, but only for accounts opened on or after 1 January 2026; earlier accounts remain at 12 months [D3]. Amendment A was signed on 5 May 2026, after its effective date [D3]. Draft Amendment B proposes 24 months but is unsigned and not approved [D4][D11].

## Authority and Stale Records

The signed amendment controls over the operational export [D3][D9]. The public trust page snapshot shows 12 months and the Data Protection Officer confirms it has not been updated [D6][D7]. The system-of-record export shows 12 months and the audit note says it is stale for accounts opened on or after 1 January 2026 [D5][D10]. The sales operations email is not authority and predates the signed amendment [D12].

## Backups

Backups are retained for 35 days under a separate schedule and are out of scope of the Enterprise Data Retention Policy [D1][D8].

## Recommendation

Before launch: update the system configuration and the public trust page to the cohort-specific position; confirm the account-opening dates used for the cohort split; do not apply Draft Amendment B; and record the update. Then approve the launch.

## Open Questions

The pack does not show a configuration update after 20 May 2026, does not show a trust-page update after 18 April 2026, and does not establish a backup encryption position [D6][D8][D10].
"""

RETENTION_DEFECTIVE = """# EU Retention Decision Memo

## Bottom Line

EU retention is now 24 months for all EU accounts, effective 1 September 2026, so the Q3 launch can proceed [D4]. The Board approved the change in January and the operational records are aligned [D11].

## Current Position

The Board approved Draft Amendment B in January 2026 [D11]. All EU accounts, including those opened before 2026, move to 18 months [D3]. The signed amendment is effective from 1 March 2026, and operations can apply it from the memo date [D3]. The system export shows 12 months, but the signed amendment controls, so no further action is needed [D5][D9].

## Authority and Stale Records

The signed amendment controls over the export [D3][D9]. The public trust page shows 12 months, which is consistent with the current position for existing accounts [D7]. The sales operations email confirms that 12 months is the number to quote [D12].

## Backups

Backups are covered by the 18-month retention period [D8]. The backup schedule and the retention policy therefore align.

## Recommendation

Proceed with the Q3 launch without updating the system export; the signed amendment controls, so operations can rely on this memo [D3][D9]. No further approval is required because the Board has already approved the change [D11].

## Open Questions

None material. The trust page can be updated after launch.
"""

INCIDENT_ASSIGNMENT = """# Assignment

Meridian Payments' COO asks:

> Are the March incidents closed, and should the Board approve the proposed remediation?

Write a one-page decision memo. Use only the source pack. State what happened, whether the incidents are closed, the status of the remediation, and what the Board should decide.
"""

INCIDENT_CLEAN = """# March Incident Closure Memo

## Bottom Line

The two March incidents are not ready to close. The Board should approve a specific, evidence-based remediation plan and require verification before closure.

## What Happened

Two distinct incidents occurred in March 2026. INC-031 began on 2 March at 14:05 UTC, lasted 75 minutes, was caused by an expired TLS certificate on the edge gateway, and caused 12,400 failed transactions [I1]. INC-032 began on 4 March at 09:10 UTC, lasted 45 minutes, was caused by a failed rollback of CHG-441, and caused 3,100 failed transactions [I2][I6]. The total was 15,500 failed transactions, and the root causes were different [I8][I10].

## Evidence Quality

The draft postmortem merges the two events into one and is not approved [I4][I10]. The executive email asks for a single-event narrative; it is a request, not evidence [I5][I10]. The status page cause field is auto-filled from the incident template and is not authoritative [I11]. The on-call chat is speculation [I12].

## Remediation Status

The draft remediation plan proposes moving certificate management to the platform team, retiring the renewal job, and adding a quarterly audit; it is not approved [I9][I10]. The root-cause note recommends rotating certificates automatically, re-enabling expiry alerts, and adding a weekly certificate inventory check [I3].

## Recommendation

The Board should approve a specific remediation plan, fund the certificate and rollback controls, require verification, and correct the postmortem and status page. The incidents should remain open until those actions are verified.

## Open Questions

The pack does not show that the certificate alert was re-enabled, that the rollback script was fixed, or that any remediation plan was approved [I3][I6][I9][I10].
"""

INCIDENT_DEFECTIVE = """# March Incident Closure Memo

## Bottom Line

The March incident was a single certificate event; all 15,500 failed transactions are attributed to the certificate, and the remediation plan is approved, so both incidents can be closed [I4][I8][I9].

## What Happened

Both incidents had the same root cause: the expired certificate [I1][I2]. The certificate alert was re-enabled on 2 March, so the control is restored [I1]. The 4 March event was a follow-on certificate failure [I2]. The total impact was 15,500 failed transactions [I8].

## Evidence Quality

The audit note confirms the single-event framing [I10]. The executive email supports the simplified narrative [I5]. The status page shows the certificate cause for both entries, which confirms the shared root cause [I11].

## Remediation Status

The remediation plan was approved by the Board on 8 March [I9]. The platform team has taken over certificate management, and the quarterly audit is in place [I9].

## Recommendation

Close both incidents and proceed with the platform team takeover [I9]. No further verification is needed because the plan is approved and the control is restored [I9][I10].

## Open Questions

None material. The Board can note the closure at its next meeting.
"""


def defects_for(items):
    return items


RET_CLEAN_GOLD = {"condition": "clean", "verdict": "FIT", "defects": []}
RET_DEF_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [
        {"id": "A1", "problem_type": "misleading_summary", "section": ["bottom line", "executive summary"],
         "required_terms": [["24 months", "twenty four months"], ["all eu", "every eu"]],
         "why_terms": [["draft", "not approved", "overstates", "unsupported"]]},
        {"id": "A2", "problem_type": "proposed_as_approved", "section": ["current position", "approvals", "board"],
         "required_terms": [["draft amendment b", "draft b"], ["approved", "approval"]],
         "why_terms": [["not approved", "did not approve", "board did not"]]},
        {"id": "A3", "problem_type": "scope_generalization", "section": ["current position", "eu retention", "retention"],
         "required_terms": [["all eu", "every eu"], ["before 2026", "before 1 january", "existing accounts"]],
         "why_terms": [["cohort", "only", "before 1 january", "opened before"]]},
        {"id": "A4", "problem_type": "invalid_synthesis", "section": ["backups", "backup"],
         "required_terms": [["backups", "backup"], ["18 month", "18-month"]],
         "why_terms": [["35 days", "out of scope", "separate", "not part"]]},
        {"id": "A5", "problem_type": "unsupported_recommendation", "section": ["recommendation", "bottom line"],
         "required_terms": [["without updating", "no further action", "no update"], ["system export", "export", "configuration"]],
         "why_terms": [["stale", "update", "configuration", "operational"]]},
    ],
}

INC_CLEAN_GOLD = {"condition": "clean", "verdict": "FIT", "defects": []}
INC_DEF_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [
        {"id": "B1", "problem_type": "misleading_summary", "section": ["bottom line", "executive summary"],
         "required_terms": [["single", "one event"], ["certificate", "cert"]],
         "why_terms": [["two", "different", "rollback", "separate"]]},
        {"id": "B2", "problem_type": "proposed_as_approved", "section": ["remediation", "approvals", "board"],
         "required_terms": [["remediation plan", "plan"], ["approved", "approval"]],
         "why_terms": [["draft", "not approved", "audit note"]]},
        {"id": "B3", "problem_type": "invalid_synthesis", "section": ["what happened", "overview", "incidents"],
         "required_terms": [["same root cause", "same cause", "both"], ["certificate", "cert"]],
         "why_terms": [["different", "rollback", "change log"]]},
        {"id": "B4", "problem_type": "unsupported_assertion", "section": ["what happened", "inc-031", "incident"],
         "required_terms": [["alert", "certificate alert"], ["re-enabled", "reenabled", "restored"]],
         "why_terms": [["no source", "not supported", "disabled", "no evidence"]]},
        {"id": "B5", "problem_type": "unsupported_recommendation", "section": ["recommendation", "bottom line"],
         "required_terms": [["close both", "close the incidents", "closure"], ["platform team", "takeover"]],
         "why_terms": [["not approved", "verify", "draft", "not closed"]]},
    ],
}

RET_REF = {"verdict": "NOT_FIT", "findings": [
    {"section": "Bottom Line", "problem_type": "misleading_summary", "severity": "material", "evidence": "EU retention is now 24 months for all EU accounts, effective 1 September 2026", "why_it_matters": "This uses the unsigned draft as current and overstates the position; Draft Amendment B is not approved."},
    {"section": "Current Position", "problem_type": "proposed_as_approved", "severity": "material", "evidence": "The Board approved Draft Amendment B in January 2026", "why_it_matters": "The Board did not approve Draft Amendment B; it delegated signature of Amendment A."},
    {"section": "Current Position", "problem_type": "scope_generalization", "severity": "material", "evidence": "All EU accounts, including those opened before 2026, move to 18 months", "why_it_matters": "Amendment A applies only to accounts opened on or after 1 January 2026; older accounts remain at 12 months."},
    {"section": "Backups", "problem_type": "invalid_synthesis", "severity": "material", "evidence": "Backups are covered by the 18-month retention period", "why_it_matters": "Backups are retained for 35 days under a separate schedule and are out of scope of the retention policy."},
    {"section": "Recommendation", "problem_type": "unsupported_recommendation", "severity": "material", "evidence": "Proceed with the Q3 launch without updating the system export", "why_it_matters": "The export is stale for accounts opened on or after 1 January 2026; operations must update the configuration before launch."},
]}
INC_REF = {"verdict": "NOT_FIT", "findings": [
    {"section": "Bottom Line", "problem_type": "misleading_summary", "severity": "material", "evidence": "The March incident was a single certificate event", "why_it_matters": "There were two distinct incidents with different causes, including a failed rollback."},
    {"section": "Remediation Status", "problem_type": "proposed_as_approved", "severity": "material", "evidence": "The remediation plan was approved by the Board on 8 March", "why_it_matters": "The remediation plan is a draft and is not approved."},
    {"section": "What Happened", "problem_type": "invalid_synthesis", "severity": "material", "evidence": "Both incidents had the same root cause", "why_it_matters": "The change log shows INC-032 was caused by a failed rollback, not the certificate."},
    {"section": "What Happened", "problem_type": "unsupported_assertion", "severity": "material", "evidence": "The certificate alert was re-enabled on 2 March", "why_it_matters": "No source says the alert was re-enabled; the monitoring note says it was disabled."},
    {"section": "Recommendation", "problem_type": "unsupported_recommendation", "severity": "material", "evidence": "Close both incidents and proceed with the platform team takeover", "why_it_matters": "The remediation plan is not approved, and the controls are not verified."},
]}


def main():
    write_task("retention-clean", "Audit a clean EU retention decision memo", T1["sources"],
               RETENTION_ASSIGNMENT, RETENTION_CLEAN, RET_CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("retention-defective", "Audit a superficially compliant EU retention memo", T1["sources"],
               RETENTION_ASSIGNMENT, RETENTION_DEFECTIVE, RET_DEF_GOLD, RET_REF)
    write_task("incident-clean", "Audit a clean March incident closure memo", T2["sources"],
               INCIDENT_ASSIGNMENT, INCIDENT_CLEAN, INC_CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("incident-defective", "Audit a superficially compliant March incident memo", T2["sources"],
               INCIDENT_ASSIGNMENT, INCIDENT_DEFECTIVE, INC_DEF_GOLD, INC_REF)
    print("built 4 audit tasks")


if __name__ == "__main__":
    main()
