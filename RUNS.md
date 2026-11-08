# Run History

This repository contains two evaluation pilots built for the Micro1 Eval Hackathon. Both are negative results for the working hypothesis. The purpose of this file is to make every run reviewable without reconstructing it from the code.

## Repository map

| Path | What it is |
|---|---|
| `PILOT_REPORT.md` | Compact adjudication pilot (D1-S): design, results, failure breakdown, NO-GO |
| `tasks/T1.json`, `tasks/T2.json` | Two synthetic compact tasks (retention, incident) |
| `src/` | Compact-task harness, OpenCode client, deterministic grader |
| `runs/` | Raw model responses from the compact pilot, one JSON file per call plus JSONL logs |
| `results/` | Graded compact results and `summary_table.md` |
| `tasks/harbor/board-brief/` | Harbor long-horizon task, scorer, oracle, transcript |
| `tasks/harbor/board-brief/PILOT_REPORT.md` | Long-horizon pilot report and NO-GO |
| `harbor_agents/host_brief_agent.py` | Custom Harbor agent that calls the OpenCode Go endpoint |

## Provider and credential notes

- The working credential is the **OpenCode Go** key at `https://opencode.ai/zen/v1`, with an `x-opencode-session` header. It is read from `.env`, which is gitignored. `.env.example` lists names only.
- The **OpenCode Zen** key available in this environment returns `402 Insufficient account funds`; Opus and Sonnet also return `Model is unavailable` through the Go catalog. No frontier-Anthropic result is claimed.
- A few early exploratory calls used **OpenRouter** (`openai/gpt-6.1-terra`, `anthropic/claude-sonnet-5.5`, `google/gemini-4-argon`) before switching to OpenCode. They are preserved under `runs/` and are not used for the main claims.
- No key is present in any committed artifact. Job configs under `jobs/` are gitignored; Harbor stored masked keys only.

## Pilot 1 — compact adjudication (D1-S)

**Question:** can a model identify what individual sources establish, but fail to preserve those limits when producing a multi-claim deliverable?

**Tasks:** two synthetic tasks, 12 sources and 12 claims each.
- T1: EU retention, signed amendment effective before signature, cohort scope, unsigned draft, stale export, backup schedule.
- T2: two March incidents, distinct causes, draft postmortem that merges them, executive email asking for a single story.

**Conditions:** recognition (adjudicate supplied claims), closed-form production, open production (free-text answers, no options), oracle evidence, oracle + true competitors, explicit decision procedure.

**Models:** OpenCode Go `deepseek-v4.1-flash`, `qwen3.8-flash`, `gpt-6-luna`, `gemini-4-argon`, `claude-haiku-5-5`.

**Main results** (full table in `results/summary_table.md`):

| Run | Model | Condition | Items | Answer accuracy |
|---|---|---|---:|---:|
| closed-form | GPT-6 Luna | production | 72 | 1.000 |
| closed-form | Gemini 4 Argon | production | 72 | 1.000 |
| closed-form | Claude Haiku 5.5 | production | 72 | 1.000 |
| closed-form | Qwen 3.8 Flash | production | 72 | 1.000 |
| open production | DeepSeek V4.1 Flash | production_open | 72 | 1.000 |
| open production | Qwen 3.8 Flash | production_open | 72 | 1.000 |
| recognition | GPT-6 Luna | recognition | 48 | 0.979 |
| recognition | Gemini 4 Argon | recognition | 48 | 0.958 |
| recognition | Qwen 3.8 Flash | recognition | 48 | 1.000 |
| recognition | Claude Haiku 5.5 | recognition | 48 | 0.938 |
| recognition | DeepSeek V4.1 Flash | recognition | 72 | 0.833* |

\* The DeepSeek recognition figure includes one empty provider response (12 items); the parsed calls were correct.

**Finding:** no recognition-production gap. The open production condition, which does not give answer options, was solved at 100% by both cheap models. The few recognition errors were **over-qualification** (adding a qualifier where the gold says SUPPORTED), the opposite of overreach. The only apparent production failure was a grader false fail: the models returned the full remediation from I3, while the gold accepted only two of its three clauses. After correcting the gold, the open production score rose from 0.958 to 1.000.

**Decision:** NO-GO on expanding the compact design.

**Caveats from this pilot:**
- The first full run used `max_tokens=2200` and truncated some JSON; the rerun used 6000. The truncated run is preserved and is not used as a model failure.
- Evidence supersets lower the strict score but are not factual errors; the primary metric is answer accuracy.
- One DeepSeek empty response and one Haiku parse error are provider/format failures, not reasoning failures.

## Pilot 2 — Harbor long-horizon generation

**Task:** `micro1/board-brief`, built in the guide's Harbor format.
- 24 synthetic sources (`D1`–`D12`, `I1`–`I12`).
- `/output/brief.md`: 1,500–2,000 words, exactly 10 level-2 sections.
- `/output/findings.json`: exactly 13 findings, each with statement, evidence IDs, and material qualifier.
- Deterministic 110-point scorer normalized to 0–1, with caps for prohibited overclaims (0.60) and invalid findings JSON (0.50).

**Oracle:** `harbor run -p tasks/harbor -a oracle` → **1.000**.

**Model runs:**

| Run | Model | Reward | Detail |
|---|---|---:|---|
| 1 | Qwen 3.8 Flash | 0.927 | 2,017 words (17 over); two grader false fails (F5 paraphrase, F8 redundant qualifier), since fixed |
| 2 | Qwen 3.8 Flash | **1.000** | 1,924 words; 13/13 findings, 10/10 sections, all citations, no forbidden overclaims, no invented numbers |
| — | DeepSeek V4.1 Flash | no content | Spent the output budget on reasoning tokens and emitted empty content |

**Transcript:** `tasks/harbor/board-brief/results/run2_qwen/` (`brief.md`, `findings.json`, `score.json`, `host_brief.txt`). The brief preserves the EU cohort split, Amendment A's effective-before-signature sequence, Draft B's unsigned status, the stale trust page and export, the 35-day backup scope, the two distinct incidents and causes, the 15,500 total, and the unapproved remediation plan.

**Finding:** a cheap model scored 1.0. The task does not expose a warrant-maintenance limitation. The likely reason is the scaffold: the instruction enumerates the 13 finding topics, so the model fills a checklist rather than deciding what matters.

**Decision:** NO-GO on expanding this task as written.

## What the runs establish

- Compact claim adjudication is saturated for current cheap models.
- A structured 1,900-word, 13-finding, 24-source brief is also saturated when the finding topics are enumerated.
- The remaining opportunity, if any, is in **unscaffolded production** (the model selects the material facts itself), longer output, larger source volume, or multi-turn state. None of those has been run yet.

## How to review

1. Read `PILOT_REPORT.md` for the compact pilot and `tasks/harbor/board-brief/PILOT_REPORT.md` for the Harbor pilot.
2. For the compact pilot, start with `results/summary_table.md`, then inspect `runs/raw/` for the exact prompts and responses.
3. For the Harbor pilot, start with `tasks/harbor/board-brief/results/run2_qwen/score.json`, then read `brief.md` and `findings.json`.
4. Re-run the deterministic graders without any model calls:

```bash
# Compact grader self-tests
PYTHONPATH=. python3 -m unittest discover -s tests -v

# Harbor scorer self-test (reference 100, bad-overclaim 60, malformed 50)
cd tasks/harbor/board-brief && python3 tests/score.py --selftest
```

5. Re-run the Harbor oracle (Docker required):

```bash
cd ~/micro1-eval-hackathon
harbor run -p tasks/harbor -a oracle --yes
```

## Cost and runtime

- Compact pilot: 152 OpenCode calls, reported `list_cost` **$0.545**, Go `allowance` **$1.169**, actual charge **$0**.
- Harbor long-horizon run 2: 3,870 prompt tokens, 47,656 output tokens (43,250 reasoning), list cost **$0.0225**, actual charge **$0**; runtime **25m48s**.
- No Opus/Sonnet calls were made. Frontier credits were not spent because the cheap-model gate saturated.

## Pilot 3 — surface-compliance audit (new pivot)

**Question:** can models tell whether a completed deliverable is fit for purpose, or do they mistake surface compliance for substance?

**Design:** four Harbor tasks under `tasks/harbor/audit/` — two scenarios (EU retention, March incidents) × clean/defective. Each model sees one deliverable, the assignment, and the source pack. It returns `FIT`/`NOT_FIT` plus findings against a general defect taxonomy. No seeded defect list is shown.

**Oracle:** 4/4 tasks at **1.000**.

**Model results** (deterministic scorer; extra findings are recorded but not penalized):

| Model | Clean | Defective | False pass | False fail | Defects matched |
|---|---:|---:|---:|---:|---:|
| Qwen 3.8 Flash | 6/6, 100.00 | 0/6 pass, 68.57 | **0.000** | 0.000 | 2.83/5 |
| Gemini 4 Argon | 6/6, 100.00 | 0/6 pass, 75.24 | **0.000** | 0.000 | 3.33/5 |
| GPT-6 Luna | 3/6, 52.38 | 0/6 pass, 80.32 | **0.000** | 0.500 | 3.67/5 |
| DeepSeek V4.1 Flash | — | — | — | — | excluded: empty content (reasoning budget) |

**Finding:** the hypothesis was not supported at this defect difficulty. No model approved a defective deliverable. The clean controls mostly passed; GPT’s three `incident-clean` false fails exposed a legitimate ambiguity in that clean memo (it says “not ready to close” rather than “not closed,” and does not explicitly answer whether to approve the draft plan). The defective memos contain direct contradictions, so the pilot is a floor test, not a surface-compliance test.

**Decision:** do not expand this version. If the direction continues, start from the clean memo and introduce **one subtle decision-critical defect** — a missing cohort split, an omitted effective-before-signature fact, or a plausible recommendation that ignores one precondition — and add a clean control that answers every assignment question explicitly.

**Artifacts:** `tasks/harbor/audit/PILOT_REPORT.md`, `tasks/harbor/audit/results/audit_*.json`, and representative transcripts under `tasks/harbor/audit/results/transcripts/`.

The two earlier pilots remain frozen; see `FREEZE.md`.

## Pilot 4 — subtle-defect audit

**Question:** if the defective deliverable is the clean memo with one changed decision-critical sentence, does Qwen still catch it?

**Design:** four Harbor tasks under `tasks/harbor/audit-subtle/` — retention/incident × clean/subtle. The subtle memo is otherwise correct.

**Oracle:** 4/4 at **1.000**.

**Qwen 3.8 Flash:** **12/12 at 1.000** after correcting one why-term false negative (raw: 11×1.000, 1×0.8095). False pass **0**, false fail **0**.

- The 0.8095 trial caught the defect and explained it with "verify" / "rollback-script"; the gold accepted only "verification" / "root-cause." Re-graded to 1.000.
- The single changed recommendation still creates an internal contradiction with the memo body, so the model sees it.

**Decision:** stop. One model passing is enough to establish the difficulty; no higher model was run. If the direction continues, the next test must be **pure omission** or a plausible recommendation with an unstated assumption, not another wording change that contradicts the body.

**Artifacts:** `tasks/harbor/audit-subtle/PILOT_REPORT.md`, `tasks/harbor/audit-subtle/results/transcripts/`.

## Pilot 5 — pure-omission audit

**Question:** can a model notice a decision-critical fact that is absent from an otherwise correct deliverable?

**Design:** four Harbor tasks under `tasks/harbor/audit-omission/` — retention/incident × clean/omission. The omission deliverable is internally consistent; the defect is what it fails to say.

**Oracle:** 4/4 at **1.000**.

**Final results:**

| Model | Clean | Omission | False pass | False fail |
|---|---:|---:|---:|---:|
| Qwen 3.8 Flash | 5/5 | 5/5 | **0** | 0 |
| GPT-6 Luna | 5/5 | 5/5 | **0** | 0 |

**Correction that mattered:** the first clean incident memo said “the audit note treats the incidents as open,” which the audit note does not say. GPT false-failed that memo 5/5, and Qwen’s earlier 1/3 and 1/5 omission false passes were tied to the same flawed text. After correcting it to “closure is not established; the audit note does not record a closure decision,” both models passed every clean and omission trial. The early transcripts are preserved under `results/transcripts/early_qwen_false_pass/`; they are not hidden.

**Decision:** stop. Pure omission in this scenario is not a frontier limitation. The next credible axis is multi-turn state integrity, not another one-shot audit.

**Artifacts:** `tasks/harbor/audit-omission/PILOT_REPORT.md`, `results/transcripts/`.

## Pilot 6 — 10-turn state integrity

**Question:** can the model restate a constraint, then keep applying it after late updates — and does context size change that?

**Design:** two Harbor tasks under `tasks/harbor/state-integrity/` — `state-short` and `state-long`. Same 10 turns and 10 state updates; the long version pads each turn with neutral operational context.

**Oracle:** 2/2 at **1.000**.

**Qwen 3.8 Flash:**

| Condition | Trials | 1.000 | 0.952 | Final answers | Stale fields | Dissociation |
|---|---:|---:|---:|---:|---:|---:|
| Short | 3 | 3 | 0 | 18/18 | 0 | 0 |
| Long | 3 | 1 | 2 | 18/18 | 0 | 0 |

The 0.952s were the recall probe, not state application: the model answered `incident_4_march` with INC-032 facts instead of the draft’s certificate attribution, while its final Q4 was correctly `failed rollback`. No recall–compliance dissociation.

**Finding:** 10 turns and ~4k tokens are below the failure regime. Padding the same updates with neutral prose does not degrade final answers. The observed OpenCode/Claude Code failure likely needs 30–50 turns and/or tool/action state.

**Decision:** do not expand the 10-turn version; do not run GPT on it. Next: 30–50 turns with 20–30 updates, or agentic tool state.

**Artifacts:** `tasks/harbor/state-integrity/PILOT_REPORT.md`, `results/transcripts/`, `GAPS.md`.
