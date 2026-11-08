# Findings: execution reliability at the frontier

**Objective:** find a reproducible weakness in frontier models, or exhaust the feasible hypothesized failure modes.

**Result:** the earlier single-context axes (audit, state recall, injection, planning, tool use) were robust. In the **corrected execution-state benchmark (v2)**, Qwen 3.8 Flash reproduced a core duplicate-operation failure in **2/28** valid trials. GPT-6 Luna (**18** valid trials) and Opus 5.5 (**30/30**) had **no duplicate operations, no missing operations, and no incorrect final states**. GPT showed a distinct dependency/verification weakness: **7/18** valid trials called the batch before its prerequisites, and **11/18** finished without a final verification read. The original frontier execution-state divergence hypothesis is **not confirmed at this scale**: the corrected benchmark isolates a Qwen-specific repeat failure and a GPT-specific order/verification weakness. The v1 results are preserved as historical evidence.

## Execution-state divergence — corrected v2

See `tasks/harbor/exec-state-v2/RESULTS.md` for the full tables and `README.md`
for the environment. The v1 benchmark and its results remain at
`tasks/harbor/exec-state/` untouched.

The v2 task: 40 operations (create, update, approve, assign, transfer, note,
delete) against a persistent account store, with **explicit, enforced
dependencies**, the same hidden fault distribution as v1 (3 lost acknowledgements,
3 fail-before, 1 partial batch, 1 stale read, 1 dependency), and a first batch
attempt that cannot be bypassed with `op_ids`.

| Model | Valid trials | Pass | Duplicate ops | Missing ops | Incorrect state | Dependency violations | No final read | Format/interface failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 3.8 Flash | 28 | 25 | **2** | 0 | 0 | 1 | 0 | 0 (1 DNS, 1 hang) |
| GPT-6 Luna | 18 | 5 | **0** | 0 | 0 | 7 | 11 | 2 |
| Opus 5.5 | 30 | 30 | **0** | 0 | 0 | 0 | 0 | 0 |

Key result: Qwen repeated an operation it had already confirmed committed
(OP21 after `get_operation → committed`; OP33 after a clean `ok`). The duplicate
side effect was real even when the final field values remained correct, and Qwen
reported completion. GPT-6 Luna and Opus 5.5 did not repeat, omit, or corrupt
state; GPT's failures were dependency-order attempts and missing final reads.

## Execution-state divergence — v1 (historical)

The v1 benchmark (no enforced dependencies, first-batch bypass open) found
low-rate failures in both models. It is preserved as historical evidence;
its ordering failure cannot occur in v2 because the environment now rejects an
earlier update after a later approval.

| Model | Trials | Pass | Fail | Failure signature |
| --- | ---: | ---: | ---: | --- |
| Qwen 3.8 Flash | 10 | 8 | 2 | duplicate `create_account` after a clean `ok` |
| GPT-6 Luna | 20 | 18 | 2 | one missing approval status, false completion |
| DeepSeek v4.1 Flash | 5 valid | 5 | 0 | no state failure; one format-failure trial excluded |
| Gemini-4 Argon | 0 | — | — | upstream unavailable (502) |

The v1 task had 40 operations against a persistent account store, with a hidden
fault schedule — three lost acknowledgements after commit, three failures before
commit, one partial batch, one stale read, and one dependency. Across 30 trials
and 120 ambiguous outcomes, **no trial retried a timeout it had confirmed
committed**. The v1 failures were in clean-operation tracking: Qwen repeated a
`create_account` that had returned `ok`; GPT lost an approval once by omitting
`OP26` and once by applying an earlier update after the approval. All four
failures reported `complete: true`.

## What was tested

| # | Axis | Task | Model(s) | Result | Verdict |
|---|---|---|---|---:|---|
| 1 | Compact claim adjudication | T1/T2, 12 claims, 12 sources | Qwen, DeepSeek, GPT, Gemini, Haiku | Production 100%; no recognition–production gap | No limitation |
| 2 | Structured long-horizon generation | 24 sources, 1,500–2,000 words, 13 findings | Qwen 3.8 Flash | 1.000; oracle 1.000 | No limitation |
| 3 | Audit with blatant defects | 2 scenarios × clean/defective | Qwen, Gemini, GPT | False pass 0.0; GPT clean false fails exposed a memo error | No frontier false pass |
| 4 | Audit with one subtle contradiction | 2 scenarios, one changed sentence | Qwen | 12/12 at 1.000 | No limitation |
| 5 | Pure omission | 2 scenarios, one missing fact | Qwen, GPT | 10/10 each; early false passes were a clean-control artifact | No limitation |
| 6 | 10-turn state integrity | 10 turns, recall probe, late corrections | Qwen | Final answers 6/6; no dissociation | No limitation |
| 7 | **30-turn state integrity** | 30 turns, 20+ updates, 2 recall probes, 5 reversals | **Qwen; GPT** | **Qwen 1/5 dissociation** (`new_eu` 24 vs 26); GPT 5/5 | **Qwen-specific, not frontier** |
| 8 | 50-turn state integrity | 50 turns, 30+ updates, 4 reversals | Qwen; GPT | Qwen 3/3 at 1.000; GPT 5/5 | No limitation |
| 9 | Self-audit framing | same defective memo, “you wrote it” vs “another analyst” | Qwen | 5/5 self, 5/5 other | No self-verification bias |
| 10 | Sycophancy / authority pressure | control, polite, COO directive | Qwen | 15/15 `not_approved` | No sycophancy |
| 11 | Artifact state | 20 turns, full JSON each turn, no assistant history | Qwen | 1/1 at 1.000 | No limitation |
| 12 | Indirect prompt injection | direct, authority-spoofed, subtle | Qwen | 3/3; no code/email leak | No injection |
| 13 | Quantitative aggregation | 24 accounts, tiers, exception, exclusion | Qwen | 1/1 exact ($69,850 / 8,730) | No limitation |
| 14 | Constraint planning | 8 meetings, rooms, dependencies, lunch | Qwen | 1/1 valid schedule | No limitation |
| 15 | Tool-using terminal task | fix a buggy pipeline, held-out CSV | Qwen | 1/1 at 1.000 | No limitation |

## The one real failure

At 30 turns, one Qwen trial showed the signature we were looking for:

- Turn 20 recall: `new_eu = 26 months`.
- Turn 30 final: `new_eu = 24 months`.
- No later update changed 26; it reverted to the value from turn 8.
- The trial also got the other seven final fields correct.
- **Score 88.6; `dissociation = true`; stale field `new_eu`.**

It did not reproduce:

- The other four valid Qwen 30-turn trials were 100.
- At 50 turns, Qwen was 3/3 at 100.
- GPT-6 Luna was 5/5 at 30 turns and 5/5 at 50 turns.

So the failure is a **stochastic cheap-model state slip**, not a frontier weakness. It is real, but it is not enough for the hackathon's "frontier models fail" criterion.

## What the negative results mean

The tested tasks share a property: the model can hold the whole state in one context, and the decision is textual. In that regime, current models are strong. The 2026 literature agrees:

- Long-Horizon-Terminal-Bench: best 28.3%, mean 6.4% — but at 239 episodes, 9.8M tokens, 89 minutes.
- OSWorld 2.0: best 20.6% binary completion — 108 workflows, median 1.6 hours, 318 tool calls.
- HORIZON: planning and memory failures dominate as horizon grows.
- STATETRACK-BENCH: 88.6% of failures are recall-without-application; degradation concentrates at greater depth.
- DeepPlanning: best fully correct plans 35% — multi-day, tool-using planning.

Our tasks are 10–50 turns, 8–30 documents, 7 tool steps. That is below the failure regime. The model's single-context evidence discipline is strong; the weakness is **long-horizon execution with many tool actions, partial failures, and recovery**, not the conversation-length or document-audit versions we can build in a day.

## Recommendation for the submission

The corrected v2 benchmark is the primary evidence. It is a **mixed result**, not
a confirmed frontier weakness:

1. **Submit the corrected benchmark as the primary finding.** Qwen 3.8 Flash
   repeated an operation it had already confirmed committed in 2/28 valid trials
   (OP21 after `get_operation → committed`; OP33 after a clean `ok`). The
   duplicate side effect was real even though the final field values remained
   correct.
2. **Do not claim a frontier-wide execution-state weakness.** GPT-6 Luna (18
   valid trials) and Opus 5.5 (30/30) had no duplicate operations, no missing
   operations, and no incorrect final states. The v1 GPT ordering corruption
   cannot occur in v2 because the environment rejects an earlier update after a
   later approval.
3. **Report GPT's dependency/verification weakness as a separate result.** 7/18
   valid GPT trials called the batch before its prerequisites, and 11/18
   finished without a read after the last write. The final state was correct;
   the enforcement prevented corruption. This is a planning/verification
   failure, not state divergence.
4. **Keep v1 as historical evidence.** The v1 GPT 2/20 result depended partly on
   an implicit ordering constraint and is superseded by v2. The v1 Qwen
   duplicate finding is consistent with v2.
5. **The next credible axis is harder observability, not more trials at the same
   setting.** Remove the per-operation status tool (or expose only aggregate
   history), increase to 80–100 operations, and test whether frontier models
   still complete the final state. The current ledger makes ambiguity
   reconciliation easy; that is why no model retried a confirmed timeout.

## Artifacts

- Execution-state v2: `tasks/harbor/exec-state-v2/` (`README.md`, `RESULTS.md`, `build.py`, `score_template.py`, `test_env.py`, `analyze.py`, `collect.py`)
- v2 raw representative transcripts: `tasks/harbor/exec-state-v2/results/transcripts/`
- Execution-state v1 (historical): `tasks/harbor/exec-state/` (`README.md`, `RESULTS.md`, generated tasks, transcripts)
- Gap ledger: `GAPS.md`
- Run history: `RUNS.md`
- Frozen pilots: `FREEZE.md`
- Audit: `tasks/harbor/audit/`, `tasks/harbor/audit-subtle/`, `tasks/harbor/audit-omission/`
- State: `tasks/harbor/state-integrity/` (10 turns), `tasks/harbor/state-deep/` (30), `tasks/harbor/state-deep50/` (50)
- Other axes: `tasks/harbor/{self-audit,sycophancy,artifact-state,injection,quant,scheduling,mini-terminal}/`
