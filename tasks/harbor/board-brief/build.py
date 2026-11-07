"""Generate sources and gold for the Harbor board-brief task."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
T1 = json.loads((ROOT / "tasks" / "T1.json").read_text())
T2 = json.loads((ROOT / "tasks" / "T2.json").read_text())

sources = []
for task in (T1, T2):
    for s in task["sources"]:
        sources.append(s)

src_dir = HERE / "environment" / "data" / "sources"
src_dir.mkdir(parents=True, exist_ok=True)
for s in sources:
    body = (
        f"# {s['id']} — {s['title']}\n\n"
        f"- Type: {s['type']}\n"
        f"- Date: {s['date']}\n\n"
        f"{s['text']}\n"
    )
    (src_dir / f"{s['id']}.md").write_text(body)

(HERE / "tests" / "sources.json").write_text(
    json.dumps({s["id"]: s["text"] + " " + s["date"] + " " + s["title"] for s in sources}, indent=2) + "\n"
)

sections = [
    ["executive summary"],
    ["retention position"],
    ["eu retention by account cohort", "eu retention by cohort"],
    ["authority and stale records", "authority and stale"],
    ["backups"],
    ["march incidents: overview", "march incidents overview"],
    ["incident inc-031", "inc-031"],
    ["incident inc-032", "inc-032"],
    ["remediation status", "remediation"],
    ["open questions and limitations", "open questions"],
]

findings = {
    "F1": {
        "required_groups": [["18 months"], ["1 march 2026", "2026-03-01"]],
        "qualifier_groups": [["opened on or after 1 january 2026", "opened on or after"]],
        "evidence_any": [["D3"]],
    },
    "F2": {
        "required_groups": [["12 months"]],
        "qualifier_groups": [["before 1 january 2026", "opened before"]],
        "evidence_any": [["D2"], ["D3"], ["D2", "D3"]],
    },
    "F3": {"required_groups": [["24 months"]], "qualifier_groups": [], "evidence_any": [["D1"]]},
    "F4": {
        "required_groups": [["draft amendment b"], ["unsigned", "not approved", "not in effect"]],
        "qualifier_groups": [],
        "evidence_any": [["D4"], ["D11"], ["D4", "D11"]],
    },
    "F5": {
        "required_groups": [["trust page"], ["12 months"], ["not current", "stale", "not updated", "not been updated", "does not reflect", "out of date"]],
        "qualifier_groups": [],
        "evidence_any": [["D6"], ["D7"], ["D6", "D7"]],
    },
    "F6": {
        "required_groups": [["export"], ["12 months"], ["not controlling", "stale", "not current"]],
        "qualifier_groups": [],
        "evidence_any": [["D5"], ["D6"], ["D9"], ["D10"], ["D5", "D6"], ["D5", "D10"]],
    },
    "F7": {
        "required_groups": [["backups"], ["35 days"], ["out of scope", "not covered", "separate"]],
        "qualifier_groups": [],
        "evidence_any": [["D1"], ["D8"], ["D1", "D8"]],
    },
    "F8": {
        "required_groups": [["1 march 2026", "2026-03-01"], ["5 may 2026", "2026-05-05"]],
        "qualifier_groups": [],
        "evidence_any": [["D3"]],
    },
    "F9": {
        "required_groups": [["two"], ["distinct", "separate"]],
        "qualifier_groups": [],
        "evidence_any": [["I1", "I2"], ["I8"], ["I1", "I2", "I8"]],
    },
    "F10": {
        "required_groups": [["2 march", "2026-03-02"], ["75"], ["12,400", "12400"], ["certificate"]],
        "qualifier_groups": [],
        "evidence_any": [["I1"], ["I1", "I3"]],
    },
    "F11": {
        "required_groups": [["4 march", "2026-03-04"], ["45"], ["3,100", "3100"], ["rollback"]],
        "qualifier_groups": [],
        "evidence_any": [["I2"], ["I2", "I6"]],
    },
    "F12": {
        "required_groups": [["15,500", "15500"], ["different", "distinct"]],
        "qualifier_groups": [],
        "evidence_any": [["I8"], ["I10"], ["I8", "I10"]],
    },
    "F13": {
        "required_groups": [["remediation"], ["not approved", "unapproved"], ["rotate", "re-enable", "inventory"]],
        "qualifier_groups": [],
        "evidence_any": [["I3"], ["I9"], ["I10"], ["I3", "I9", "I10"]],
    },
}

forbidden = [
    "one outage",
    "single outage",
    "both incidents were caused by the certificate",
    "both outages were caused by the certificate",
    "the draft amendment is in effect",
    "draft amendment b is in effect",
    "the trust page is current",
    "the system-of-record export is controlling",
    "the system export is controlling",
    "the remediation plan is approved",
    "all eu data is retained for 24 months",
    "backups are covered by the retention policy",
]

gold = {
    "word_count": [1500, 2000],
    "finding_count": 13,
    "sections": sections,
    "findings": findings,
    "forbidden_phrases": forbidden,
    "allowed_numbers_extra": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "2025", "2026", "2027"],
}
(HERE / "tests" / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
print(f"wrote {len(sources)} sources, {len(findings)} findings, {len(sections)} sections")
