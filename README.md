# D1-S Pilot: Warrant Maintenance in Organizational Briefs

This is the pilot for a Micro1 Eval Hackathon submission. It tests whether models preserve the limits of what a source pack establishes when they turn the sources into a multi-claim organizational deliverable.

**Status: pilot complete. NO-GO for expanding this design.** The cheap-model gate scored 100% on the open production condition, and no recognition-production gap appeared. See `PILOT_REPORT.md` for the evidence and the recommendation.

The benchmark is independently authored. It does not import, call, or depend on Atlas code, services, datasets, or infrastructure. All organizations, people, documents, dates, and numbers are synthetic.

## What is here

```
tasks/build_tasks.py     # builds T1.json and T2.json
tasks/T1.json            # retention / contract-amendment task
tasks/T2.json            # incident-investigation task
src/prompts.py           # recognition, closed-form production, open production, oracle
src/provider.py          # OpenCode Zen client (stdlib only)
src/grader.py            # deterministic grader, no LLM judge
src/reference.py         # reference outputs from the gold
src/run_pilot.py         # harness
src/regrade.py           # re-grade saved outputs without model calls
tests/test_grader.py     # grader self-tests
runs/                    # raw model responses (JSONL + per-call JSON)
results/                 # graded results and summary table
```

## Provider

The pilot uses the **OpenCode Zen** OpenAI-compatible endpoint:

```
OPENCODE_BASE_URL=https://opencode.ai/zen/v1
OPENCODE_API_KEY=<OpenCode Go key>
OPENCODE_SESSION=<routing session id>
```

The credential is read from `.env`, which is gitignored. `.env.example` lists the variable names only. No key is printed, logged, or included in any artifact.

Models actually used (verified against the endpoint):
- `opencode-go/deepseek-v4.1-flash` (cheap-model gate)
- `opencode-go/qwen3.8-flash` (cheap-model gate)
- `opencode-go/gpt-6-luna`
- `opencode-go/gemini-4-argon`
- `opencode-go/claude-haiku-5-5`

Claude Opus/Sonnet were not available with the supplied credentials: the Zen path returned `402 Insufficient account funds`, and the Go catalog returned `Model is unavailable` for Opus/Sonnet. The pilot therefore does not claim a frontier-Anthropic result.

## Run

```bash
python3 tasks/build_tasks.py
PYTHONPATH=. python3 -m unittest discover -s tests -v

# no API calls; checks the grader end to end
PYTHONPATH=. python3 -m src.run_pilot --dry-run --trials 1 \
  --models test/model --conditions recognition production

# cheap-model open production gate
PYTHONPATH=. python3 -m src.run_pilot --conditions production_open --trials 3 \
  --models opencode-go/deepseek-v4.1-flash opencode-go/qwen3.8-flash

# re-grade saved outputs after a gold change (no API calls)
PYTHONPATH=. python3 -m src.regrade runs/pilot_open_cheap.jsonl \
  --out results/pilot_results_open_cheap_regraded.json
```

## Grading

The grader parses structured JSON and scores, per claim or item:

- answer/verdict (0.6)
- evidence set (0.3; exact = 1.0, superset = 0.5, wrong = 0)
- qualifier (0.1; required terms must appear)

It tracks, separately: evidence-identification failure, evidence-correct/conclusion-wrong, dropped qualifier, temporal overreach, scope generalization, unsupported synthesis, draft-as-fact, unsupported additional assertion, and internal inconsistency. The summary is checked for required terms and forbidden overclaims. No LLM judge.

`tests/test_grader.py` covers reference outputs, always-supported and always-insufficient baselines, missing qualifiers, wrong evidence, superseded values, unsupported synthesis, missing/extra/duplicate items, malformed JSON, and inconsistency rules.

## Result

The valid open production condition (no answer options, model formulates its own conclusions) scored **100% answer accuracy** for both cheap models (72 items each). The recognition baseline was also at ceiling once provider/parse failures were separated. The pilot therefore does **not** establish a warrant-maintenance limitation. See `PILOT_REPORT.md`.

## Harbor long-horizon task

The next pilot is a Harbor task at `tasks/harbor/board-brief/`:

- 24 synthetic sources, 13 findings, exactly 10 sections, 1,500–2,000 words.
- Deterministic 110-point scorer normalized to a 0–1 reward, with caps for prohibited overclaims and invalid findings JSON.
- Oracle passes at reward 1.0.
- A custom `HostBriefAgent` runs the OpenCode Go endpoint inside Harbor because the built-in OpenCode CLI path bills the Zen account, which has no funds here.

See `tasks/harbor/board-brief/README.md` for the task and run commands.

## Harbor long-horizon pilot result

The Harbor task at `tasks/harbor/board-brief/` is built and verified:

- Oracle: **1.000**.
- Qwen 3.8 Flash clean run: **1.000** (1,924-word brief, 13/13 findings, 10/10 sections, all citations, no forbidden overclaims, no invented numbers).
- Qwen 3.8 Flash first run: **0.927** (17 words over the 2,000 limit; two grader false fails, since fixed).
- DeepSeek V4.1 Flash: empty content because the output budget was consumed by reasoning tokens.

The clean transcript is in `tasks/harbor/board-brief/results/run2_qwen/`, and the full report is `tasks/harbor/board-brief/PILOT_REPORT.md`.

**Recommendation: NO-GO on expanding this task as written.** The instruction enumerates the 13 findings, which turns the task into a checklist and lets a cheap model score 1.0. If the direction continues, remove the enumerated findings and require the model to select the material facts itself.

## Run history

`RUNS.md` records every pilot run, the models used, the scores, the failures, the cost/runtime, and the decision for each pilot. Review it before the individual reports.

## Surface-compliance audit pilot

`tasks/harbor/audit/` is the new pivot: four Harbor tasks (two scenarios × clean/defective) that ask whether a completed memo is fit for purpose, not whether facts can be retrieved. Oracle 4/4 at 1.000; Qwen, Gemini, and GPT-6 Luna all showed **zero false passes** on the obviously defective memos, so the pilot is a negative result at this defect difficulty. See `tasks/harbor/audit/PILOT_REPORT.md`.
