# March Incident Closure Memo

## Bottom Line

Closure is not established. The incidents should be treated as open until a closure decision and verification are recorded. The Board should not approve the draft remediation plan as written; it should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.

## Are the Incidents Closed?

Closure is not established. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and the audit note does not record a closure decision.

## What Happened

Two distinct incidents occurred in March 2026. INC-031 began on 2 March at 14:05 UTC, lasted 75 minutes, was caused by an expired TLS certificate on the edge gateway, and caused 12,400 failed transactions [I1]. INC-032 began on 4 March at 09:10 UTC, lasted 45 minutes, and caused 3,100 failed transactions [I2]. The total was 15,500 failed transactions [I8].

## Evidence Quality

The draft postmortem merges the two events into one and is not approved [I4][I10]. The executive email asks for a single-event narrative; it is a request, not evidence [I5][I10]. The status page cause field is auto-filled from the incident template and is not authoritative [I11]. The on-call chat is speculation [I12].

## Remediation Status

The draft remediation plan proposes moving certificate management to the platform team, retiring the renewal job, and adding a quarterly audit; it is not approved [I9][I10]. The root-cause note recommends rotating certificates automatically, re-enabling expiry alerts, and adding a weekly certificate inventory check [I3].

## Recommendation

The Board should not approve the draft plan as written. It should direct a specific plan based on the root-cause note, approve that plan, and require verification before closure.

## Open Questions

The pack does not show that the remediation actions were completed or that any remediation plan was approved [I3][I9][I10].
