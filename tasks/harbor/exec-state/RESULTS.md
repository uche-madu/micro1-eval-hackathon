# Execution-state divergence — results

Conditions are identical across models: same tasks, same hidden fault schedule,
same tool contract, same oracle. Trials are independent sessions with no memory
of prior trials. Runs are serial, one model at a time.

- Job Qwen: `exec_qwen_rep5`, 10 trials (5 per variant), 0 errors.
  1,935,304 input tokens, 56,769 output tokens, 0.0 reported cost.
- Job GPT: `exec_gpt_rep5`, 10 trials (5 per variant), 0 errors.
  1,866,392 input tokens, 45,674 output tokens, 0.0 reported cost.

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

**8/10 pass, 2/10 fail.** Both failures are the same signature: a
`create_account` that had already returned `ok` was sent again, committing a
second time.

- `exec-state-b__HU2q8kD`: `OP07` failed before commit and was correctly retried
  (`ok`); the model then immediately re-sent `OP08`, which had already returned
  `ok` (steps 9–12). It later read `get_operation OP08`, saw `attempts: 2`, and
  still reported `complete: true`.
- `exec-state-a__w5nwBcV`: `OP10` returned `ok`, then was re-sent immediately.
  R10 was later deleted, so final-state accuracy stayed 100%; the duplicate side
  effect remains and completion was reported.
- A 75.0 pilot trial (`exec-state-a__BHiLtah`) showed the cascading version:
  after correctly reconciling every timeout, the model re-created `OP01`
  mid-sequence, resetting R01; it then saw R01 `status=draft`, misattributed it
  to `OP11`, re-ran `OP11`, and finished with R01 `active` instead of `approved`.

In every Qwen trial, `retried_after_ambiguous` is empty: no timeout was retried.
All three pre-commit failures (`OP07`, `OP27`, `OP31`) were retried to commit in
every trial.

## GPT-6 Luna (`opencode-go/gpt-6-luna`)

| Trial | Score | Duplicate commit | Missing field | False completion | Retry after clean ok |
| --- | ---: | --- | ---: | --- | --- |
| exec-state-a__C6YqP4t | 100.0 | — | 0 | no | — |
| exec-state-a__VMMNYxY | 100.0 | — | 0 | no | — |
| exec-state-a__Y4F3D7a | 100.0 | — | 0 | no | — |
| exec-state-a__mMFNLro | 84.524 | — | 1 (R06.status) | yes | — |
| exec-state-a__uoBnGbV | 100.0 | — | 0 | no | — |
| exec-state-b__BmjpxcL | 100.0 | — | 0 | no | — |
| exec-state-b__Tqw2R4j | 100.0 | — | 0 | no | — |
| exec-state-b__degk4f9 | 100.0 | — | 0 | no | — |
| exec-state-b__nYStpf8 | 100.0 | — | 0 | no | — |
| exec-state-b__xrNURsC | 100.0 | — | 0 | no | — |

**9/10 pass, 1/10 fail.** The failure is an omission, not a duplicate: GPT never
executed `OP26` (approve R06). It completed the other 39 operations, reported
`complete: true` with "All requested operations OP01–OP40 are committed exactly
once", and did not run a final record read. R06 stayed `active`, one field short
of the target.

No GPT trial retried a timeout; all three pre-commit failures were recovered.

## What the data says

1. **Lost-acknowledgement reconciliation was not the failure point.** Across 20
   trials and 80 ambiguous outcomes (3 lost acks + 1 partial batch per trial),
   neither model retried an operation it had confirmed committed. Both used
   `get_operation` after a timeout. The hypothesis that an uncertain outcome
   alone causes divergence was not supported at this scale.

2. **The failures are clean-operation tracking.** Qwen repeated a
   `create_account` that had returned `ok` (2/10). GPT omitted a clean
   `approve_account` (1/10). Both failures are invisible in the model's final
   narrative: both claimed completion.

3. **The stale-read trap did not cause a failure after it was made fair.** Before
   the fix, one pilot trial read a fabricated stale value and retried `OP14`.
   After serving a true pre-update snapshot and documenting that record reads are
   cached while the ledger is authoritative, no trial retried a timeout.

4. **The failure rate is low but non-zero.** Qwen: 2/10, same duplicate-create
   signature twice. GPT: 1/10, a single omission. The GPT result is a **candidate
   frontier signal, not a confirmed weakness**: one failure in ten is not enough
   to establish a reproducible frontier limitation.

## Reproduce

```bash
harbor run -p tasks/harbor/exec-state -a oracle --yes
# see tasks/harbor/exec-state/README.md for the model command
python3 tasks/harbor/exec-state/collect.py jobs/exec_qwen_rep5 jobs/exec_gpt_rep5
```

Representative raw transcripts (agent JSON, authoritative state/history/events,
score) are under `results/transcripts/`.
