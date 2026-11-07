# Subtle-defect audit pilot

Four Harbor tasks: two scenarios (EU retention, March incidents) × clean/subtle.

The subtle deliverable is the clean memo with **one** decision-critical sentence changed:

- Retention: "update the system configuration and trust page before launch" becomes "can be updated after launch."
- Incident: "do not approve the draft plan as written" becomes "approve the draft plan as written and close once signed."

The rest of each memo is correct. The model must decide `FIT`/`NOT_FIT` and explain the one defect. No defect list is shown.

Oracle: `harbor run -p tasks/harbor/audit-subtle -a oracle` → 4/4 at 1.000.

Qwen 3.8 Flash: 12/12 at 1.000 after a why-term correction; false-pass 0, false-fail 0. No higher model was run.

Full report: `PILOT_REPORT.md`.
