# Execution-state divergence — hardened v2 results

Baseline conditions are identical across models: same tasks, same hidden fault
schedule, same tool affordances, same oracle. Trials are independent sessions.
Runs are serial, one model at a time.

The v1 results remain in `tasks/harbor/exec-state/RESULTS.md` as historical
evidence; this file reports the corrected benchmark only.

## Design

40 operations against a persistent account store, with explicit enforced
dependencies and the same fault distribution as v1:

- lost acknowledgement after commit: OP03, OP14, OP36
- fail before commit: OP07, OP27, OP31
- partial batch: B1 = OP21–OP25, first 3 commit, last 2 fail
- stale cached read: first read of R04 after OP14 returns the true pre-update value
- dependency failure: OP32 requires OP27, explicit in the graph

The first batch attempt must be the full batch; a subset on the first attempt is
rejected and does not consume the partial fault. `list_records` is the current
full state; `get_record` is the cached observation. The operation ledger is
authoritative.

## Scoring dimensions

Incorrect final state (40), missing operations (15), duplicate operations (15),
dependency violations (10), false completion — state (5), false completion —
contract (5), verification any (5), verification final (5).

## Qwen 3.8 Flash (`opencode-go/qwen3.8-flash`)

Job `exec2_qwen_30`: 28 valid trials (15 attempts per variant; 1 DNS error and 1
hung container are infrastructure, not model results).

| Result | Trials | Detail |
| --- | ---: | --- |
| Pass (100) | 25 | no missing, duplicate, or dependency failure |
| Duplicate operation (90) | 2 | OP21, OP33 |
| Dependency violation (90) | 1 | batch B1 called before its prerequisites |

Failure signatures:

- `exec-state2-a__rYqjntk` (90.0): after the batch partial, Qwen read
  `get_operation OP21 → committed`, then re-issued `approve_account OP21`
  anyway. The final state was correct (idempotent approval) and Qwen reported
  complete. `duplicate_operations=1`, `false_completion_contract=true`.
- `exec-state2-b__S6J5xx7` (90.0): `OP33` returned `ok`, then was re-sent
  immediately. Qwen later read `attempts: 2` and continued; its summary says
  the ledger shows "a single committed effect", which is false.
  `duplicate_operations=1`, `false_completion_contract=true`.
- `exec-state2-b__GmcVfUR` (90.0): the first action was `run_batch B1`, before
  the create/update prerequisites. The environment rejected it as a dependency
  violation and did not consume the partial fault. Qwen recovered, reached the
  correct final state, and reported complete. `dependency_violations=1`.

Infrastructure failures (excluded from the model rate): one trial failed with
`URLError: Temporary failure in name resolution` at step 42; one trial hung
before its first model call and was stopped.

**Qwen reproduces operation-tracking failure**: 3/28 valid trials, with two
distinct signatures (duplicate after confirmed commit, and out-of-order batch).

## GPT-6 Luna (`opencode-go/gpt-6-luna`)

Jobs `exec2_gpt_30` and `exec2_gpt_30b`: 20 scored trials, 18 valid, 2
format/interface failures. The run was interrupted by server restarts after 20
scored trials; a hung 6-trial continuation was stopped.

| Result | Trials | Detail |
| --- | ---: | --- |
| Pass (100) | 5 | no defects |
| Missing final read (95) | 6 | dependency order correct, no final verification |
| Dependency violation + missing final read (85) | 5 | batch called before prerequisites |
| Dependency violation only (90) | 2 | recovered, correct final state |

Valid-trial core metrics:

- **0 duplicate operations**
- **0 missing operations**
- **0 incorrect final states**
- 7 dependency violations (batch called before its prerequisites)
- 11 trials with no read after the last write
- 2 format/interface failures, excluded: one trial emitted multiple
  concatenated JSON objects and then concluded the tools were unavailable; one
  looped on `list_records` for 160 turns. Both executed zero operations. These
  are contract/interface failures, not state-tracking failures.

**GPT did not reproduce the core operation-tracking failure** in 18 valid
trials. It completed the final state correctly, but frequently ignored the
explicit dependency order and skipped final verification.

## Opus 5.5 (`claude-opus-5-5` via OpenCode)

OpenRouter was attempted first and returned `402 Insufficient credits` on every
trial (the key is valid but the account has no credits). The OpenCode endpoint
exposes the same model as `claude-opus-5-5`; the probe scored 2/2 at 100.0.

| Batch | Trials | Score |
| --- | ---: | --- |
| probe | 2 | 2 × 100 |
| 30b | 6 | 6 × 100 |
| 30c | 6 | 6 × 100 |
| 30d | 6 | 6 × 100 |
| 30e | 4 | 4 × 100 |
| 30f | 6 | 6 × 100 |

**30/30 at 100.0.** No duplicate operations, no missing operations, no
incorrect final state, no dependency violations, and a final verification read
in every trial.

## Cross-model comparison

| Model | Valid trials | Pass | Duplicate ops | Missing ops | Incorrect state | Dependency violations | No final read | Format/interface failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 3.8 Flash | 28 | 25 | **2** | 0 | 0 | 1 | 0 | 0 (1 DNS, 1 hang) |
| GPT-6 Luna | 18 | 5 | **0** | 0 | 0 | 7 | 11 | 2 |
| Opus 5.5 | 30 | 30 | **0** | 0 | 0 | 0 | 0 | 0 |

## What the data says

1. **The corrected benchmark still reproduces Qwen's core failure.** Qwen
   repeated a successfully completed operation twice (OP21 after reading it
   committed; OP33 after a clean `ok`). The duplicate side effect is real even
   when the final field values remain correct, and Qwen reported completion.

2. **The frontier models do not reproduce the core failure at this scale.**
   GPT-6 Luna and Opus 5.5 had no duplicate operations, no missing operations,
   and no incorrect final states in 48 valid frontier trials. The v1 GPT failure
   that corrupted R05 cannot occur now because the environment rejects an
   earlier update after a later approval.

3. **GPT-6 Luna has a distinct dependency/verification weakness.** It repeatedly
   called the full batch before the create/update prerequisites, was rejected,
   and recovered. It also frequently finished without a read after the last
   write. The final state was correct, so this is a planning/verification
   failure, not state corruption.

4. **The v1 ordering defect was masking a task-design issue.** Enforcing
   dependencies both ways removed the specific v1 failure where an earlier
   update reverted a later approval. The remaining Qwen duplicates are not an
   ordering artifact; they are direct repeats of committed operations.

5. **The original hypothesis is not confirmed at the frontier.** In 18 GPT and
   30 Opus valid trials, no frontier model claimed completion over an incorrect
   final state, repeated a committed operation, or omitted a required one. The
   evidence supports a Qwen-specific duplicate-operation weakness and a
   GPT-specific dependency/verification weakness, not a frontier-wide
   execution-state divergence.

## Limitations

- GPT has 18 valid trials, not 30: 2 format/interface failures and one hung
  continuation. The conclusion is based on 18 valid trials.
- Opus is at 24 trials plus the final batch; the final count is reported below.
- The format failures are model contract violations (multiple concatenated JSON
  objects; a loop on `list_records`), not state failures. They are excluded from
  the state rate and reported separately.
- The environment exposes an authoritative per-operation ledger; ambiguity
  reconciliation is easier than in a system with only aggregate history.
- Server restarts, one DNS failure, and one hung container interrupted the runs;
  all such cases are separated from model state failures.

## Reproduce

```bash
python3 tasks/harbor/exec-state-v2/test_env.py
harbor run -p tasks/harbor/exec-state-v2 -a oracle --yes
python3 tasks/harbor/exec-state-v2/collect.py jobs/exec2_qwen_30 jobs/exec2_gpt_30 jobs/exec2_gpt_30b jobs/exec2_opus_30b jobs/exec2_opus_30c jobs/exec2_opus_30d jobs/exec2_opus_30e jobs/exec2_opus_30f
```

Representative raw transcripts are under `results/transcripts/`.

## Failure classification rule

A trial is an operation-tracking failure if it has any missing operation,
duplicate operation, or dependency violation, or if it reports complete over
such a defect. Harness/tool-interface failures (unparseable tool calls, container
write errors, endpoint errors) are reported separately and are not counted as
model state failures.
