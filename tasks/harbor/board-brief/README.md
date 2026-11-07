# Harbor task: micro1/board-brief

A long-horizon, evidence-grounded generation task. The agent receives a 24-document source pack, a brief specification, and must produce:

- `/output/brief.md` — 1,500–2,000 words, exactly 10 required sections.
- `/output/findings.json` — exactly 13 findings, each with a statement, evidence IDs, and a material qualifier.

The task tests **warrant maintenance in production**: whether the model preserves effective dates, cohort scope, qualifiers, draft status, and source authority while composing a long deliverable, instead of over-asserting from true but insufficient evidence.

## Why it is hard

The source pack contains a signed amendment effective before signature, a cohort-specific EU retention rule, an unsigned draft, a stale system export, a stale public page, an executive email that asks for a misleading simplification, two distinct incidents with different causes, a draft postmortem that merges them, and an unapproved remediation plan. A correct brief must keep all of those limits; a fluent brief can easily drop one.

The task also requires the model to satisfy 13 finding-level constraints, 10 section headings, a word count, citations for every finding, no invented figures, and no prohibited overclaims. That is a long-horizon consistency problem, not a single-answer quiz.

## Files

```
instruction.md                  # task prompt and full rubric
task.toml                       # Harbor config
environment/Dockerfile          # python:3.13-slim + source pack
environment/data/sources/       # 24 synthetic Markdown sources
solution/reference_brief.md     # oracle brief
solution/reference_findings.json
solution/solve.sh
tests/test.sh                    # runs score.py, writes reward.txt
tests/score.py                   # deterministic 110-point scorer, normalized to 0-1
tests/gold.json                  # finding/section/forbidden-phrase gold
tests/sources.json               # source texts + dates for numeric whitelist
tests/fixtures/                  # self-test fixtures (reference + bad)
build.py                         # regenerates sources/gold from the pilot tasks
```

## Scoring

The scorer writes `/logs/verifier/reward.txt` as a float 0–1 and `score.json` with per-check detail. It uses no LLM judge.

- 52 points: 13 findings × (facts 2, evidence 1, qualifier 1).
- 10 points: the 10 required level-2 headings.
- 5 points: word count.
- 10 points: finding IDs and evidence citations in the prose.
- 8 points: no prohibited overclaims.
- 5 points: no invented numbers (every number must appear in the source pack).
- 3 points: no evaluation/grader leakage.
- 5 points: consistency (no duplicate IDs, no contradictory overclaim).
- 5 points: output and JSON schema.

Caps: any prohibited overclaim caps the score at 0.60; invalid/missing `findings.json` caps at 0.50. Partial credit is intentional.

## Run

Oracle (reference solution):

```bash
cd ~/micro1-eval-hackathon
harbor run -p tasks/harbor -a oracle --yes
```

The oracle passes at reward 1.0.

Model run uses the custom `HostBriefAgent`, because the built-in OpenCode CLI path bills the Zen account (which has no funds here) and the Go credential works through the raw OpenAI-compatible endpoint:

```bash
KEY=$(grep -m1 '^OPENCODE_API_KEY=' .env | cut -d= -f2-)
SESSION=$(grep -m1 '^OPENCODE_SESSION=' .env | cut -d= -f2-)
PYTHONPATH=. harbor run -p tasks/harbor \
  -a "harbor_agents.host_brief_agent:HostBriefAgent" \
  -m opencode-go/qwen3.8-flash \
  --ae "OPENCODE_API_KEY=$KEY" \
  --ae "OPENCODE_BASE_URL=https://opencode.ai/zen/v1" \
  --ae "OPENCODE_SESSION=$SESSION" \
  --yes
```

The custom agent reads `/data/sources`, calls the OpenCode Go endpoint, writes the two output files into the container, and lets Harbor run the same verifier.

## Local checks (no Docker)

```bash
cd tasks/harbor/board-brief
python3 tests/score.py --selftest
```

Expected: reference 100.0, bad-overclaim 60.0 (capped), bad-malformed 49.091.
