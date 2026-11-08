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

Pending: 30 trials, job `exec2_gpt_30`.

## Failure classification rule

A trial is an operation-tracking failure if it has any missing operation,
duplicate operation, or dependency violation, or if it reports complete over
such a defect. Harness/tool-interface failures (unparseable tool calls, container
write errors, endpoint errors) are reported separately and are not counted as
model state failures.
