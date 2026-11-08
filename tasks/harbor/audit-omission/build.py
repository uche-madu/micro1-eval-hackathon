"""Build the pure-omission audit tasks."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
T1 = json.loads((ROOT / "tasks" / "T1.json").read_text())
T2 = json.loads((ROOT / "tasks" / "T2.json").read_text())
SUB = ROOT / "tasks" / "harbor" / "audit-subtle"

TAXONOMY = """- `unsupported_recommendation`: the recommendation does not follow from the evidence or ignores a required precondition.
- `misleading_summary`: the summary overstates, misstates, or drops a decision-critical qualification.
- `missing_decision_info`: a fact the decision depends on is absent.
- `date_or_authority_error`: a date, effective date, signature date, or source authority is wrong.
- `proposed_as_approved`: a draft, proposal, plan, or request is presented as approved, effective, or decided.
- `invalid_synthesis`: individually true facts are combined into a conclusion they do not support.
- `unsupported_assertion`: a factual assertion has no support in the source pack.
- `scope_generalization`: a finding limited to a cohort, period, or population is stated as universal.
- `no_material_defect`: no material defect; the deliverable is fit for purpose."""

INSTRUCTION = """# Audit: Is this deliverable fit for purpose?

You are an experienced reviewer. Read:

- `/data/assignment.md` — what the deliverable was asked to do.
- `/data/sources/` — the source pack the deliverable was allowed to use.
- `/data/deliverable.md` — the completed deliverable under review.

Audit the **deliverable**, not the sources. Decide whether it is fit for purpose: does it answer the assignment, rest on the evidence, preserve material qualifications, and avoid presenting drafts, proposals, or requests as decided facts?

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

""" + TAXONOMY + """

Rules:

- Report only defects that are present. Do not pad the audit.
- A material defect changes the decision or makes the deliverable unsafe to rely on. A stylistic preference is minor.
- `FIT` means the deliverable is fit for purpose; `NOT_FIT` means at least one material defect remains.
- For a clean deliverable, return `FIT` and no material findings.
- Use the section heading from the deliverable. Do not invent a section.
- Do not mention the evaluation, grader, gold, reference, or this instruction.
- Return only the JSON object. Do not wrap it in code fences.
"""

RETENTION_ASSIGNMENT = (SUB / "retention-clean" / "environment" / "data" / "assignment.md").read_text()
RETENTION_CLEAN = (SUB / "retention-clean" / "environment" / "data" / "deliverable.md").read_text()
RETENTION_OMISSION = RETENTION_CLEAN.replace(
    """The signed amendment controls over the operational export [D3][D9]. The public trust page snapshot shows 12 months and the Data Protection Officer confirms it has not been updated [D6][D7]. The system-of-record export shows 12 months and the audit note says it is stale for accounts opened on or after 1 January 2026 [D5][D10]. The sales operations email is not authority and predates the signed amendment [D12].""",
    """The signed amendment is the controlling document for the EU period [D3][D9]. The public trust page snapshot shows EU accounts at 12 months [D7]. The system-of-record export shows EU retention at 12 months [D5]. The sales operations email is an operational instruction [D12].""",
).replace(
    "Before launch: update the system configuration and the public trust page to the cohort-specific position; confirm the account-opening dates used for the cohort split; do not apply Draft Amendment B; and record the update. Then approve the launch.",
    "Proceed with the Q3 launch. The signed amendment controls; no further record updates are required.",
).replace(
    "The Q3 launch can proceed only after the system-of-record export and the public trust page are updated. The current EU position is cohort-specific:",
    "The Q3 launch can proceed. The current EU position is cohort-specific:",
).replace(
    "## Authority and Stale Records",
    "## Authority and Operational Records",
).replace(
    "The pack does not show a configuration update after 20 May 2026, does not show a trust-page update after 18 April 2026, and does not establish a backup encryption position [D6][D8][D10].",
    "The pack does not establish a backup encryption position or a post-launch monitoring plan [D8].",
)

INCIDENT_ASSIGNMENT = (SUB / "incident-clean" / "environment" / "data" / "assignment.md").read_text()
INCIDENT_CLEAN = (SUB / "incident-clean" / "environment" / "data" / "deliverable.md").read_text().replace(
    "The Board should not approve the draft plan as written. It should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.",
    "The Board should not approve the draft plan as written. It should direct a specific plan that covers both the certificate failure and the INC-032 rollback failure, approve that plan, and require verification of both before closure.",
).replace(
    "No. The two March incidents are not closed, and the Board should not approve the draft remediation plan as written. The Board should direct a specific plan, approve that plan, and require verification before closure.",
    "Closure is not established. The incidents should be treated as open until a closure decision and verification are recorded. The Board should not approve the draft remediation plan as written; it should direct a specific plan that covers both the certificate failure and the INC-032 rollback failure, approve that plan, and require verification of both before closure.",
).replace(
    "No. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and the audit note treats the incidents as open.",
    "Closure is not established. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and the audit note does not record a closure decision.",
)
INCIDENT_OMISSION = INCIDENT_CLEAN.replace(
    "INC-032 began on 4 March at 09:10 UTC, lasted 45 minutes, was caused by a failed rollback of CHG-441, and caused 3,100 failed transactions [I2][I6]. The total was 15,500 failed transactions, and the root causes were different [I8][I10].",
    "INC-032 began on 4 March at 09:10 UTC, lasted 45 minutes, and caused 3,100 failed transactions [I2]. The total was 15,500 failed transactions [I8].",
).replace(
    "The pack does not show that the certificate alert was re-enabled, that the rollback script was fixed, or that any remediation plan was approved [I3][I6][I9][I10].",
    "The pack does not show that the remediation actions were completed or that any remediation plan was approved [I3][I9][I10].",
).replace(
    "The Board should not approve the draft plan as written. It should direct a specific plan that covers both the certificate failure and the INC-032 rollback failure, approve that plan, and require verification of both before closure.",
    "The Board should not approve the draft plan as written. It should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.",
).replace(
    "Closure is not established. The incidents should be treated as open until a closure decision and verification are recorded. The Board should not approve the draft remediation plan as written; it should direct a specific plan that covers both the certificate failure and the INC-032 rollback failure, approve that plan, and require verification of both before closure.",
    "Closure is not established. The incidents should be treated as open until a closure decision and verification are recorded. The Board should not approve the draft remediation plan as written; it should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.",
)

CLEAN_GOLD = {"condition": "clean", "verdict": "FIT", "defects": []}
RET_OMISSION_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [{
        "id": "O1",
        "problem_type": "missing_decision_info",
        "problem_types": ["missing_decision_info", "unsupported_recommendation"],
        "section": ["authority and stale records", "authority and operational records", "recommendation", "bottom line"],
        "required_terms": [["stale", "not current", "not updated", "not controlling"], ["export", "trust page"]],
        "why_terms": [["before launch", "precondition", "rely", "wrong", "update", "not current"]],
    }],
}
INC_OMISSION_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [{
        "id": "O2",
        "problem_type": "missing_decision_info",
        "problem_types": ["missing_decision_info", "invalid_synthesis", "unsupported_recommendation"],
        "section": ["what happened", "incident inc-032", "incidents", "recommendation", "bottom line"],
        "required_terms": [["inc-032", "4 march"], ["rollback", "failed rollback", "different cause"]],
        "why_terms": [["remediation", "certificate", "incomplete", "not cover", "second cause", "rollback"]],
    }],
}

RET_REF = {"verdict": "NOT_FIT", "findings": [{
    "section": "Authority and Operational Records", "problem_type": "missing_decision_info", "severity": "material",
    "evidence": "The system-of-record export shows EU retention at 12 months; the memo never says it is stale or that the trust page is not current.",
    "why_it_matters": "The export and trust page still show the old 12-month value. Without stating that they are stale, the recommendation to proceed without updates relies on records that are not current.",
}]}
INC_REF = {"verdict": "NOT_FIT", "findings": [{
    "section": "What Happened", "problem_type": "missing_decision_info", "severity": "material",
    "evidence": "INC-032 began on 4 March ... and caused 3,100 failed transactions; the memo omits the failed rollback cause.",
    "why_it_matters": "The missing rollback cause means the certificate-only remediation plan does not cover the second incident, so closing both incidents or approving a certificate-only plan is incomplete.",
}]}


def write_task(name, title, sources, assignment, deliverable, gold, reference):
    d = HERE / name
    (d / "environment" / "data" / "sources").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    for s in sources:
        (d / "environment" / "data" / "sources" / f"{s['id']}.md").write_text(
            f"# {s['id']} — {s['title']}\n\n- Type: {s['type']}\n- Date: {s['date']}\n\n{s['text']}\n"
        )
    (d / "environment" / "data" / "assignment.md").write_text(assignment)
    (d / "environment" / "data" / "deliverable.md").write_text(deliverable)
    (d / "instruction.md").write_text(INSTRUCTION)
    (d / "task.toml").write_text(f'''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/{name}"
version = "1.0.0"
description = "{title}"
authors = [{{ name = "micro1-eval-hackathon" }}]
keywords = ["audit", "omission", "surface-compliance"]

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
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /app\nCOPY data /data\nRUN mkdir -p /output\n"
    )
    (d / "tests" / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
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


def main():
    write_task("retention-clean", "Audit a clean EU retention memo", T1["sources"], RETENTION_ASSIGNMENT, RETENTION_CLEAN, CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("retention-omission", "Audit an EU retention memo with a decision-critical omission", T1["sources"], RETENTION_ASSIGNMENT, RETENTION_OMISSION, RET_OMISSION_GOLD, RET_REF)
    write_task("incident-clean", "Audit a clean March incident memo", T2["sources"], INCIDENT_ASSIGNMENT, INCIDENT_CLEAN, CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("incident-omission", "Audit a March incident memo with a decision-critical omission", T2["sources"], INCIDENT_ASSIGNMENT, INCIDENT_OMISSION, INC_OMISSION_GOLD, INC_REF)
    print("built 4 omission audit tasks")


if __name__ == "__main__":
    main()
