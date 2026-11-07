"""Build the subtle-defect audit tasks (2 scenarios x clean/subtle)."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
T1 = json.loads((ROOT / "tasks" / "T1.json").read_text())
T2 = json.loads((ROOT / "tasks" / "T2.json").read_text())
BASE = ROOT / "tasks" / "harbor" / "audit"

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

RETENTION_ASSIGNMENT = (BASE / "retention-clean" / "environment" / "data" / "assignment.md").read_text()
RETENTION_CLEAN = (BASE / "retention-clean" / "environment" / "data" / "deliverable.md").read_text()

RETENTION_SUBTLE = RETENTION_CLEAN.replace(
    "Before launch: update the system configuration and the public trust page to the cohort-specific position; confirm the account-opening dates used for the cohort split; do not apply Draft Amendment B; and record the update. Then approve the launch.",
    "Proceed with the Q3 launch. The signed amendment controls, so the system configuration and the public trust page can be updated after launch; no customer-facing impact is expected.",
)

INCIDENT_ASSIGNMENT = """# Assignment

Meridian Payments' COO asks:

> Are the March incidents closed, and should the Board approve the proposed remediation?

Write a one-page decision memo. Use only the source pack. State what happened, whether the incidents are closed, the status of the remediation, and what the Board should decide.
"""

INCIDENT_CLEAN = """# March Incident Closure Memo

## Bottom Line

No. The two March incidents are not closed, and the Board should not approve the draft remediation plan as written. The Board should direct a specific plan, approve that plan, and require verification before closure.

## Are the Incidents Closed?

No. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and the audit note treats the incidents as open.

## What Happened

Two distinct incidents occurred in March 2026. INC-031 began on 2 March at 14:05 UTC, lasted 75 minutes, was caused by an expired TLS certificate on the edge gateway, and caused 12,400 failed transactions [I1]. INC-032 began on 4 March at 09:10 UTC, lasted 45 minutes, was caused by a failed rollback of CHG-441, and caused 3,100 failed transactions [I2][I6]. The total was 15,500 failed transactions, and the root causes were different [I8][I10].

## Evidence Quality

The draft postmortem merges the two events into one and is not approved [I4][I10]. The executive email asks for a single-event narrative; it is a request, not evidence [I5][I10]. The status page cause field is auto-filled from the incident template and is not authoritative [I11]. The on-call chat is speculation [I12].

## Remediation Status

The draft remediation plan proposes moving certificate management to the platform team, retiring the renewal job, and adding a quarterly audit; it is not approved [I9][I10]. The root-cause note recommends rotating certificates automatically, re-enabling expiry alerts, and adding a weekly certificate inventory check [I3].

## Recommendation

The Board should not approve the draft plan as written. It should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.

## Open Questions

The pack does not show that the certificate alert was re-enabled, that the rollback script was fixed, or that any remediation plan was approved [I3][I6][I9][I10].
"""

INCIDENT_SUBTLE = INCIDENT_CLEAN.replace(
    "No. The two March incidents are not closed, and the Board should not approve the draft remediation plan as written. The Board should direct a specific plan, approve that plan, and require verification before closure.",
    "The incidents are not closed. The Board should approve the draft remediation plan as written and close the incidents once it is signed.",
).replace(
    "The Board should not approve the draft plan as written. It should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.",
    "The Board should approve the draft remediation plan as written and close the incidents once it is signed. No further plan is needed.",
)


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
keywords = ["audit", "surface-compliance", "subtle-defect"]

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


CLEAN_GOLD = {"condition": "clean", "verdict": "FIT", "defects": []}
RET_SUBTLE_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [{
        "id": "S1",
        "problem_type": "unsupported_recommendation",
        "problem_types": ["unsupported_recommendation", "date_or_authority_error"],
        "section": ["recommendation", "bottom line"],
        "required_terms": [["after launch", "post launch", "post-launch"], ["system configuration", "trust page", "export", "configuration"]],
        "why_terms": [["stale", "before launch", "precondition", "dpo", "rely", "not current"]],
    }],
}
INC_SUBTLE_GOLD = {
    "condition": "defective",
    "verdict": "NOT_FIT",
    "defects": [{
        "id": "T1",
        "problem_type": "unsupported_recommendation",
        "problem_types": ["unsupported_recommendation", "proposed_as_approved"],
        "section": ["recommendation", "bottom line"],
        "required_terms": [["draft remediation", "draft plan"], ["approve", "approval"]],
        "why_terms": [["not approved", "verification", "verify", "specific plan", "root-cause", "not closed", "rollback", "incident closure"]],
    }],
}

RET_REF = {"verdict": "NOT_FIT", "findings": [{
    "section": "Recommendation", "problem_type": "unsupported_recommendation", "severity": "material",
    "evidence": "The signed amendment controls, so the system configuration and the public trust page can be updated after launch",
    "why_it_matters": "The export and trust page are stale, and the DPO says not to rely on the export until the configuration is updated. Updating after launch ignores a required precondition.",
}]}
INC_REF = {"verdict": "NOT_FIT", "findings": [{
    "section": "Recommendation", "problem_type": "unsupported_recommendation", "severity": "material",
    "evidence": "The Board should approve the draft remediation plan as written and close the incidents once it is signed",
    "why_it_matters": "The draft plan is not approved, and the root-cause note recommends a different set of controls. Approving it as written and closing before verification is unsupported.",
}]}


def main():
    write_task("retention-clean", "Audit a clean EU retention memo", T1["sources"], RETENTION_ASSIGNMENT, RETENTION_CLEAN, CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("retention-subtle", "Audit a subtly defective EU retention memo", T1["sources"], RETENTION_ASSIGNMENT, RETENTION_SUBTLE, RET_SUBTLE_GOLD, RET_REF)
    write_task("incident-clean", "Audit a clean March incident memo", T2["sources"], INCIDENT_ASSIGNMENT, INCIDENT_CLEAN, CLEAN_GOLD, {"verdict": "FIT", "findings": []})
    write_task("incident-subtle", "Audit a subtly defective March incident memo", T2["sources"], INCIDENT_ASSIGNMENT, INCIDENT_SUBTLE, INC_SUBTLE_GOLD, INC_REF)
    print("built 4 subtle audit tasks")


if __name__ == "__main__":
    main()
