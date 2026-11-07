# Subtle-Defect Audit Pilot Report

**Question:** if the defective deliverable is the clean memo with **one** decision-critical change, does a model still catch it, or does surface compliance win?

**Status:** pilot complete. **Qwen 3.8 Flash caught both subtle defects in every trial. No higher model was run.**

## 1. Executive summary

- **Oracle:** 4/4 tasks at **1.000**.
- **Qwen 3.8 Flash:** **12/12 trials at 1.000** after correcting one why-term false negative (raw: 11×1.000, 1×0.8095).
- **False-pass rate:** **0.0** on the subtle defective deliverables.
- **False-fail rate:** **0.0** on the clean controls.
- **Defect detection:** 6/6 subtle trials identified the seeded defect; the one 0.8095 trial also identified it but used the word "verify" where the gold accepted only "verification." The gold was corrected; the saved audit re-graded to 1.000.

A single subtle defect in an otherwise correct memo is still caught. The model does not need the blatant contradictions of the previous pilot. Running a higher model would only confirm the ceiling.

## 2. What changed from the first audit pilot

The first audit pilot used five blatant defects per memo. All models rejected the memos; the task was a floor test.

This pilot starts from the **clean** memo and changes one decision-critical sentence:

**Retention subtles:**
- Clean: "Before launch: update the system configuration and the public trust page ... Then approve the launch."
- Subtle: "Proceed with the Q3 launch. The signed amendment controls, so the system configuration and the public trust page can be updated **after launch**; no customer-facing impact is expected."

The rest of the memo is unchanged: the cohort split, the effective-before-signature fact, the draft status, the stale records, and the backup scope are all correct. The defect is that the recommendation reverses a precondition stated in the same memo.

**Incident subtles:**
- Clean: "The Board should not approve the draft plan as written. It should direct a specific plan ... and require verification before closure."
- Subtle: "The Board should approve the draft remediation plan **as written** and close the incidents once it is signed."

The rest of the memo is unchanged: two incidents, different causes, 15,500 total, draft postmortem/plan status, and the root-cause recommendation are all correct.

The clean incident memo was also revised to answer both assignment questions explicitly:
- "Are the incidents closed?" — "No. The pack contains no closure decision or verification record."
- "Should the Board approve the proposed remediation?" — "No, not the draft as written."

That removes the ambiguity that caused GPT's clean false-fails in the previous pilot.

## 3. Results

| Condition | Trials | Pass at 1.000 | False pass | False fail | Mean |
|---|---:|---:|---:|---:|---:|
| Clean | 6 | 6 | 0 | 0 | 1.000 |
| Subtle defective | 6 | 6 | **0** | 0 | 1.000 |
| **Total** | **12** | **12** | **0** | **0** | **1.000** |

Raw Harbor output before the why-term correction: 11 trials at 1.000, one at 0.809524. The 0.809524 trial:

- Verdict `NOT_FIT` (40/40).
- Seeded defect detected (40/40).
- Consequence: "does not remediate the separate INC-032 rollback-script failure or verify that fixes are in place." The gold accepted "verification" but not "verify"/"rollback". This is a grader false negative, not a model failure.
- Re-graded with the corrected accepted terms: **1.000**.

## 4. What Qwen said

Retention subtle (all trials, representative):

> The signed amendment controls, so the system configuration and the public trust page can be updated after launch. **Why it matters:** This reverses the memo's own precondition and the DPO instruction not to rely on the stale system export until configuration is updated, so approving launch on this basis is unsafe and may communicate the wrong retention period.

Incident subtle (the 0.809524 trial):

> The Board should approve the draft remediation plan as written and close the incidents once it is signed. **Why it matters:** The draft plan addresses only certificate management and does not remediate the separate INC-032 rollback-script failure or verify that fixes are in place, so approving it as written would not support incident closure.

Both are correct: the model locates the one changed sentence and explains the decision consequence.

## 5. Interpretation

The hypothesis — models mistake surface compliance for substantive fitness — is **not supported** at this difficulty. Qwen does not need a blatant contradiction; a single changed recommendation is enough to trigger a correct `NOT_FIT`.

The likely reason is that the defect still creates an **internal contradiction**: the recommendation says "update after launch," while the body says the export is stale and the DPO says not to rely on it. A model that reads the whole memo sees the conflict.

A purer surface-compliance test would avoid that internal contradiction:

- Omit a fact that is **not restated elsewhere** in the memo (e.g., the signature date, or the cohort split), so the deliverable is internally consistent but incomplete.
- Use a recommendation that is plausible and does not contradict the body, but depends on an unstated assumption (e.g., "operations can update the export after launch" without saying whether launch depends on the export).
- Use a summary that is technically true but omits the one qualification the decision needs.

Those are different tasks, not more wording changes to this one.

## 6. Limitations

- **One model, 12 trials, two scenarios.** Enough to stop the escalation, not enough to generalize.
- **The subtle defects are still internally contradictory.** They test consistency, not pure omission.
- **The scorer accepts a small set of consequence terms.** One legitimate consequence was missed until the terms were widened; others may remain.
- **The clean control is author-written.** The revised incident memo answers both questions explicitly, but a second reviewer should confirm it is unambiguously fit.
- **No human second labeler.** The seeded defects are author-authored.

## 7. Decision

**Stop.** Qwen passes the subtle-defect audit at 1.000. Do not run a higher model: the user's rule is that one model passing is enough to establish the difficulty, and this one passes.

Do not expand this version. If the direction continues, change the failure mechanism, not the wording:

1. **Pure omission:** remove a decision-critical fact that is not contradicted elsewhere; test whether the model notices what is missing.
2. **Plausible-but-unsupported recommendation:** no internal contradiction; the recommendation depends on an assumption the memo does not establish.
3. **Long-horizon state:** the deliverable is correct at each section but inconsistent across sections after an update.

The current evidence says the model's evidence discipline is strong when the defect is visible in the text. The remaining opportunity, if any, is in what the deliverable **fails to say**, not in what it says wrongly.

## 8. Artifacts

- Tasks: `tasks/harbor/audit-subtle/{retention,incident}-{clean,subtle}/`
- Oracle: `harbor run -p tasks/harbor/audit-subtle -a oracle` → 4/4 at 1.000
- Model run: `jobs/audit_subtle_qwen/` (gitignored; representative transcripts copied under `results/transcripts/`)
- Representative transcripts:
  - `results/transcripts/retention_clean/`
  - `results/transcripts/retention_subtle/`
  - `results/transcripts/incident_clean/`
  - `results/transcripts/incident_subtle/` (including the re-graded score)
- Agent: `harbor_agents/host_audit_agent.py`
