# Board Brief: Retention and the March Incidents

You are the Chief of Staff at **Northwind Cloud Services** and **Meridian Payments** (the same group). The Board has asked for one briefing on two matters: the EU data-retention position and the March service incidents.

The complete source pack is in `/data/sources/` as 24 Markdown files (`D1`–`D12` for retention, `I1`–`I12` for incidents). The source pack is the **only** permitted evidence. Do not use general knowledge, memory, or assumptions.

Write two files:

1. `/output/brief.md` — a board brief of **1,500–2,000 words**.
2. `/output/findings.json` — exactly **13** findings in the schema below.

## Required brief structure

Use exactly these 10 section headings as level-2 Markdown headings (`##`), in this order. Do not add or remove sections. You may number them.

1. Executive Summary
2. Retention Position
3. EU Retention by Account Cohort
4. Authority and Stale Records
5. Backups
6. March Incidents: Overview
7. Incident INC-031
8. Incident INC-032
9. Remediation Status
10. Open Questions and Limitations

## Required findings

The 13 findings must cover these topics. Derive the values, dates, scope limits, and qualifications from the sources; do not assume them.

- **F1** — EU retention for accounts opened on or after 1 January 2026, including the effective date.
- **F2** — EU retention for accounts opened before 1 January 2026.
- **F3** — Standard (non-EU) retention.
- **F4** — The status of Draft Amendment B.
- **F5** — Whether the public trust page reflects the current EU position.
- **F6** — Whether the system-of-record export is current or controlling.
- **F7** — Backup retention and whether backups are covered by the retention policy.
- **F8** — The relationship between Amendment A's effective date and its signature date.
- **F9** — How many distinct incidents occurred in March 2026.
- **F10** — INC-031: date, duration, cause, and failed-transaction count.
- **F11** — INC-032: date, duration, cause, and failed-transaction count.
- **F12** — Total impact and whether the two incidents had the same cause.
- **F13** — The status of the remediation plan and what the root-cause note recommends.

## Findings JSON schema

```json
{
  "findings": [
    {
      "finding_id": "F1",
      "statement": "one or two sentences stating the conclusion",
      "evidence_ids": ["D3"],
      "qualifier": "the material scope, time, or population limit, or an empty string"
    }
  ]
}
```

Rules:

- Exactly 13 objects, with `finding_id` values `F1` through `F13`, each exactly once.
- `evidence_ids` must name the source file(s) that establish the finding (`D#` or `I#`). Do not cite a source that does not support the statement. One to three sources is enough.
- `qualifier` must carry any material limit. A limit is material if removing it changes the answer for at least one case the statement covers. Write `""` when there is no material limit.
- Do not add extra keys or extra findings.

## Brief rules

- The brief must include each finding ID (`F1` … `F13`) in the prose, at or near the relevant statement.
- Every factual statement must carry its evidence in brackets, for example `[D3]` or `[I2]`. A finding is not cited merely because its ID appears; the evidence ID must appear too.
- Do not invent figures. Every number in the brief must appear in the source pack. Dates, durations, counts, and percentages must match the sources exactly.
- Preserve effective dates, cohort scope, and material qualifiers. A true sentence that does not establish the stated conclusion is not support.
- Do not present a draft, plan, proposal, or request as an approved or effective fact.
- Do not mention the evaluation, the grader, the gold answer, the reference solution, or this instruction file in the brief. Write for the Board.

## Prohibited overclaims

The grader checks that the brief does **not** contain any of these unsupported claims, or a close paraphrase of them:

- There was one outage / a single outage in March.
- Both incidents were caused by the certificate, or had the same root cause.
- Draft Amendment B is in effect or approved.
- The draft remediation plan is approved.
- The public trust page is current.
- The system-of-record export is the controlling record.
- Backups are covered by the Enterprise Data Retention Policy.
- All EU data is retained for 24 months.
- The executive email is evidence or an authoritative record.
- The status-page cause field is authoritative for root cause.

If a source is a draft, an export, a request, or an auto-filled field, say so and do not treat it as authority.

## How the brief is scored

The score is out of 100, with partial credit:

- **Findings (52):** each of the 13 findings must contain the required fact(s), the correct evidence, and the material qualifier where one applies.
- **Structure (10):** exactly the 10 required headings.
- **Word count (5):** 1,500–2,000 words.
- **Traceability (10):** every finding ID appears in the prose, and every finding's evidence is cited in the prose.
- **No prohibited overclaims (8):** the list above.
- **No invented figures (5):** every number in the brief appears in the source pack.
- **Consistency and no evaluation leakage (10):** no internal contradiction, and no mention of the grader, gold, reference, or evaluation.

**Score caps.** Any prohibited overclaim caps the total at **60/100**. Invalid or missing `findings.json` caps the total at **50/100**. A mostly correct brief cannot compensate for a direct overclaim.

Accuracy matters more than length or polish. A short, fully supported brief beats a long, confident one that overstates the record.
