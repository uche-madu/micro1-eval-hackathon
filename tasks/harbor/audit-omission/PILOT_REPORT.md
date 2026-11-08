# Pure-Omission Audit Pilot Report

**Question:** can a model notice a decision-critical fact that is **absent** from an otherwise correct deliverable, when nothing in the deliverable contradicts it?

**Status:** pilot complete. **Both Qwen and GPT-6 Luna pass 10/10. No frontier limitation found.**

## 1. Executive summary

- **Oracle:** 4/4 tasks at **1.000**.
- **Final Qwen 3.8 Flash:** **10/10** at 1.000 — 5/5 clean, 5/5 omission.
- **Final GPT-6 Luna:** **10/10** at 1.000 — 5/5 clean, 5/5 omission.
- **False-pass rate:** **0.0** for both models after the clean control was corrected.

The earlier Qwen run showed 1/3 and 1/5 false passes on the incident omission. That result did **not** survive a clean-control review. The clean memo claimed “the audit note treats the incidents as open,” which the audit note does not say. GPT false-failed that clean memo 5/5, and Qwen’s omission failures were tied to the same flawed memo. After correcting the clean control to “closure is not established; the audit note does not record a closure decision,” both models passed every clean and omission trial.

**Conclusion:** pure omission in this scenario is not a frontier-model limitation. Do not expand.

## 2. Design

Four Harbor tasks under `tasks/harbor/audit-omission/`:

| Task | Deliverable |
|---|---|
| `retention-clean` | internally consistent, complete |
| `retention-omission` | same memo, but does not state that the export/trust page are stale; recommends launch without updates |
| `incident-clean` | internally consistent, complete |
| `incident-omission` | same memo, but omits the INC-032 rollback cause and “different causes”; keeps a generic remediation recommendation |

The model gets the assignment, the source pack, and one deliverable. It returns `FIT`/`NOT_FIT` plus findings. The seeded defect is an **absence**, not a contradictory sentence.

## 3. The correction that mattered

The first clean incident memo said:

> “No. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and **the audit note treats the incidents as open**.”

The audit note does not say the incidents are open. GPT-6 Luna rejected the “clean” memo 5/5 for that overstatement. That was a real defect in my clean control, not a model failure.

Corrected clean memo:

> “Closure is not established. The pack contains no closure decision or verification record. The status page and the draft postmortem do not establish closure, and the audit note does not record a closure decision.”

The omission memo uses the same corrected language and keeps a generic “based on the root-cause note” recommendation, so the missing rollback cause remains the only defect.

## 4. Final results

| Model | Condition | Trials | Pass at 1.000 | False pass | False fail |
|---|---|---:|---:|---:|---:|
| Qwen 3.8 Flash | clean | 5 | 5 | 0 | 0 |
| Qwen 3.8 Flash | omission | 5 | 5 | **0** | 0 |
| GPT-6 Luna | clean | 5 | 5 | 0 | 0 |
| GPT-6 Luna | omission | 5 | 5 | **0** | 0 |

Representative Qwen omission audit:

> The memo omits that INC-032 was caused by a failed rollback unrelated to the certificate incident. Without that fact, the Board cannot assess whether the certificate-focused draft remediation addresses all incidents or whether closure is justified.

Representative GPT omission audit:

> The memo omits that INC-032 was caused by a failed rollback unrelated to the certificate incident. Without that fact, the Board cannot assess whether the certificate-focused draft remediation addresses all incidents or whether closure is justified.

Both locate the absence and explain why it matters.

## 5. Earlier result, preserved

The earlier Qwen runs (before the clean-control correction) produced false passes that looked like a finding:

- `jobs/audit_omission_qwen2/incident-omission__Bmtzsu5`: verdict `FIT`, one minor finding, reward 0.047619.
- `jobs/audit_omission_qwen3/incident-omission__oFSBotv`: verdict `FIT`, no findings, reward 0.047619.

Those transcripts are copied to `results/transcripts/early_qwen_false_pass/`. They are not deleted or hidden. They are explained by the flawed clean memo: the model was reacting to an unsupported “audit note says open” sentence, and the omission condition inherited that text. Once the control was corrected, the false pass disappeared.

**Lesson:** a false sentence in the clean deliverable can produce both false fails (GPT) and false passes (Qwen) that look like model behavior. Human review of the clean control is not optional.

## 6. What this establishes

- Both a cheap and a frontier model can notice a decision-critical omission in a short, internally consistent memo when the source pack is in front of them.
- The omission defect is not a stable frontier weakness at this difficulty.
- The earlier 20–25% false-pass estimate was an artifact of the clean-control defect, not a reliable model property.

## 7. Limitations

- **One scenario family** (incident omission) for the final result; the retention omission was caught 3/3 by Qwen.
- **Short memo, 24 sources, one-shot.** This is not multi-turn state tracking or long-horizon execution.
- **One omission per scenario.** A denser omission pattern might be harder.
- **The clean-control correction was driven by GPT’s critique.** That is appropriate, but a second human reviewer should confirm the corrected memo is unambiguously fit.
- **Small n.** Five trials per condition per model; report raw counts, not significance.

## 8. Decision

**Stop.** Both models pass. Do not expand the omission benchmark.

The next credible frontier weakness is not another single-turn audit. The 2026 evidence points to **multi-turn state integrity** and **long-horizon execution**:

- STATETRACK-BENCH: 88.6% of failures are “recall but do not apply,” not forgetting.
- LongDS: best model 48.45%; ~47-point drop from early to late turns.
- TurnFlow: 27.5–51% aggregate pass; locally helpful, globally invalid.
- Hy-MultiTurn: GPT-5.5 satisfies all requirements in only 41.1% of 12–76 turn dialogues.
- Long-Horizon-Terminal-Bench: best 28.3%, mean 6.4%.

If the project continues, build the **10-turn state-integrity pilot** described in the research note: one evolving organizational decision, a recall probe at turn 7, final decisions at turn 10, deterministic state table, Qwen first. That is the axis our one-shot pilots have not tested.

## 9. Artifacts

- Tasks: `tasks/harbor/audit-omission/`
- Oracle: `harbor run -p tasks/harbor/audit-omission -a oracle` → 4/4 at 1.000
- Final transcripts: `results/transcripts/{qwen,gpt}_{clean,omission}/`
- Early false-pass transcripts: `results/transcripts/early_qwen_false_pass/`
- Scorer: `tasks/harbor/audit-omission/*/tests/score.py`
- Agent: `harbor_agents/host_audit_agent.py`
