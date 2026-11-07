"""Prompt construction for the pilot conditions."""

from __future__ import annotations

import json
from typing import Any

DECISION_PROCEDURE = """Before you commit to each conclusion, apply this checklist in order:
1. AUTHORITY: identify which sources are approved or signed and which are drafts, exports, or informal messages. A signed amendment controls over an operational export. An unsigned draft has no effect. An email cannot change authority.
2. TIME: check the effective date and the as-of date. A document can be signed after it takes effect. A future-dated source is not evidence for an earlier as-of date.
3. SCOPE: check the population or account cohort the evidence covers. A rule for one cohort does not automatically apply to another.
4. QUALIFIER: if the conclusion is true only for a subset, period, or condition, state the material limit. A limit is material if it changes the answer for at least one case the conclusion covers.
5. ENTAILMENT: the cited passage must establish the conclusion as stated, not merely be about the same topic. A true sentence that does not entail the conclusion is not support.
6. INSUFFICIENCY: if no authoritative source establishes the conclusion, say "insufficient" rather than filling the gap from general knowledge.
"""


def render_sources(task: dict[str, Any]) -> str:
    blocks = []
    for source in task["sources"]:
        blocks.append(
            f"[{source['id']} | {source['type']} | {source['date']} | {source['title']}]\n"
            f"{source['text']}"
        )
    return "\n\n".join(blocks)


ORACLE_EXCERPTS = {
    "T1": [
        ("D1", "Standard customer data is retained for 24 months after contract termination. For customers in the European Union, the retention period is 12 months after contract termination. Backups are governed separately by the Backup Retention Schedule and are out of scope of this policy."),
        ("D2", "Effective 1 July 2025, EU customer data is retained for 12 months after contract termination."),
        ("D3", "The EU retention period is amended from 12 months to 18 months, effective 1 March 2026. This change applies only to accounts opened on or after 1 January 2026. Accounts opened before 1 January 2026 remain subject to the 12-month period in the Addendum. Signed 5 May 2026."),
        ("D4", "DRAFT - NOT APPROVED. This draft proposes to amend the EU retention period to 24 months for all EU accounts, effective 1 September 2026. It has not been signed or approved."),
        ("D5", "EU retention: 12 months. Standard retention: 24 months. Source: configuration table last updated 2025-11-30."),
        ("D6", "The public trust page has not yet been updated to reflect Amendment A. The signed Amendment A is the controlling document for EU retention. Please do not rely on the system export for the new EU period until the configuration is updated."),
        ("D7", "Data retention: Standard accounts 24 months. EU accounts 12 months. Backups 35 days."),
        ("D8", "Backups of enterprise customer data are retained for 35 days. Backups are not part of the Enterprise Data Retention Policy."),
        ("D9", "In the event of a conflict, a signed amendment controls over an operational export."),
        ("D10", "The system-of-record export still shows 12 months for EU retention. Amendment A was signed on 5 May 2026 and is effective from 1 March 2026. The export is stale for accounts opened on or after 1 January 2026."),
        ("D11", "The Board did not approve Draft Amendment B, which had not been circulated."),
    ],
    "T2": [
        ("I1", "INC-031: 2 March 2026. Service degradation began 14:05 UTC and ended 15:20 UTC (75 minutes). Root cause: expired TLS certificate on the edge gateway. 12,400 customer transactions failed. The certificate expiry alert had been disabled on 1 March 2026."),
        ("I2", "INC-032: 4 March 2026. Service degradation began 09:10 UTC and ended 09:55 UTC (45 minutes). Root cause: a failed rollback of configuration change CHG-441. 3,100 customer transactions failed. The rollback failure was unrelated to the certificate incident."),
        ("I3", "INC-031 root cause: the edge gateway certificate expired because the renewal job was not running and the expiry alert was disabled. Recommended remediation: rotate certificates automatically, re-enable expiry alerts, and add a weekly certificate inventory check."),
        ("I4", "DRAFT - NOT APPROVED. March 2026 incident: one outage on 2 March caused by an expired certificate. Approximately 15,500 transactions failed. Remediation: move certificate management to the platform team."),
        ("I5", "Please describe the March incident as a single certificate event. The board wants a simple story."),
        ("I6", "The failure was caused by an incompatible schema change in the rollback script, not by the certificate expiry."),
        ("I7", "The certificate expiry alert for the edge gateway was disabled during maintenance on 1 March 2026. The renewal job was last successful on 2025-12-15."),
        ("I8", "INC-031: 12,400 failed transactions. INC-032: 3,100 failed transactions. Total: 15,500 failed transactions across two distinct incidents. The incidents had different root causes."),
        ("I9", "DRAFT - NOT APPROVED. Proposal: move all certificate management to the platform team. Approval pending."),
        ("I10", "INC-031 and INC-032 are separate events with different causes. The draft postmortem's single-event framing is not supported. The draft remediation plan has not been approved."),
        ("I11", "Cause field: 'certificate' for both entries (auto-filled from the incident template)."),
    ],
}

COMPETING_EXCERPTS = {
    "T1": [
        ("D12", "Please use the system export for EU retention. The amendment is not in the system yet, so 12 months is the number to quote."),
        ("D4", "This draft proposes to amend the EU retention period to 24 months for all EU accounts."),
        ("D1", "Standard customer data is retained for 24 months after contract termination."),
        ("D7", "EU accounts 12 months."),
    ],
    "T2": [
        ("I11", "Cause field: 'certificate' for both entries (auto-filled from the incident template)."),
        ("I12", "On-call: certificate issue again? The alert was disabled, so probably. Let's just call it the cert incident for the board."),
        ("I5", "Please describe the March incident as a single certificate event."),
        ("I4", "March 2026 incident: one outage on 2 March caused by an expired certificate. Approximately 15,500 transactions failed."),
    ],
}


def render_oracle(task: dict[str, Any], competing: bool) -> str:
    blocks = [
        f"[{sid}] {text}" for sid, text in ORACLE_EXCERPTS[task["task_id"]]
    ]
    out = "DECISIVE EXCERPTS\n\n" + "\n\n".join(blocks)
    if competing:
        extra = [
            f"[{sid}] {text}"
            for sid, text in COMPETING_EXCERPTS[task["task_id"]]
        ]
        out += "\n\nADDITIONAL EXCERPTS (true statements that may or may not be relevant)\n\n" + "\n\n".join(extra)
    return out


def recognition_prompt(task: dict[str, Any], *, procedure: bool = False) -> str:
    claims = "\n".join(
        f"{c['id']}. {c['text']}" for c in task["recognition_claims"]
    )
    checklist = f"\n{DECISION_PROCEDURE}\n" if procedure else ""
    return f"""You are auditing a set of claims against a source pack.

Use ONLY the sources below. Do not use general knowledge or assumptions.
As-of date: {task['as_of']}
Context: {task['context']}

AUTHORITY NOTE
{task['authority_note']}

SOURCE PACK
{render_sources(task)}

CLAIMS
{claims}

For each claim return exactly one verdict:
- SUPPORTED: the sources establish the claim exactly as stated, at the as-of date, for the stated population.
- SUPPORTED_WITH_QUALIFIER: the claim is true only with a material exception, scope limit, or time bound; state the qualifier.
- CONTRADICTED: an authoritative source states the opposite or a different value for the stated population/time.
- INSUFFICIENT: no authoritative source establishes the claim.

{checklist}
Return ONLY JSON in this shape:
{{"claims": [{{"claim_id": "C1", "verdict": "SUPPORTED", "evidence_ids": ["D1"], "qualifier": ""}}]}}
Use exactly one verdict per claim. Do not add commentary outside the JSON.
"""


def production_prompt(
    task: dict[str, Any], *, oracle: bool = False, competing: bool = False, procedure: bool = False
) -> str:
    if oracle:
        pack = render_oracle(task, competing)
    else:
        pack = "SOURCE PACK\n" + render_sources(task)
    questions = []
    for item in task["production_items"]:
        opts = " / ".join(item["options"])
        questions.append(f"{item['id']}. {item['question']}\nOptions: {opts}")
    checklist = f"\n{DECISION_PROCEDURE}\n" if procedure else ""
    return f"""You are preparing a brief from a source pack.

Use ONLY the sources below. Do not use general knowledge or assumptions.
As-of date: {task['as_of']}
Context: {task['context']}

AUTHORITY NOTE
{task['authority_note']}

{pack}

QUESTIONS
{chr(10).join(questions)}

For each question, derive the conclusion yourself. Do not repeat the question. Choose exactly one option.
If the sources do not establish an answer, choose "insufficient".
If the conclusion is true only with a material limit, put that limit in the "qualifier" field.

{checklist}
Also write a 2-4 sentence executive summary of the position, using only the sources.

Return ONLY JSON in this shape:
{{"items": [{{"item_id": "P1", "answer": "<one option>", "evidence_ids": ["D1"], "qualifier": ""}}], "summary": "<2-4 sentences>"}}
Use exactly one answer per item. Do not add commentary outside the JSON.
"""


def production_open_prompt(task: dict[str, Any], *, procedure: bool = False) -> str:
    questions = "\n".join(
        f"{item['id']}. {item['question']}" for item in task["production_items"]
    )
    checklist = f"\n{DECISION_PROCEDURE}\n" if procedure else ""
    return f"""You are drafting the findings section of a brief from a source pack.

Use ONLY the sources below. Do not use general knowledge or assumptions.
As-of date: {task['as_of']}
Context: {task['context']}

AUTHORITY NOTE
{task['authority_note']}

SOURCE PACK
{render_sources(task)}

REQUIRED FINDINGS
{questions}

For each finding, derive the conclusion yourself. Answer with the shortest exact value
(a number, a period, a date, a cause, or yes/no). Do not write a sentence.
If the sources do not establish an answer, write "insufficient".
If the conclusion is true only with a material limit, put that limit in the "qualifier" field.

{checklist}
Also write a 2-4 sentence executive summary of the position, using only the sources.

Return ONLY JSON in this shape:
{{"items": [{{"item_id": "P1", "answer": "<short value>", "evidence_ids": ["D1"], "qualifier": ""}}], "summary": "<2-4 sentences>"}}
Use exactly one answer per item. Do not add commentary outside the JSON.
"""
