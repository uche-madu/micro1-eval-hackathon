# 10-Turn State-Integrity Pilot Report

**Question:** does a model that can restate a constraint keep applying it after later updates — and does context size change that?

**Status:** complete. **Qwen answered every final question correctly in 6/6 trials. No recall–compliance dissociation at 10 turns.**

## 1. Executive summary

- **Oracle:** 2/2 tasks at **1.000**.
- **Qwen 3.8 Flash, short context:** 3/3 trials at **1.000**.
- **Qwen 3.8 Flash, long context:** 1/3 at **1.000**, 2/3 at **0.952**.
- **Final answers:** **6/6 correct in every trial** — old EU 12 months, new EU 24 months, Draft B in effect, 4 March cause = failed rollback, launch not approved, remediation not approved.
- **Stale fields:** **none**. The model applied the withdrawn 15-month rule and both late corrections in every trial.
- **No dissociation:** no trial restated the old state correctly and then used it in the final answers.

The two 0.952 scores were the **recall probe**, not state application. The probe field `incident_4_march` was ambiguous: the model answered with INC-032's duration and transaction count instead of the draft postmortem's certificate attribution. Its final answer for Q4 was correctly `failed rollback`. That is a probe-wording miss, not a state-integrity failure.

## 2. Design

Two Harbor tasks: `state-short` and `state-long`.

Both use the same 10 turns and the same 10 state updates. The long version pads each user message with ~150 words of neutral operational context; the updates, dates, and final questions are identical.

| Turn | State event |
|---:|---|
| 1 | Baseline: standard 24 months, EU 12 months, backups 35 days |
| 2 | Amendment A: EU 18 months for accounts opened on/after 2026-01-01; older accounts 12 |
| 3 | Temporary 15-month rule for old EU accounts, effective immediately |
| 4 | Draft Amendment B proposes 24 months for new EU accounts; not approved; trust page/export stale |
| 5 | Launch not approved until trust page/export updated and recorded |
| 6 | Two incidents; draft postmortem attributes both to certificate; postmortem and remediation plan not approved |
| 7 | **Recall probe:** current old EU, new EU, Draft B status, 4 March cause |
| 8 | Draft Amendment B approved effective immediately; new EU = 24 months |
| 9 | **Two corrections:** withdraw the 15-month rule (old EU = 12); 4 March cause = failed rollback, not certificate |
| 10 | **Final questions:** Q1–Q6 |

The final answers require applying turns 8 and 9, not the state captured at the turn-7 probe.

## 3. Results

| Condition | Trials | Reward 1.000 | Reward 0.952 | Final answers correct | Stale fields | Dissociation |
|---|---:|---:|---:|---:|---:|---:|
| Short | 3 | 3 | 0 | 18/18 questions | 0 | 0 |
| Long | 3 | 1 | 2 | 18/18 questions | 0 | 0 |

The 0.952 trials:

- `state-long__aGBNaka`: recall `incident_4_march` = “INC-032: 45 minutes, 3,100 failed transactions; draft postmortem not approved.” Final Q4 = “failed rollback of CHG-441.”
- `state-long__3VYmELN`: same pattern. Final Q4 correct.

The recall probe asked for a field named `incident_4_march`; the model reasonably returned the incident facts it had. It did not return the draft’s cause. The final answer was correct.

## 4. Does context size matter?

**At this scale, no.** The long condition had the same final-answer accuracy as the short condition: 18/18 questions correct. The only score differences came from the ambiguous recall field, and those trials still applied the final state correctly.

This is consistent with the 2026 literature, but it also locates the threshold:

- STATETRACK-BENCH finds failures concentrated at **greater dialogue depth** (up to 50 turns), not merely longer messages.
- LongDS finds a ~47-point drop from early to late turns, driven by **state dependency span**, not interaction budget.
- Hy-MultiTurn evaluates 12–76 turns; GPT-5.5 satisfies all requirements in only 41.1%.
- StateBench shows long **sequence** effects, but the relevant variable is the number of state changes the model must track.

A 10-turn conversation at ~4k tokens is below the regime where the failure appears. Padding the same 10 updates with neutral prose does not reproduce it. The failure the user sees in OpenCode/Claude Code is more likely **30–50 turns of accumulated state and tool actions**, where an early constraint becomes low-salience and the model stops applying it.

## 5. What this establishes

- Qwen can maintain a 10-turn state table, apply two late corrections, and answer all six final questions correctly in short and long contexts.
- Raw context padding at fixed update count does not degrade final-answer accuracy at this scale.
- The recall probe needs to name the specific field (“what does the draft postmortem say caused 4 March?”), not the incident as a whole.
- The 10-turn chat is not the right instrument for the observed failure.

## 6. Limitations

- **One model, three trials per condition.** Enough to stop this version, not to generalize.
- **One scenario.** Retention + incident only.
- **No tools or environment actions.** The observed OpenCode/Claude Code failure may require tool state, not just conversation state.
- **10 turns, ~4k tokens.** Below the literature’s failure regime.
- **Recall probe ambiguity.** The two 0.952s are a probe-wording artifact; the final answers were correct.

## 7. Decision

**Do not expand this 10-turn version.** It is a ceiling for Qwen.

The next version should change **depth and action**, not padding:

1. **30–50 turns** with 20–30 state updates, including withdrawn rules and late corrections. Keep the deterministic state table.
2. **Tool/action state:** a small workspace where the model edits a plan or config over many turns; a late correction must propagate to a previously written artifact.
3. **Recall probe with exact field names**, asked at two points, so a recall–compliance dissociation is measurable rather than inferred from an ambiguous label.

If a cheap model passes 30–50 turns, the remaining axis is agentic execution (Long-Horizon-Terminal-Bench’s 28% best, 6.4% mean), not conversation length.

## 8. Artifacts

- Tasks: `tasks/harbor/state-integrity/{state-short,state-long}/`
- Oracle: `harbor run -p tasks/harbor/state-integrity -a oracle` → 2/2 at 1.000
- Transcripts: `results/transcripts/{short_pass,long_pass,long_recall_miss}/`
- Agent: `harbor_agents/host_state_agent.py`
- Gap ledger: `GAPS.md` (G1–G4)
