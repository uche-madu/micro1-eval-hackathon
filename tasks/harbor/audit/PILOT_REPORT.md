# Surface-Compliance Audit Pilot Report

**Question:** can models tell whether a completed organizational deliverable is fit for purpose, or do they mistake surface compliance for substantive quality?

**Status:** pilot complete. **Recommendation: do not expand this version; the defects are too blatant to test the hypothesis.**

## 1. Executive summary

The pilot built four Harbor audit tasks: two scenarios (EU retention, March incidents), each with a clean deliverable and a superficially compliant but defective deliverable.

- **Oracle:** 4/4 tasks at **1.000**.
- **False-pass rate on defective deliverables: 0.0 for all three models.**
  - Qwen 3.8 Flash: 0/6 defective trials approved.
  - Gemini 4 Argon: 0/6.
  - GPT-6 Luna: 0/6.
- **Clean controls:** Qwen 6/6 at 1.000; Gemini 6/6 at 1.000; GPT 3/6 (three incident-clean false fails).
- **Defect detection:** Qwen matched 2.83/5 seeded defects on average; Gemini 3.33/5; GPT 3.67/5. All three rejected the defective memos, but often missed some seeded defects or classified them under a different type.

The hypothesis was **not supported at this defect difficulty**. The models did not approve the defective deliverables. They were cautious, sometimes over-flagging, and GPT rejected a clean incident memo for a legitimate ambiguity in that memo.

## 2. Design

Four tasks under `tasks/harbor/audit/`:

| Task | Scenario | Deliverable |
|---|---|---|
| `retention-clean` | EU retention / Q3 launch decision memo | genuinely fit for purpose |
| `retention-defective` | same assignment and sources | format-compliant, five material defects |
| `incident-clean` | March incident closure / remediation decision | genuinely fit for purpose |
| `incident-defective` | same assignment and sources | format-compliant, five material defects |

The model receives `/data/assignment.md`, `/data/sources/`, and `/data/deliverable.md`. It does not know whether the deliverable is clean or defective. It returns:

```json
{"verdict": "FIT|NOT_FIT", "findings": [{"section": "...", "problem_type": "...", "severity": "material|minor", "evidence": "...", "why_it_matters": "..."}]}
```

The taxonomy is general (unsupported recommendation, misleading summary, missing decision info, date/authority error, proposed-as-approved, invalid synthesis, unsupported assertion, scope generalization), not a list of the seeded defects.

## 3. Scoring

Deterministic; no LLM judge.

**Defective (100 points):**
- 30 verdict `NOT_FIT`
- 50 defect detection (5 seeded defects × 10)
- 20 consequence explanation (4 per matched defect)

**Clean (100 points):**
- 30 verdict `FIT`
- 60 no material findings
- 10 no invented defects

**Caps:**
- `FIT` on a defective deliverable (false pass): **0.50**
- `NOT_FIT` on a clean deliverable (false fail): **0.50**
- invalid audit JSON: **0.40**

Extra findings on defective deliverables are recorded but not penalized: they may be legitimate issues the five-defect seed did not enumerate.

## 4. Results

| Model | Condition | Trials | Mean score | Pass rate | False pass | False fail | Defects matched (of 5) |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen 3.8 Flash | clean | 6 | 100.00 | 1.000 | 0.000 | 0.000 | 0.00 |
| Qwen 3.8 Flash | defective | 6 | 68.57 | 0.000 | **0.000** | 0.000 | 2.83 |
| Gemini 4 Argon | clean | 6 | 100.00 | 1.000 | 0.000 | 0.000 | 0.00 |
| Gemini 4 Argon | defective | 6 | 75.24 | 0.000 | **0.000** | 0.000 | 3.33 |
| GPT-6 Luna | clean | 6 | 52.38 | 0.500 | 0.000 | **0.500** | 0.00 |
| GPT-6 Luna | defective | 6 | 80.32 | 0.000 | **0.000** | 0.000 | 3.67 |

**DeepSeek V4.1 Flash:** excluded. It returned empty content because it spent the output budget on reasoning tokens. Four trials errored before the run was stopped; no valid audit was produced.

## 5. What the models actually did

The defective deliverables contain direct contradictions: the retention memo says the Board approved Draft Amendment B, that all EU accounts move to 18 months, and that backups are covered by the retention period. The incident memo says there was one certificate event, that both incidents had the same cause, that the alert was re-enabled, and that the remediation plan was approved.

All three models rejected both defective memos. They did not mistake the memo's format, headings, or citations for substantive fitness. This is the opposite of the hypothesised failure.

Examples:

- Qwen, retention-defective: identified the draft-as-current defect, the Board-approval error, the cohort generalization, the stale export, the backup error, and the missing preconditions.
- Gemini, retention-defective: identified the draft-as-current defect, the cohort error, the backup error, and the recommendation; it missed or re-typed some seeded defects.
- GPT, incident-defective: identified the single-event framing, the same-cause error, the re-enabled alert, and the approval status; it matched 3.67/5.

## 6. The clean-control issue

GPT rejected all three `incident-clean` trials. Its audit says the memo does not state whether the incidents are formally closed or whether the Board should approve, reject, or amend the specific proposed plan.

This is a **legitimate ambiguity in the clean memo**, not only model over-criticism. The memo says:

- "The two March incidents are not ready to close" — but does not explicitly say "they are not closed; no closure decision exists."
- "The Board should approve a specific remediation plan" — but does not explicitly say "do not approve the draft plan as written; direct a specific plan."

Qwen and Gemini accepted the memo; GPT did not. For a clean control, the deliverable should answer both assignment questions directly. The clean incident memo needs a revision that says, in terms:

1. "Are the incidents closed?" — "No. The pack contains no closure decision or verification record."
2. "Should the Board approve the proposed remediation?" — "No, not the draft as written. The Board should direct a specific plan and approve that plan after verification."

Until that revision, the GPT clean false-fail is a **control limitation**, not a clean model finding. It does not affect the false-pass result because the defective condition is unchanged.

## 7. Why the false-pass result is not enough to save the benchmark

The defective memos are too easy. They contain claims that directly contradict the source pack (e.g., "the Board approved Draft Amendment B" when D11 says it did not). A model does not need to understand surface compliance versus substance to catch those; it only needs to compare a few sentences.

The reviewer's interesting case is a deliverable that **looks right and is mostly right** but fails on one decision-critical point: a recommendation that is plausible but ignores a precondition, a summary that is technically true but omits a material qualification, or a memo that answers the literal question while missing the decision the Board actually needs. This pilot does not test that.

## 8. Limitations

- **Two scenarios, six trials per condition per model.** Small; report raw counts, not significance.
- **Five seeded defects per scenario.** Extra legitimate findings are not penalized, but they are also not credited; the detection score is a lower bound on audit quality.
- **Blatant defects.** The defective memos contain direct contradictions; the pilot is a floor test, not a surface-compliance test.
- **Clean-control ambiguity.** The incident-clean memo does not explicitly answer "are they closed?" and "approve the draft?"; GPT's false fails expose that.
- **Taxonomy matching.** A correct observation classified under a different `problem_type` can miss the seed; this understates detection.
- **DeepSeek unavailable.** The third family was replaced by GPT-6 Luna; DeepSeek produced no content.
- **No human second reviewer.** The gold defects are author-authored; a second reviewer should check the clean/defective distinction before expansion.

## 9. Decision

**Do not expand this version.** The false-pass rate is 0.0 across 18 defective trials. The benchmark correctly separates clean from defective, but the defects are too easy.

If the direction continues, make the defective deliverable **subtler**, not longer:

- Start from the clean memo and change one decision-critical fact: remove the cohort split, omit the effective-before-signature sequence, or recommend launch without the configuration update.
- Keep the format, citations, and tone intact.
- Use one material defect per deliverable, not five.
- Add a clean control that explicitly answers every assignment question.
- Test on Qwen and Gemini first; escalate only if they false-pass.

That is the version that could reveal surface compliance. The current result is a useful negative: the models are not fooled by obvious defects.

## 10. Artifacts

- Tasks: `tasks/harbor/audit/{retention,incident}-{clean,defective}/`
- Oracle: `harbor run -p tasks/harbor/audit -a oracle` → 4/4 at 1.000
- Regraded results: `tasks/harbor/audit/results/audit_qwen.json`, `audit_gemini.json`, `audit_gpt.json`
- Raw audits: `jobs/audit_*` (gitignored; representative audits to be copied under `results/` if needed)
- Scorer: `tasks/harbor/audit/*/tests/score.py`
- Agent: `harbor_agents/host_audit_agent.py`
