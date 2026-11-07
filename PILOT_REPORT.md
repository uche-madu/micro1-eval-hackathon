# D1-S Pilot Report

**Date:** 7 November 2026. **Status:** pilot complete. **Recommendation: NO-GO** on expanding this design.

## 1. Executive summary

The pilot tested whether models preserve the limits of what a source pack establishes when they turn the sources into a multi-claim organizational deliverable.

The result is negative for the hypothesis as operationalized here:

- The **open production** condition (no answer options; the model formulates its own conclusions) scored **100% answer accuracy** for both cheap models: DeepSeek V4.1 Flash 72/72 and Qwen 3.8 Flash 72/72.
- The **closed-form production** condition scored **100%** for all four models tested (288/288 item judgments), but it gave multiple-choice options and is therefore not a valid test of the hypothesis.
- **Recognition** was also at ceiling once provider/format failures were separated: GPT-6 Luna 0.979, Gemini 4 Argon 0.958, Qwen 1.000, Claude Haiku 0.938, DeepSeek 0.833 (the DeepSeek figure is one empty provider response, not 12 wrong answers).
- There is **no 20-point recognition-versus-production gap**. The gap is approximately zero, and the few recognition errors are **over-qualification** (the model adds a qualifier where none is needed), not over-assertion.
- The only apparent production failure (T2 P9) was a **grader false fail**: the models returned the full remediation from I3, while the gold accepted only two of its three clauses. After correcting the gold, the open production score rose from 0.958 to 1.000.

**Conclusion:** this task is too easy for current cheap models. It does not establish a warrant-maintenance limitation. Running frontier models on the same tasks would only confirm a ceiling and would waste credits. Stop, do not expand.

## 2. What was built

An isolated, standalone project at `~/micro1-eval-hackathon`:

- **Two synthetic tasks**, each with 12 sources, 12 recognition claims, and 12 production items:
  - **T1 — retention/contract amendment:** base policy, EU addendum, signed amendment effective before signature, unsigned draft, stale system export, public trust page, backup schedule, audit note, board minutes, informal emails. Tests authority, effective dates, cohort scope, superseded values, and a material EU exception.
  - **T2 — incident investigation:** two separate incidents, distinct causes, a draft postmortem that merges them, an executive email asking for a single story, a status export that auto-fills the wrong cause, an approved impact report, and an unapproved remediation plan. Tests unsupported synthesis, draft-as-fact, causal overreach, and authority.
- **Four conditions:** recognition (adjudicate supplied claims), closed-form production (answer options), open production (free-text answers, no options), oracle evidence, oracle + true competing passages, and explicit decision procedure.
- **Deterministic grader:** structured JSON, per-item answer/verdict, evidence set, qualifier; separate failure tags for evidence identification, evidence-correct/conclusion-wrong, qualifier drop, temporal overreach, scope generalization, unsupported synthesis, draft-as-fact, unsupported additional assertion, and internal inconsistency. No LLM judge.
- **Grader validation:** 13 unit tests covering reference outputs, always-supported and always-insufficient baselines, missing qualifiers, wrong evidence, superseded values, unsupported synthesis, missing/extra/duplicate items, malformed JSON, and inconsistency rules. All pass.
- **Raw outputs preserved** under `runs/raw/`, one JSON file per call, plus JSONL run logs. No response was discarded.

All organizations, people, documents, dates, and numbers are synthetic. No Atlas, Veridane, HI-05, customer, or employer material is used. The project does not depend on Atlas code, services, datasets, or infrastructure.

## 3. Provider and models

The pilot used the **OpenCode Zen** OpenAI-compatible endpoint at `https://opencode.ai/zen/v1` with the OpenCode Go credential and an `x-opencode-session` header.

Models actually used and verified:

| Model | Role | Notes |
|---|---|---|
| `opencode-go/deepseek-v4.1-flash` | cheap gate | 100% open production |
| `opencode-go/qwen3.8-flash` | cheap gate | 100% open production |
| `opencode-go/gpt-6-luna` | stronger comparison (closed-form run) | 100% closed-form production |
| `opencode-go/gemini-4-argon` | stronger comparison (closed-form run) | 100% closed-form production |
| `opencode-go/claude-haiku-5-5` | smaller comparison (closed-form run) | 100% closed-form production |

**Opus/Sonnet were not available with the supplied credentials.** The Zen path returned `402 Insufficient account funds`; the Go catalog returned `Model is unavailable` for both. This is a provider/account limitation, not a model result. The pilot does not claim an Anthropic-frontier finding.

**Consumption:** 152 OpenCode calls across the pilot (including exploratory and smoke calls), total reported `list_cost` **$0.545** and Go `allowance` **$1.169**; actual charge $0 because billing source is the Go plan. The final cheap-model gate was 18 calls. Frontier models were not run on the open production condition because the cheap models already saturated it.

## 4. Results

Full table in `results/summary_table.md`. Key rows:

| Run | Model | Condition | Items | Answer acc | Strict | Overreach | Signature | Parse errors |
|---|---|---|---:|---:|---:|---:|---:|---:|
| open production | DeepSeek V4.1 Flash | production_open | 72 | **1.000** | 0.597 | 0 | 0 | 0 |
| open production | Qwen 3.8 Flash | production_open | 72 | **1.000** | 0.528 | 0 | 0 | 0 |
| closed-form | GPT-6 Luna | production | 72 | 1.000 | 0.667 | 0 | 0 | 0 |
| closed-form | Gemini 4 Argon | production | 72 | 1.000 | 0.458 | 0 | 0 | 0 |
| closed-form | Claude Haiku 5.5 | production | 72 | 1.000 | 0.417 | 0 | 0 | 0 |
| closed-form | Qwen 3.8 Flash | production | 72 | 1.000 | 0.472 | 0 | 0 | 0 |
| recognition | GPT-6 Luna | recognition | 48 | 0.979 | 0.646 | 0 | 1 | 0 |
| recognition | Gemini 4 Argon | recognition | 48 | 0.958 | 0.458 | 2 | 2 | 0 |
| recognition | Qwen 3.8 Flash | recognition | 48 | 1.000 | 0.625 | 0 | 0 | 0 |
| recognition | Claude Haiku 5.5 | recognition | 48 | 0.938 | 0.583 | 3 | 3 | 0 |
| recognition | DeepSeek V4.1 Flash | recognition | 72 | 0.833 | 0.597 | 0 | 0 | 1 |

**Strict scores are lower than answer accuracy for a non-substantive reason:** the models often cite extra corroborating sources. The grader gives evidence credit for an exact set, half credit for a superset, and zero for a wrong set. A superset is not a factual error; it is evidence-precision over-inclusion. The primary metric is answer accuracy, and it is at ceiling.

**Recognition errors are over-qualification, not overreach:**

- Gemini, T1 C9 ("public trust page shows the current EU period"): gold CONTRADICTED, model SUPPORTED_WITH_QUALIFIER.
- Claude Haiku, T1 C2 and C11: gold SUPPORTED, model SUPPORTED_WITH_QUALIFIER.
- GPT-6 Luna, T1 C7 ("backups are retained for 35 days"): gold SUPPORTED, model SUPPORTED_WITH_QUALIFIER.

These are the opposite of the hypothesised failure: the model adds a qualifier where none is needed. They account for 1–3 items out of 48 per model and do not appear in production.

**Open production** outputs are correct and concise. Representative DeepSeek T1 summary:

> Signed Amendment A controls EU retention for accounts opened on or after 1 January 2026, setting 18 months effective 1 March 2026; accounts opened before that date remain at 12 months. The system-of-record export and public trust page still show 12 months and are stale for 2026 accounts. Draft Amendment B is unsigned and has no effect, while standard retention is 24 months and backups are retained 35 days outside the Enterprise Data Retention Policy.

Representative Qwen T2 summary:

> The approved incident records show two distinct March 2026 outages: INC-031 lasted 75 minutes and was caused by an expired TLS certificate, while INC-032 lasted 45 minutes and was caused by a failed rollback of CHG-441. Customer impact totals 15,500 failed transactions across the two incidents. The executive email's single-event description is not supported by the incident records, and the remediation plan remains unapproved.

Both preserve the qualifiers, the effective date, the cohort scope, the distinct causes, and the draft status.

## 5. Failure breakdown

| Failure | Count | Classification | Evidence |
|---|---:|---|---|
| Truncated JSON at `max_tokens=2200` | several in the first full run | **Harness limitation** | Recognition/oracle outputs cut mid-JSON; rerun at 6000 removed them |
| Empty provider response | 1 (DeepSeek T1 recognition t2) | **Provider failure** | `empty_content` after two attempts; 12 items scored 0; parsed calls were correct |
| Haiku procedure parse error | 1 | **Format/provider** | One of two T2 calls; not a reasoning error |
| T2 P9 gold too narrow | 3 per cheap model in the raw run (6 total) | **Grader false fail** | Models returned the full I3 remediation; gold accepted only two clauses |
| Evidence superset | many | **Grader strictness**, not factual error | Models cite corroborating sources in addition to the decisive one |
| Summary required term "different" vs "distinct" | several T2 summaries | **Grader false fail** | Paraphrase; required terms reduced to "two" for the pilot |
| Over-qualification in recognition | 1–3 per model | **Model behaviour**, but opposite to the hypothesis | Models add a qualifier where the gold says SUPPORTED |

**No production overreach was observed.** `overreach = 0` and `signature = 0` for every production and open-production run. The hypothesised failure — identify the evidence, then assert more than it warrants — did not appear.

## 6. What this establishes and what it does not

**Establishes:**

- For these two tasks, with explicit authority notes and a compact source pack, cheap models can identify the decisive evidence, preserve qualifiers, respect effective dates and cohort scope, detect draft status, and avoid unsupported synthesis.
- A recognition-versus-production gap is not present at this difficulty. The open production condition is not harder than recognition for these models.
- The deterministic grader works on reference and adversarial outputs. The failures it produced were mostly grader-side (P9 gold, summary paraphrase, evidence supersets), which is itself a useful finding: an evaluator can manufacture a false limitation if the gold is too narrow.

**Does not establish:**

- That models never over-assert. The task is too easy to test the hypothesis; a null result on an easy task is not evidence of absence.
- That frontier models would fail a harder version. They were not run on the open condition because the cheap models saturated it.
- That the result generalizes beyond two tasks, one domain pair, five models, and a compact source pack.
- That Opus/Sonnet would behave differently. They were unavailable.

## 7. Limitations

- **Two tasks only.** n = 24 claims and 24 production items per task; per-class cells are small.
- **Compact source packs.** 12 short documents per task; the models may have found the decisive evidence easily. Volume and distribution were not stressed.
- **Closed-form production gave options.** It is not a valid test of independent formulation; the 100% result there is a ceiling artifact, not a finding.
- **Open production answers are short.** The model formulates the conclusion but not a long deliverable. The task does not test long-horizon consistency.
- **Model availability.** Opus/Sonnet could not be tested; the Anthropic datapoint is Haiku only.
- **Provider variance.** One DeepSeek empty response and one Haiku parse error; these are recorded, not hidden.
- **No human second labeler.** The gold is author-authored against a written decision procedure. A second expert would strengthen the claim; this pilot is a design gate, not a publication.

## 8. Decision gate

The design gate required a **20-percentage-point recognition-versus-production gap**, with the gap not explained by evidence identification, ambiguity, or formatting.

Observed:

- DeepSeek: recognition 0.833 (one empty provider response; parsed calls correct) vs open production 1.000 → gap ≤ 0.
- Qwen: recognition 1.000 vs open production 1.000 → gap 0.
- Closed-form production: 1.000 for all models; not a valid ceiling test.

**Gate result: FAIL.** There is no meaningful gap, and the residual errors are provider/format or grader false fails. The hypothesis is not supported by this pilot.

## 9. Recommendation

**NO-GO on expanding D1-S as designed.** Do not add tasks or run frontier models on this construct. More of the same will produce another ceiling.

If the project continues, the next experiment must change the difficulty axis, not the sample size:

1. **Long-horizon constrained generation.** Ask the model to write a 1,500–2,000-word brief with 20–30 checkable factual and formal constraints, not 12 short answers. Grade constraint coverage, qualifiers, citations, and internal consistency. This is the closest test of the production failure the hypothesis describes.
2. **Document volume and distribution.** 30–50 documents with the decisive evidence split across several sources and buried among true-but-irrelevant distractors. Keep the gold fixed and vary only the pack. This tests evidence management, not warrant.
3. **Multi-turn state tracking.** Six to ten turns, each adding or updating a constraint; grade the final state and consistency. This tests whether the model maintains a coherent situation model, which the compact tasks do not.

Any of these should be piloted first on **DeepSeek V4.1 Flash and Qwen 3.8 Flash**. Only if a cheap model fails should the experiment escalate to GPT-6 Luna, Gemini 4 Argon, or a funded Opus/Sonnet. The current evidence does not justify spending frontier credits.

**Bottom line:** the pilot did its job. It falsified the easy version of the hypothesis before we built a submission around it. The honest finding is that compact evidence adjudication and short structured production are not a frontier-model limitation; the remaining opportunity, if any, is in long-horizon production or volume, not in more claim-classification tasks.
