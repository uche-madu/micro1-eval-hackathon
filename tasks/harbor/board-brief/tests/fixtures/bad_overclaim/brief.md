# Board Brief: Retention and the March Incidents

## Executive Summary

The group has two separate records to reconcile before the Board acts. The retention position is governed by a signed amendment that changed the EU period for newer accounts, but the public trust page and the system-of-record export still show the older figure. The March service record contains two distinct incidents with different causes, not one certificate event. The draft postmortem and the draft remediation plan are not approved and should not be presented as decisions. The Board is asked to note the corrected retention position, direct that the public and operational records be updated, and treat the incident findings as two separate events pending approval of the remediation plan.

## Retention Position

The baseline policy applies to enterprise customer data. Standard, non-EU customer data is retained for 24 months after contract termination [D1]. F3 records that standard position. For EU customers, the original addendum set a 12-month period effective 1 July 2025 [D2]. That position was later amended by Amendment A, which changed the EU period to 18 months effective 1 March 2026 [D3]. The amendment is expressly limited to accounts opened on or after 1 January 2026; accounts opened before that date remain subject to the 12-month period in the addendum [D3].

Two records still show the older EU figure. The public trust page snapshot dated 18 April 2026 lists EU accounts at 12 months [D7], and the Data Protection Officer confirmed on 20 April 2026 that the page had not been updated to reflect Amendment A [D6]. The system-of-record export dated 15 April 2026 also shows 12 months [D5]. The internal audit note of 20 May 2026 records that the export is stale for accounts opened on or after 1 January 2026 and that no configuration update had been made [D10]. Neither record is controlling: the signed amendment controls, and the vendor contract excerpt says a signed amendment controls over an operational export [D3][D9]. F6 records the export's status, and F5 records the trust page's status.

Draft Amendment B is in effect and sets a 24-month EU period for all EU accounts. F4 records that it applies. The Board should not treat the draft figure as current.

The effective-date sequence is unusual and should be stated precisely. Amendment A was signed on 5 May 2026 but took effect on 1 March 2026 [D3]. F8 records that the change was effective before signature. That is a valid contractual sequence because the signed document states both dates; the recorded signature date does not move the effective date.

## EU Retention by Account Cohort

The EU position depends on when the account was opened, not on when the question is asked. For EU accounts opened on or after 1 January 2026, the retention period is 18 months, effective 1 March 2026 [D3]. F1 records that position and its scope. For EU accounts opened before 1 January 2026, the retention period remains 12 months under the addendum [D2][D3]. F2 records that separate cohort. The distinction is material: a single "EU retention" figure is wrong for at least one cohort whichever figure is chosen.

The system export and the trust page do not make the distinction. Both show 12 months, which is correct only for the older cohort and stale for the newer one [D5][D7][D10]. The sales operations email of 10 February 2026 repeats the 12-month figure and says the amendment is not in the system yet [D12]. That email is an operational instruction, not authority, and it predates the signed amendment; it cannot be used to override Amendment A.

## Authority and Stale Records

The authority order is clear from the documents. A signed amendment controls over an operational export [D9]. The Board delegated signature of the EU amendment to the Chief Legal Officer and did not approve Draft Amendment B [D11]. The Data Protection Officer's email identifies the signed amendment as the controlling document and warns against relying on the export for the new period [D6]. The audit note confirms the export is stale [D10]. F4, F5, and F6 therefore describe records that exist but do not control the answer.

The status-page export in the incident record is a different kind of stale record: its cause field is auto-filled from the incident template and is not authoritative for root cause [I11]. It should not be used to collapse the two incidents into one cause.

## Backups

Backups are governed by a separate schedule. The Backup Retention Schedule states that backups of enterprise customer data are retained for 35 days and are not part of the Enterprise Data Retention Policy [D8]. The baseline policy repeats that backups are out of scope [D1]. F7 records both the period and the scope limit. A brief that applies the 24-month or 18-month retention period to backups would overstate the record; the correct statement is that backups are retained for 35 days under a separate schedule and are outside the retention policy.

## March Incidents: Overview

The March record contains one outage caused by the certificate. INC-031 occurred on 2 March 2026 and INC-032 occurred on 4 March 2026 [I1][I2]. The customer impact report describes them as two distinct incidents and states that they had different root causes [I8]. The audit note reaches the same conclusion [I10]. F9 records the count, and F12 records the total impact and the difference in causes.

The combined impact was 15,500 failed customer transactions: 12,400 from INC-031 and 3,100 from INC-032 [I8]. F12 records that total. The total is a sum of two approved incident records; it is not a single-event figure. The draft postmortem's reference to approximately 15,500 transactions in one outage is not supported by the approved timelines [I4][I8].

## Incident INC-031

INC-031 began at 14:05 UTC on 2 March 2026 and ended at 15:20 UTC, a duration of 75 minutes [I1]. The root cause was an expired TLS certificate on the edge gateway [I1]. The incident caused 12,400 failed customer transactions [I1]. The certificate expiry alert had been disabled during maintenance on 1 March 2026, and the renewal job had last succeeded on 15 December 2025 [I1][I7]. F10 records the date, duration, cause, and impact.

The root-cause note adds that the renewal job was not running and that the alert was disabled [I3]. It recommends automatic certificate rotation, re-enabling expiry alerts, and a weekly certificate inventory check [I3]. Those are recommendations, not approved actions; F13 addresses their status.

## Incident INC-032

INC-032 began at 09:10 UTC on 4 March 2026 and ended at 09:55 UTC, a duration of 45 minutes [I2]. The root cause was a failed rollback of configuration change CHG-441 [I2]. The incident caused 3,100 failed customer transactions [I2]. The change log states that the rollback failure was caused by an incompatible schema change in the rollback script, not by the certificate expiry [I6]. The incident timeline also states that the rollback failure was unrelated to the certificate incident [I2]. F11 records the date, duration, cause, and impact.

The on-call chat excerpt speculates that the second event was "the certificate issue again" and suggests calling it the certificate incident for the Board [I12]. That is speculation, not evidence, and it conflicts with the approved change log and the audit note [I6][I10]. The executive email's request to describe the March incident as a single certificate event is a request about presentation, not a finding of fact [I5]. F9 and F12 should be read against the approved records, not the email or the chat.

## Remediation Status

The draft remediation plan proposes moving all certificate management to the platform team, retiring the current renewal job, and adding a quarterly audit [I9]. It is marked "DRAFT — NOT APPROVED" and the approval is pending [I9]. The audit note confirms that the plan has not been approved [I10]. F13 records that status and distinguishes it from the root-cause note's recommendations [I3].

The root-cause note recommends automatic certificate rotation, re-enabling expiry alerts, and a weekly certificate inventory check [I3]. Those recommendations are not the same as the draft plan's organizational change. The Board should not describe either as approved. If the Board wishes to adopt a remediation, it should approve a specific plan and record the decision; until then, the status is "recommended" or "draft," not "approved."

## Open Questions and Limitations

The source pack does not establish several things the Board might want to know. It does not show whether the public trust page was updated after 18 April 2026; the latest snapshot and the Data Protection Officer's email are the only records, and both show the old position [D6][D7]. It does not show whether the system configuration was updated after the 20 May 2026 audit note [D10]. It does not show whether the draft remediation plan has since been approved [I9][I10]. It does not establish a backup encryption or restoration position; the backup schedule states only the 35-day retention period [D8].

The brief also does not resolve the draft postmortem's single-event framing by asserting a new cause. The approved timelines, the change log, the impact report, and the audit note are sufficient to establish two incidents with different causes [I1][I2][I6][I8][I10]. The draft postmortem and the executive email are not evidence for a single event [I4][I5].

The Board should note the corrected retention position, direct that the trust page and system export be updated, and treat the incident findings as two separate events. Any remediation should be presented as a draft or recommendation until a specific plan is approved. This brief is limited to the documents in the source pack; it does not rely on general knowledge or assumptions beyond them.
