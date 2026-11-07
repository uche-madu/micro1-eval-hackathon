# Harbor Long-Horizon Pilot Report

**Task:** `micro1/board-brief`  
**Date:** 7 November 2026  
**Status:** pilot complete. **Recommendation: NO-GO** on expanding this design.

## 1. Executive summary

The task was built in the guide's Harbor format and verified end to end.

- **Oracle:** reward **1.000**.
- **Cheap model (Qwen 3.8 Flash):**
  - Clean run: **reward 1.000**, 1,924 words, all 13 findings, all 10 sections, all citations, no forbidden overclaims, no invented numbers.
  - First run: **reward 0.927**, 2,017 words (17 over the limit), plus two grader false fails that were fixed.
- **DeepSeek V4.1 Flash:** produced no content because it spent the entire output budget on reasoning tokens. This is a reasoning-budget/provider issue, not a warrant failure.

The actual brief was reviewed. It preserves the EU cohort split, the effective-before-signature sequence, the unsigned draft status, the stale trust page and export, the backup scope, the two distinct incidents and their causes, the total impact, and the unapproved remediation plan. No ungraded overclaim was found.

**Conclusion:** a cheap model handles this long-horizon evidence task at ceiling. The task does not expose a meaningful warrant-maintenance limitation. Do not spend frontier-model credits on it.

## 2. What was built

A single Harbor task at `tasks/harbor/board-brief/`:

- **24 synthetic sources** (`D1`–`D12`, `I1`–`I12`) covering a retention/contract-amendment workstream and a March incident workstream.
- **Instruction:** write `/output/brief.md` (1,500–2,000 words, exactly 10 level-2 sections) and `/output/findings.json` (exactly 13 findings, each with statement, evidence IDs, and qualifier).
- **Why it is hard:** the source pack contains a signed amendment effective before signature, a cohort-specific EU rule, an unsigned draft, a stale system export, a stale public page, an executive email asking for a misleading simplification, two incidents with different causes, a draft postmortem that merges them, an auto-filled status-page cause field, and an unapproved remediation plan. A fluent brief can easily drop one of those limits.
- **Deterministic scorer:** `tests/score.py`, no LLM judge. 110 points normalized to 0–1. 52 points for the 13 findings, 10 for sections, 5 for word count, 10 for IDs/citations, 8 for no prohibited overclaims, 5 for no invented numbers, 3 for no evaluation leakage, 5 for consistency, 5 for schema. Caps: any prohibited overclaim caps at 0.60; invalid findings JSON caps at 0.50.
- **Grader self-test:** reference **100/100**, bad-overclaim **60/100** (capped), malformed **50/100** (capped). The reference solution passes every check.

## 3. Harbor execution

Harbor 0.23.0 with Docker.

- `harbor run -p tasks/harbor -a oracle` → **1.000**.
- The built-in `opencode` CLI path bills the Zen account and returned `402 Insufficient account funds`; the Go credential works through the raw OpenAI-compatible endpoint. A small custom Harbor agent, `harbor_agents.host_brief_agent:HostBriefAgent`, reads `/data/sources`, calls the Go endpoint, writes the two output files into the container, and lets Harbor run the task's own verifier. This is a Harbor agent and a Harbor verifier, not an external harness.

Model run:

```bash
PYTHONPATH=. harbor run -p tasks/harbor \
  -a "harbor_agents.host_brief_agent:HostBriefAgent" \
  -m opencode-go/qwen3.8-flash \
  --ae OPENCODE_API_KEY=... --ae OPENCODE_BASE_URL=https://opencode.ai/zen/v1 \
  --ae OPENCODE_SESSION=... --yes
```

## 4. Results

| Run | Model | Reward | Words | Findings | Sections | Citations | Overclaims | Invented numbers |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Oracle | reference | **1.000** | 1,648 | 13/13 | 10/10 | yes | none | none |
| 1 | Qwen 3.8 Flash | 0.927 | 2,017 | 11/13* | 10/10 | yes | none | none |
| 2 | Qwen 3.8 Flash | **1.000** | 1,924 | 13/13 | 10/10 | yes | none | none |

\* Run 1's two lost findings were grader false fails: F5 rejected the paraphrase "has not **been** updated", and F8 checked a redundant qualifier. Both were fixed. Run 1's remaining loss was the 17-word overrun. A corrected estimate for run 1 is 0.955, not a re-grade (the run-1 brief was not preserved).

**Cost:** run 2 used 3,870 prompt tokens and 47,656 output tokens (43,250 reasoning), list cost **$0.0225**, actual charge **$0** (Go plan). Runtime 25m48s.

## 5. Transcript review

The run-2 brief is at `results/run2_qwen/brief.md`; findings at `results/run2_qwen/findings.json`; score at `results/run2_qwen/score.json`.

Representative correct behavior:

- F1/F2: "For accounts opened on or after 1 January 2026, Amendment A sets the EU retention period at 18 months, effective 1 March 2026" and "accounts opened before 1 January 2026 remain at 12 months."
- F4: "Draft Amendment B is unsigned and not approved."
- F5/F6: "The public trust page snapshot does not reflect the current EU position" and "The system-of-record export is stale and is not controlling for EU retention."
- F7: "Backups are retained for 35 days and are out of scope of the Enterprise Data Retention Policy."
- F8: "Amendment A was signed on 5 May 2026 but is effective from 1 March 2026."
- F9/F12: "Two distinct incidents occurred in March 2026"; "The total failed transaction count was 15,500, and the incidents had different root causes."
- F13: "The remediation plan remains a draft and is not approved."

No sentence describes the incidents as one outage, both as certificate-caused, the draft as effective, the trust page as current, the export as controlling, or backups as covered. No invented number was found. The prose is repetitive and checklist-like, but it is factually disciplined.

## 6. What this establishes and what it does not

**Establishes:**

- A cheap model can produce a 1,900-word, 13-claim, 24-source brief that preserves every tested qualifier, effective date, cohort limit, draft status, and incident distinction.
- Harbor can run this task end to end with a deterministic verifier; the oracle is 1.0 and the verifier rejects known bad outputs.
- The remaining failure in the first run was formal (length), not warrant.

**Does not establish:**

- That the model never over-asserts. The task's instruction enumerates the 13 finding topics, which is a strong scaffold; the model fills a checklist rather than deciding what matters. This is a **construct-validity limitation**.
- That the result generalizes. One model, two trials, one domain pair, one prompt.
- That a harder version would also saturate. It might not; the next design should remove the scaffold.

## 7. Why this is still a useful negative result

The first D1-S pilot showed that compact adjudication is easy. This pilot shows that a **structured, long-horizon generation task with an enumerated finding list** is also easy for a cheap model. The model did not fail because it could not track the evidence; it tracked it correctly. The limitation, if it exists, is not in short or medium evidence handling.

The task's scaffold is the likely reason. The instruction tells the model exactly which 13 findings to produce and which 10 sections to use. A harder version should require the model to **select** the material findings, decide the structure, and cover the record without a checklist. That is where omission, overgeneralization, and unsupported synthesis are more likely.

## 8. Recommendation

**NO-GO on expanding this task as written.** Do not run frontier models on it; a cheap model already scores 1.0.

If the project continues, change one variable at a time and pilot on the cheap models first:

1. **Remove the enumerated findings.** Give only the 10-section requirement and the general topics. Require the model to select the 13 most material findings itself. The same gold applies; omission and wrong selection now count.
2. **Increase the output horizon.** 3,000–5,000 words, 30+ findings, 15 sections. The model must maintain the constraints longer.
3. **Increase the source volume.** 40–60 documents, with the decisive evidence split across several sources and buried among true distractors. Keep the gold fixed.
4. **Multi-turn state.** Six to ten turns, each adding or updating a constraint; grade the final brief and consistency.

Only escalate to GPT-6 Luna, Gemini 4 Argon, or a funded Opus/Sonnet if a cheap model fails one of those. The current evidence does not justify frontier spend.

**Bottom line:** the Harbor task is well-built, reproducible, and genuinely long-horizon, but it is not hard enough. The cheap model's 1.0 is the finding, and it is a negative one for D1-S.
