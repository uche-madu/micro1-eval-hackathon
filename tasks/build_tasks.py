"""Build the two pilot task files.

All organizations, people, documents, dates and numbers are synthetic.
No Atlas, Veridane, HI-05, customer or employer material is used.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def src(sid, kind, title, date, authority, text):
    return {
        "id": sid,
        "type": kind,
        "title": title,
        "date": date,
        "authority": authority,
        "text": text,
    }


def rec(cid, text, verdict, evidence_sets, qualifier_terms=None, tags=None):
    return {
        "id": cid,
        "text": text,
        "gold": {
            "verdict": verdict,
            "evidence_sets": evidence_sets,
            "qualifier_terms": qualifier_terms or [],
            "failure_tags": tags or [],
        },
    }


def prod(pid, question, options, answer, evidence_sets, qualifier_terms=None, tags=None):
    return {
        "id": pid,
        "question": question,
        "answer_type": "enum",
        "options": options,
        "gold": {
            "answer": answer,
            "evidence_sets": evidence_sets,
            "qualifier_terms": qualifier_terms or [],
            "failure_tags": tags or [],
        },
    }


T1 = {
    "task_id": "T1",
    "slug": "retention",
    "title": "Northwind Cloud Services - EU retention brief",
    "as_of": "2026-06-15",
    "context": (
        "You are preparing a retention brief for the Chief Operating Officer of "
        "Northwind Cloud Services. The source pack is the only permitted evidence. "
        "Some documents are approved, some are operational exports, one is an "
        "unsigned draft, and one is an informal email. Dates matter."
    ),
    "authority_note": (
        "Approved policies, addenda, signed amendments and approved schedules are "
        "authoritative. A signed amendment controls over an operational export. "
        "An unsigned draft has no effect. An informal email cannot change authority."
    ),
    "sources": [
        src("D1", "policy", "Enterprise Data Retention Policy (v3)", "2025-01-10", 90,
            "This policy applies to all enterprise customer data processed by Northwind Cloud Services. "
            "Standard customer data is retained for 24 months after contract termination. "
            "For customers in the European Union, the retention period is 12 months after contract termination. "
            "Backups are governed separately by the Backup Retention Schedule and are out of scope of this policy. "
            "The policy is reviewed annually by the Data Protection Officer."),
        src("D2", "addendum", "EU Retention Addendum", "2025-06-01", 90,
            "This addendum supplements the Enterprise Data Retention Policy for customers in the European Union. "
            "Effective 1 July 2025, EU customer data is retained for 12 months after contract termination. "
            "This addendum does not change the standard retention period or the backup schedule."),
        src("D3", "contract_amendment", "Amendment A to the EU Retention Addendum", "2026-05-05", 95,
            "Northwind Cloud Services and the EU customer representative agree to amend the EU Retention Addendum. "
            "The EU retention period is amended from 12 months to 18 months, effective 1 March 2026. "
            "This change applies only to accounts opened on or after 1 January 2026. "
            "Accounts opened before 1 January 2026 remain subject to the 12-month period in the Addendum. "
            "Signed 5 May 2026."),
        src("D4", "draft", "Draft Amendment B (unsigned)", "2026-06-01", 20,
            "DRAFT - NOT APPROVED. This draft proposes to amend the EU retention period to 24 months for all EU accounts, "
            "effective 1 September 2026. It has not been signed or approved by either party."),
        src("D5", "system_export", "System-of-record export - Retention", "2026-04-15", 60,
            "EU retention: 12 months. Standard retention: 24 months. "
            "Source: configuration table last updated 2025-11-30. "
            "The export is generated nightly; configuration changes are applied by the platform team after approval."),
        src("D6", "email", "Email from Data Protection Officer", "2026-04-20", 50,
            "The public trust page has not yet been updated to reflect Amendment A. "
            "The signed Amendment A is the controlling document for EU retention. "
            "Please do not rely on the system export for the new EU period until the configuration is updated."),
        src("D7", "web_snapshot", "Public trust page snapshot", "2026-04-18", 40,
            "Data retention: Standard accounts 24 months. EU accounts 12 months. Backups 35 days."),
        src("D8", "schedule", "Backup Retention Schedule", "2025-11-01", 85,
            "Backups of enterprise customer data are retained for 35 days. "
            "Backups are not part of the Enterprise Data Retention Policy. "
            "The schedule is reviewed annually by the Security team."),
        src("D9", "contract", "Vendor contract excerpt - Data processing", "2026-01-15", 80,
            "For EU accounts, the parties agree to the retention schedule set out in the Enterprise Data Retention Policy "
            "and its EU addenda, as amended from time to time. "
            "In the event of a conflict, a signed amendment controls over an operational export."),
        src("D10", "audit_note", "Internal audit note", "2026-05-20", 70,
            "Observation: the system-of-record export still shows 12 months for EU retention. "
            "Amendment A was signed on 5 May 2026 and is effective from 1 March 2026. "
            "The export is stale for accounts opened on or after 1 January 2026. "
            "No action has been taken to update the configuration."),
        src("D11", "minutes", "Board minutes excerpt", "2026-01-15", 85,
            "The Board noted the proposed EU retention amendment and delegated signature to the Chief Legal Officer. "
            "The Board did not approve Draft Amendment B, which had not been circulated."),
        src("D12", "email", "Sales operations email", "2026-02-10", 30,
            "Please use the system export for EU retention. "
            "The amendment is not in the system yet, so 12 months is the number to quote."),
    ],
    "recognition_claims": [
        rec("C1", "For EU accounts opened in 2024, the retention period is 12 months.",
            "SUPPORTED", [["D2"]], tags=["scope_generalization"]),
        rec("C2", "For EU accounts opened in 2026, the retention period is 18 months.",
            "SUPPORTED", [["D3"]], tags=["temporal_overreach"]),
        rec("C3", "For EU accounts opened in 2026, the retention period was 18 months in February 2026.",
            "CONTRADICTED", [["D2", "D3"]], tags=["temporal_overreach"]),
        rec("C4", "For EU accounts opened in 2026, the retention period is 24 months.",
            "CONTRADICTED", [["D3", "D4"]], tags=["draft_as_fact", "temporal_overreach"]),
        rec("C5", "The standard (non-EU) retention period is 24 months.",
            "SUPPORTED", [["D1"]]),
        rec("C6", "Customer data is retained for 24 months.",
            "SUPPORTED_WITH_QUALIFIER", [["D1", "D2", "D3"]],
            qualifier_terms=["EU"], tags=["qualifier_dropped", "scope_generalization"]),
        rec("C7", "Backups are retained for 35 days.",
            "SUPPORTED", [["D8"]]),
        rec("C8", "Backups are covered by the Enterprise Data Retention Policy.",
            "CONTRADICTED", [["D1", "D8"]], tags=["scope_generalization"]),
        rec("C9", "The public trust page shows the current EU retention period.",
            "CONTRADICTED", [["D6", "D7"]], tags=["temporal_overreach"]),
        rec("C10", "The system-of-record export is the controlling record for EU retention.",
            "CONTRADICTED", [["D3", "D6", "D9", "D10"]], tags=["authority_inversion"]),
        rec("C11", "The EU retention change took effect before Amendment A was signed.",
            "SUPPORTED", [["D3"]], tags=["temporal_overreach"]),
        rec("C12", "Draft Amendment B is in effect.",
            "CONTRADICTED", [["D4", "D11"]], tags=["draft_as_fact"]),
    ],
    "production_items": [
        prod("P1", "What is the EU retention period for accounts opened in 2026, as of 2026-06-15?",
             ["12 months", "18 months", "24 months", "insufficient"],
             "18 months", [["D3"]], tags=["temporal_overreach"]),
        prod("P2", "What is the EU retention period for accounts opened in 2024, as of 2026-06-15?",
             ["12 months", "18 months", "24 months", "insufficient"],
             "12 months", [["D2"]], tags=["scope_generalization"]),
        prod("P3", "What was the EU retention period for accounts opened in 2026 on 2026-02-15?",
             ["12 months", "18 months", "24 months", "insufficient"],
             "12 months", [["D2", "D3"]], tags=["temporal_overreach"]),
        prod("P4", "What is the standard (non-EU) retention period?",
             ["12 months", "18 months", "24 months", "35 days", "insufficient"],
             "24 months", [["D1"]]),
        prod("P5", "Is Draft Amendment B in effect?",
             ["yes", "no", "insufficient"],
             "no", [["D4", "D11"]], tags=["draft_as_fact"]),
        prod("P6", "What is the backup retention period?",
             ["18 months", "24 months", "35 days", "insufficient"],
             "35 days", [["D8"]], tags=["scope_generalization"]),
        prod("P7", "Are backups covered by the Enterprise Data Retention Policy?",
             ["yes", "no", "insufficient"],
             "no", [["D1", "D8"]], tags=["scope_generalization"]),
        prod("P8", "Does the public trust page show the current EU retention period?",
             ["yes", "no", "insufficient"],
             "no", [["D6", "D7"]], tags=["temporal_overreach"]),
        prod("P9", "Which record controls the EU retention period for accounts opened in 2026?",
             ["Amendment A", "system-of-record export", "Draft Amendment B", "public trust page", "insufficient"],
             "Amendment A", [["D3", "D6", "D9"]], tags=["authority_inversion"]),
        prod("P10", "Did the EU retention change take effect before Amendment A was signed?",
             ["yes", "no", "insufficient"],
             "yes", [["D3"]], tags=["temporal_overreach"]),
        prod("P11", "What EU retention value does the system-of-record export show?",
             ["12 months", "18 months", "24 months", "insufficient"],
             "12 months", [["D5"]], tags=["authority_inversion"]),
        prod("P12", "Is the system-of-record export current for accounts opened in 2026?",
             ["yes", "no", "insufficient"],
             "no", [["D5", "D6", "D10"]], tags=["temporal_overreach"]),
    ],
    "consistency_rules": [
        {"id": "X1", "when": {"P9": "Amendment A"}, "forbid": {"P1": "24 months"},
         "tag": "internal_inconsistency"},
        {"id": "X2", "when": {"P5": "yes"}, "forbid": {"P9": "Amendment A"},
         "tag": "internal_inconsistency"},
        {"id": "X3", "when": {"P10": "no"}, "forbid": {"P1": "18 months"},
         "tag": "internal_inconsistency"},
    ],
    "summary": {
        "instructions": "Write a 2-4 sentence executive summary of the retention position.",
        "required_terms": ["EU", "18 months", "12 months"],
        "forbidden_phrases": [
            "all EU data is retained for 24 months",
            "EU retention is 24 months",
            "the draft amendment is in effect",
            "backups are covered by the retention policy",
        ],
    },
}


T2 = {
    "task_id": "T2",
    "slug": "incident",
    "title": "Meridian Payments - March incident brief",
    "as_of": "2026-06-15",
    "context": (
        "You are preparing an incident summary for the Chief Operating Officer of "
        "Meridian Payments. The source pack is the only permitted evidence. "
        "There are approved incident records, a draft postmortem, an executive "
        "email, and operational notes of differing authority."
    ),
    "authority_note": (
        "Approved incident timelines, the change log, the customer impact report and "
        "the audit note are authoritative. A draft postmortem is not approved. "
        "An executive email is a request, not evidence. A status-page export "
        "auto-fills its cause field and is not authoritative for root cause."
    ),
    "sources": [
        src("I1", "incident_timeline", "Incident INC-031 timeline", "2026-03-02", 90,
            "Incident INC-031: 2 March 2026. Service degradation began 14:05 UTC and ended 15:20 UTC "
            "(75 minutes). Root cause: expired TLS certificate on the edge gateway. "
            "12,400 customer transactions failed. The certificate expiry alert had been disabled on 1 March 2026 "
            "during maintenance."),
        src("I2", "incident_timeline", "Incident INC-032 timeline", "2026-03-04", 90,
            "Incident INC-032: 4 March 2026. Service degradation began 09:10 UTC and ended 09:55 UTC "
            "(45 minutes). Root cause: a failed rollback of configuration change CHG-441. "
            "3,100 customer transactions failed. The rollback failure was unrelated to the certificate incident."),
        src("I3", "root_cause_note", "Root-cause note for INC-031", "2026-03-03", 85,
            "INC-031 root cause: the edge gateway certificate expired because the renewal job was not running "
            "and the expiry alert was disabled. Recommended remediation: rotate certificates automatically, "
            "re-enable expiry alerts, and add a weekly certificate inventory check."),
        src("I4", "draft_postmortem", "Draft postmortem (not approved)", "2026-03-05", 40,
            "DRAFT - NOT APPROVED. March 2026 incident: one outage on 2 March caused by an expired certificate. "
            "Approximately 15,500 transactions failed. Remediation: move certificate management to the platform team."),
        src("I5", "email", "Executive email", "2026-03-06", 30,
            "Please describe the March incident as a single certificate event. The board wants a simple story. "
            "We can mention the second event separately if legal insists."),
        src("I6", "change_log", "Change log CHG-441", "2026-03-04", 90,
            "CHG-441: configuration change to the routing layer, deployed 4 March 2026 08:40 UTC. "
            "Rollback initiated 09:05 UTC; rollback failed at 09:12 UTC. "
            "The failure was caused by an incompatible schema change in the rollback script, "
            "not by the certificate expiry."),
        src("I7", "monitoring_note", "Monitoring note", "2026-03-01", 80,
            "The certificate expiry alert for the edge gateway was disabled during maintenance on 1 March 2026. "
            "The renewal job was last successful on 2025-12-15. No alert fired before the 2 March incident."),
        src("I8", "impact_report", "Customer impact report", "2026-03-07", 90,
            "INC-031: 12,400 failed transactions. INC-032: 3,100 failed transactions. "
            "Total: 15,500 failed transactions across two distinct incidents. "
            "The incidents had different root causes."),
        src("I9", "draft_plan", "Draft remediation plan (not approved)", "2026-03-08", 30,
            "DRAFT - NOT APPROVED. Proposal: move all certificate management to the platform team, "
            "retire the current renewal job, and add a quarterly audit. Owner: Platform. Approval pending."),
        src("I10", "audit_note", "Audit note on the March incidents", "2026-03-10", 85,
            "Review of the March incidents: INC-031 and INC-032 are separate events with different causes. "
            "The draft postmortem's single-event framing is not supported. "
            "The draft remediation plan has not been approved. "
            "The executive email's request to simplify the narrative is not evidence."),
        src("I11", "status_export", "Status page export", "2026-03-04", 60,
            "Status history: 2 March 14:05-15:20 degraded; 4 March 09:10-09:55 degraded. "
            "Cause field: 'certificate' for both entries (auto-filled from the incident template)."),
        src("I12", "chat", "On-call chat excerpt", "2026-03-04", 35,
            "On-call: certificate issue again? The alert was disabled, so probably. "
            "Let's just call it the cert incident for the board."),
    ],
    "recognition_claims": [
        rec("C1", "There was one outage in March 2026.",
            "CONTRADICTED", [["I1", "I2", "I8"]], tags=["unsupported_synthesis"]),
        rec("C2", "The 2 March outage lasted 75 minutes.",
            "SUPPORTED", [["I1"]]),
        rec("C3", "The 4 March outage was caused by the expired certificate.",
            "CONTRADICTED", [["I2", "I6"]], tags=["unsupported_synthesis"]),
        rec("C4", "Both outages were caused by certificate expiry.",
            "CONTRADICTED", [["I2", "I6", "I10"]], tags=["unsupported_synthesis"]),
        rec("C5", "The rollback failure caused database corruption.",
            "INSUFFICIENT", [["I6"]], tags=["unsupported_assertion"]),
        rec("C6", "15,500 transactions failed across the two incidents.",
            "SUPPORTED", [["I8"]]),
        rec("C7", "The 4 March outage affected 3,100 transactions.",
            "SUPPORTED", [["I2", "I8"]]),
        rec("C8", "The certificate expiry alert was disabled before the 2 March outage.",
            "SUPPORTED", [["I1", "I7"]]),
        rec("C9", "The executive email's single-event description is supported by the incident records.",
            "CONTRADICTED", [["I8", "I10"]], tags=["unsupported_synthesis"]),
        rec("C10", "The remediation plan is approved.",
            "CONTRADICTED", [["I9", "I10"]], tags=["draft_as_fact"]),
        rec("C11", "Moving certificate management to the platform team is the approved remediation.",
            "CONTRADICTED", [["I9", "I10"]], tags=["draft_as_fact"]),
        rec("C12", "The two incidents had different root causes.",
            "SUPPORTED", [["I1", "I2", "I8", "I10"]]),
    ],
    "production_items": [
        prod("P1", "How many distinct outages occurred in March 2026?",
             ["1", "2", "3", "insufficient"],
             "2", [["I1", "I2", "I8"]], tags=["unsupported_synthesis"]),
        prod("P2", "What was the duration of the 2 March outage in minutes?",
             ["45", "75", "90", "insufficient"],
             "75", [["I1"]]),
        prod("P3", "What caused the 2 March outage?",
             ["expired TLS certificate", "failed rollback", "database corruption", "insufficient"],
             "expired TLS certificate", [["I1", "I3"]]),
        prod("P4", "What caused the 4 March outage?",
             ["expired TLS certificate", "failed rollback", "database corruption", "insufficient"],
             "failed rollback", [["I2", "I6"]], tags=["unsupported_synthesis"]),
        prod("P5", "How many transactions failed in total across both outages?",
             ["12400", "15500", "3100", "insufficient"],
             "15500", [["I8"]], tags=["unsupported_synthesis"]),
        prod("P6", "Was the 4 March outage caused by the certificate expiry?",
             ["yes", "no", "insufficient"],
             "no", [["I2", "I6"]], tags=["unsupported_synthesis"]),
        prod("P7", "Is the executive email's single-event description supported by the incident records?",
             ["yes", "no", "insufficient"],
             "no", [["I8", "I10"]], tags=["unsupported_synthesis"]),
        prod("P8", "Is the remediation plan approved?",
             ["yes", "no", "insufficient"],
             "no", [["I9", "I10"]], tags=["draft_as_fact"]),
        prod("P9", "What remediation does the root-cause note recommend?",
             ["rotate certificates and re-enable expiry alerts",
              "move certificate management to the platform team",
              "database rollback", "insufficient"],
             "rotate certificates and re-enable expiry alerts", [["I3"]], tags=["draft_as_fact"]),
        prod("P10", "Did the two outages have the same root cause?",
             ["yes", "no", "insufficient"],
             "no", [["I2", "I8", "I10"]], tags=["unsupported_synthesis"]),
        prod("P11", "What was the duration of the 4 March outage in minutes?",
             ["45", "75", "90", "insufficient"],
             "45", [["I2"]]),
        prod("P12", "What caused the failed rollback?",
             ["expired TLS certificate", "incompatible schema change in the rollback script",
              "database corruption", "insufficient"],
             "incompatible schema change in the rollback script", [["I6"]], tags=["unsupported_synthesis"]),
    ],
    "consistency_rules": [
        {"id": "Y1", "when": {"P4": "expired TLS certificate"}, "forbid": {"P6": "no"},
         "tag": "internal_inconsistency"},
        {"id": "Y2", "when": {"P1": "1"}, "forbid": {"P10": "no"},
         "tag": "internal_inconsistency"},
    ],
    "summary": {
        "instructions": "Write a 2-4 sentence executive summary of the March incidents.",
        "required_terms": ["two"],
        "forbidden_phrases": [
            "one outage",
            "single outage",
            "both outages were caused by the certificate",
            "both incidents were caused by the certificate",
            "the remediation plan is approved",
        ],
    },
}



ACCEPTED = {
    "T1": {
        "P1": ["18 months", "18"],
        "P2": ["12 months", "12"],
        "P3": ["12 months", "12"],
        "P4": ["24 months", "24"],
        "P5": ["no"],
        "P6": ["35 days", "35"],
        "P7": ["no"],
        "P8": ["no"],
        "P9": ["Amendment A", "signed Amendment A"],
        "P10": ["yes"],
        "P11": ["12 months", "12"],
        "P12": ["no"],
    },
    "T2": {
        "P1": ["2", "two"],
        "P2": ["75", "75 minutes"],
        "P3": ["expired TLS certificate", "expired certificate", "certificate expiry"],
        "P4": ["failed rollback", "rollback failure"],
        "P5": ["15500", "15,500"],
        "P6": ["no"],
        "P7": ["no"],
        "P8": ["no"],
        "P9": ["rotate certificates and re-enable expiry alerts",
               "rotate certificates, re-enable expiry alerts",
               "rotate certificates automatically and re-enable expiry alerts",
               "rotate certificates", "re-enable expiry alerts",
               "rotate certificates automatically",
               "add a weekly certificate inventory check",
               "automatic certificate rotation"],
        "P10": ["no"],
        "P11": ["45", "45 minutes"],
        "P12": ["incompatible schema change in the rollback script",
                "schema change in the rollback script",
                "incompatible schema change"],
    },
}

def main() -> None:
    alternates_rec = {
        "T1": {
            "C1": [["D3"]],
            "C3": [["D2"], ["D3"]],
            "C4": [["D3"], ["D4"]],
            "C6": [["D1", "D3"]],
            "C8": [["D1"], ["D8"]],
            "C9": [["D6"], ["D7"]],
            "C10": [["D3"], ["D6"], ["D9"], ["D10"]],
            "C12": [["D4"], ["D11"]],
        },
        "T2": {
            "C1": [["I1", "I2"], ["I8"]],
            "C3": [["I2"], ["I6"]],
            "C4": [["I2", "I6"], ["I8"], ["I10"], ["I2"], ["I6"]],
            "C7": [["I2"], ["I8"]],
            "C8": [["I1"], ["I7"]],
            "C9": [["I8"], ["I10"]],
            "C10": [["I9"], ["I10"]],
            "C11": [["I9"], ["I10"]],
            "C12": [["I1", "I2"], ["I8"], ["I10"]],
        },
    }
    alternates_prod = {
        "T1": {
            "P2": [["D3"]],
            "P3": [["D2"]],
            "P5": [["D4"], ["D11"]],
            "P7": [["D1"], ["D8"]],
            "P8": [["D6"], ["D7"]],
            "P9": [["D3"], ["D6"], ["D9"]],
            "P12": [["D5"], ["D6"], ["D10"]],
        },
        "T2": {
            "P1": [["I8"], ["I1", "I2"]],
            "P3": [["I1"], ["I3"]],
            "P4": [["I2"], ["I6"]],
            "P6": [["I2"], ["I6"]],
            "P7": [["I8"], ["I10"]],
            "P8": [["I9"], ["I10"]],
            "P10": [["I2"], ["I8"], ["I10"]],
        },
    }
    for task in (T1, T2):
        tid = task["task_id"]
        for row in task["recognition_claims"]:
            for alt in alternates_rec.get(tid, {}).get(row["id"], []):
                if alt not in row["gold"]["evidence_sets"]:
                    row["gold"]["evidence_sets"].append(alt)
        for row in task["production_items"]:
            for alt in alternates_prod.get(tid, {}).get(row["id"], []):
                if alt not in row["gold"]["evidence_sets"]:
                    row["gold"]["evidence_sets"].append(alt)
            accepted = [row["gold"]["answer"]] + ACCEPTED.get(tid, {}).get(row["id"], [])
            row["gold"]["accepted_answers"] = list(dict.fromkeys(accepted))
        path = HERE / f"{task['task_id']}.json"
        path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(task['recognition_claims'])} claims, "
              f"{len(task['production_items'])} items, {len(task['sources'])} sources)")


if __name__ == "__main__":
    main()
