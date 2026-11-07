# March Incident Closure Memo

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
