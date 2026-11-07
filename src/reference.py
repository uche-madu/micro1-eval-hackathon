"""Reference outputs derived from the task gold.

Used for grader self-tests and for dry runs. These are not model outputs.
"""

from __future__ import annotations

import json
from typing import Any

SUMMARY = {
    "T1": (
        "EU retention is 18 months for accounts opened on or after 1 January 2026, "
        "effective 1 March 2026, and 12 months for accounts opened before that date. "
        "The standard non-EU period is 24 months. Backups are retained for 35 days "
        "under a separate schedule and are not covered by the retention policy. "
        "The public trust page and the system export still show 12 months and are not current."
    ),
    "T2": (
        "Two distinct outages occurred in March: INC-031 on 2 March (75 minutes, expired "
        "TLS certificate, 12,400 failed transactions) and INC-032 on 4 March (45 minutes, "
        "failed rollback, 3,100 failed transactions). The causes were different, and the "
        "total impact was 15,500 failed transactions. The single-event framing in the "
        "executive email is not supported, and the draft remediation plan is not approved."
    ),
}


def recognition_reference(task: dict[str, Any]) -> str:
    claims = []
    for claim in task["recognition_claims"]:
        gold = claim["gold"]
        claims.append(
            {
                "claim_id": claim["id"],
                "verdict": gold["verdict"],
                "evidence_ids": gold["evidence_sets"][0] if gold["evidence_sets"] else [],
                "qualifier": " ".join(gold["qualifier_terms"]),
            }
        )
    return json.dumps({"claims": claims}, indent=2)


def production_reference(task: dict[str, Any]) -> str:
    items = []
    for item in task["production_items"]:
        gold = item["gold"]
        items.append(
            {
                "item_id": item["id"],
                "answer": gold["answer"],
                "evidence_ids": gold["evidence_sets"][0] if gold["evidence_sets"] else [],
                "qualifier": " ".join(gold["qualifier_terms"]),
            }
        )
    return json.dumps(
        {"items": items, "summary": SUMMARY[task["task_id"]]}, indent=2
    )
