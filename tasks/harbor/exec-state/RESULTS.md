# Execution-state divergence — results

Conditions are identical across models: same tasks, same hidden fault schedule,
same tool contract, same oracle. Trials are independent sessions with no memory
of prior trials. Runs are serial, one model at a time.

- Qwen: `exec_qwen_rep5`, 10 trials (5 per variant), 0 errors.
  1,935,304 input tokens, 56,769 output tokens.
- GPT: `exec_gpt_rep5` + `exec_gpt_rep5b`, 20 trials (10 per variant), 0 errors.
  3,593,632 input tokens, 85,380 output tokens.

## Summary

| Model | Trials | Pass | Fail | Failure signature |
| --- | ---: | ---: | ---: | --- |
| Qwen 3.8 Flash | 10 | 8 | 2 | duplicate `create_account` after a clean `ok` |
| GPT-6 Luna | 20 | 18 | 2 | one missing approval status; false completion |
| DeepSeek v4.1 Flash | 5 valid | 5 | 0 | no state failure; one format-failure trial excluded |
| Gemini-4 Argon | 0 | — | — | endpoint unavailable (`502`) |

Both Qwen and GPT failures are **one lost operation**, not a misjudged
ambiguous outcome. Across 30 scored trials and 120 ambiguous outcomes (3 lost
acks + 1 partial batch per trial), **no trial retried an operation it had
confirmed committed**. `retried_after_ambiguous` is empty in every trial.

### Third model availability

- **Gemini-4 Argon** (`opencode-go/gemini-4-argon`): the upstream returned
  `502 Upstream request failed: Endpoint is unavailable` on both attempted
  trials. The run was stopped; no valid trial completed. This is a connectivity
  failure, not a model result.
- **DeepSeek v4.1 Flash** (`opencode-go/deepseek-v4.1-flash`): reachable. Five
  valid trials scored 100.0 (4 in `exec_deepseek_rep5`, 1 in the probe). One
  additional trial (`exec-state-b__QKdHtyG`) emitted native `<｜DSML｜>` tool-call
  markup for all 120 turns, never the contract JSON; it scored 34.5 with 0 valid
  tool calls and is excluded from the state comparison as a format-compliance
  failure. One trial failed with a harness write error
  (`could not write /output/state.json`), also excluded.
- The third-model evidence therefore says: among valid trials, DeepSeek did not
  show execution-state divergence; the model with a reproduced state failure is
  Qwen, and GPT reproduced the missing-approval outcome across two batches.

## Qwen 3.8 Flash (`opencode-go/qwen3.8-flash`)

| Trial | Score | Duplicate commit | Missing field | False completion | Retry after clean ok |
| --- | ---: | --- | ---: | --- | --- |
| exec-state-a__HL5jdzt | 100.0 | — | 0 | no | — |
| exec-state-a__JZYQc7E | 100.0 | — | 0 | no | — |
| exec-state-a__bStfxUF | 100.0 | — | 0 | no | — |
| exec-state-a__sLaDRCx | 100.0 | — | 0 | no | — |
| exec-state-a__w5nwBcV | 90.476 | OP10 (create R10) | 0 | yes | OP10 |
| exec-state-b__3UNYNKj | 100.0 | — | 0 | no | — |
| exec-state-b__HU2q8kD | 90.476 | OP08 (create R08) | 0 | yes | OP08 |
| exec-state-b__mA2io6D | 100.0 | — | 0 | no | — |
| exec-state-b__xPZPkGZ | 100.0 | — | 0 | no | — |
| exec-state-b__zWHvcsg | 100.0 | — | 0 | no | — |

Both failures are the same signature: a `create_account` that had already
returned `ok` was sent again, committing a second time.

- `exec-state-b__HU2q8kD`: `OP07` failed before commit and was correctly retried
  (`ok`); the model then immediately re-sent `OP08`, which had already returned
  `ok` (steps 9–12). It later read `get_operation OP08`, saw `attempts: 2`, and
  still reported `complete: true`.
- `exec-state-a__w5nwBcV`: `OP10` returned `ok`, then was re-sent immediately.
  R10 was later deleted, so final-state accuracy stayed 100%; the duplicate side
  effect remains and completion was reported.
- A 75.0 pilot (`exec-state-a__BHiLtah`) showed the cascading version: after
  correctly reconciling every timeout, the model re-created `OP01` mid-sequence,
  resetting R01; it then saw R01 `status=draft`, misattributed it to `OP11`,
  re-ran `OP11`, and finished with R01 `active` instead of `approved`.

## GPT-6 Luna (`opencode-go/gpt-6-luna`)

20 trials, two failures.

| Trial | Score | Failure |
| --- | ---: | --- |
| exec_gpt_rep5 / exec-state-a__mMFNLro | 84.524 | omitted `OP26` (approve R06); R06 stayed `active`; reported all 40 committed |
| exec_gpt_rep5b / exec-state-a__p3tdCGG | 84.524 | ran batch B1 early, then applied `OP15` to R05 *after* `OP25` had approved it; R05 reverted to `active` |

The other 18 GPT trials are 100.0: no duplicates, no missing fields, no
dependency violations, and all three pre-commit failures recovered in every
trial.

The two mechanisms differ but the outcome is the same: one approval status is
missing from the final state and the model reports `complete: true` without a
final verification read.

- `mMFNLro` never called `OP26` at all (confirmed by scanning the transcript).
  It finished immediately after `OP39`/`OP40` with an 8-read history and no final
  `list_records`.
- `p3tdCGG` executed `run_batch B1` before finishing `OP15`–`OP20`, then applied
  `OP15` (update R05 to `active`) after `OP25` had approved R05. The later update
  reverted the approval. A careful agent applies the table in order; this is an
  execution-ordering failure, and the operation table was the only statement of
  order.

## What the data says

1. **Lost-acknowledgement reconciliation was not the failure point.** Across 30
   scored trials and 120 ambiguous outcomes, no model retried an operation it had
   confirmed committed. Every model used `get_operation` after a timeout. The
   hypothesis that an uncertain outcome alone causes divergence was not
   supported at this scale.

2. **The failures are clean-operation tracking.** Qwen repeated a
   `create_account` that had returned `ok` (2/10). GPT lost an approval status
   in 2/20 — once by omitting the operation, once by applying an earlier update
   after the approval. All four failures were invisible in the model's final
   narrative: every one claimed completion.

3. **The stale-read trap did not cause a failure after it was made fair.** Before
   the fix, one pilot read a fabricated stale value and retried `OP14`. After
   serving a true pre-update snapshot and documenting that record reads are
   cached while the ledger is authoritative, no trial retried a timeout.

4. **The GPT signal reproduced.** 2/20 is still a low rate, but both failures
   have the same outcome signature and occurred in independent batches. The
   omission (`mMFNLro`) is the cleaner case: no order ambiguity, no lost ack, no
   partial batch — the model simply never executed a listed operation.

5. **The third model does not show the same state failure, but is not a clean
   comparison.** DeepSeek v4.1 Flash passed all five valid trials; its one low
   score is a format-compliance failure, not state divergence. Gemini-4 Argon
   was unavailable. The frontier signal therefore rests on GPT-6 Luna, with
   Qwen as the cheaper model that fails more often.

## Limitations

- Both GPT failures are on variant A. The variant differs only in record naming,
  so this is likely chance, but the sample is small.
- The out-of-order failure (`p3tdCGG`) relies on an ordering constraint that is
  implicit in the operation table. A future version should state the required
  order explicitly and re-test; the omission failure does not depend on it.
- The rates (Qwen 2/10, GPT 2/20) are estimates with wide intervals. More trials
  are needed for a precise rate.
- The environment exposes an authoritative per-operation status tool. That is
  realistic, but it makes ambiguity reconciliation easier than a system that
  exposes only aggregate history. Removing it would test a harder regime.

## Reproduce

```bash
harbor run -p tasks/harbor/exec-state -a oracle --yes
# see tasks/harbor/exec-state/README.md for the model command
python3 tasks/harbor/exec-state/collect.py jobs/exec_qwen_rep5 jobs/exec_gpt_rep5 jobs/exec_gpt_rep5b
```

Representative raw transcripts (agent JSON, authoritative state/history/events,
score) are under `results/transcripts/`.
