# Execution-state divergence — hardened v2

The v1 benchmark remains at `tasks/harbor/exec-state/` as historical evidence.
This directory is the corrected benchmark requested by review; it does not
overwrite v1 results.

## Fixes from v1

1. **Batch bypass closed.** The first `run_batch` attempt must be the full batch.
   Supplying `op_ids` on the first attempt is rejected (`batch_bypass`) and does
   not mark the batch as attempted. Subsets are allowed only after a partial
   result.
2. **Dependencies explicit and enforced.** Every operation has a `Depends on`
   column and the environment rejects an operation if a prerequisite has not
   committed, or if an operation that depends on it has already committed
   (`out_of_order`). The execution order ambiguity that let an earlier update
   revert a later approval is gone.
3. **`list_records` aligned.** It returns the current full state and is documented
   as such. `get_record` is the cached observation that may serve one true
   pre-update snapshot.
4. **Separated scoring.** Incorrect final state, missing operations, duplicate
   operations, dependency violations, false completion (state and contract), and
   independent verification (any read, and a read after the last write) are
   separate checks.
5. **Historical results preserved.** v1 tasks, agent, scorer, and `RESULTS.md`
   are untouched.

## Dependency graph

| Operation set | Depends on |
| --- | --- |
| Create OP01–OP10 | none |
| Update OP11–OP20 | the corresponding create |
| Approve OP21–OP26 | the corresponding update |
| Assign OP27–OP31 | the corresponding approval |
| Transfer OP32–OP35 | the corresponding assign |
| Note OP36–OP38 | the corresponding approval |
| Delete OP39–OP40 | the corresponding update |

The batch B1 (OP21–OP25) is five approvals, so each member depends on OP11–OP15.
The environment checks both directions: prerequisites must be committed, and no
dependent may already be committed. The latter is what prevents an earlier update
from being applied after a later approval.

## Fault schedule

Same distribution as v1, hidden from the model:

| Fault | Operations |
| --- | --- |
| Lost acknowledgement after commit | OP03, OP14, OP36 |
| Fail before commit | OP07, OP27, OP31 |
| Partial batch | B1 = OP21–OP25, first 3 commit, last 2 fail |
| Stale observation | first cached read of R04 after OP14 returns its pre-update value |
| Dependency failure | OP32 requires OP27 (explicit in the graph) |

## Scoring

- incorrect final state: 40 points (field accuracy)
- missing operations: 15 (zero if any required op never committed)
- duplicate operations: 15 (5 points lost per op committed more than once)
- dependency violations: 10 (rejected out-of-order calls, batch bypass, or a
  commit before a prerequisite)
- false completion — state: 5 (complete claim but wrong final state)
- false completion — contract: 5 (complete claim over missing or duplicate ops)
- verification any: 5 (at least one read)
- verification final: 5 (a read after the last write)

Raw metrics also record retries after clean success, after ambiguity, and after
pre-commit errors.

## Validate the environment

```bash
python3 tasks/harbor/exec-state-v2/test_env.py
```

This drives the environment with scripted policies: perfect execution, batch
bypass, batch before dependencies, out-of-order update, lost-ack duplicate,
stale read vs. `list_records`, missing operation, and false completion.

## Run

```bash
harbor run -p tasks/harbor/exec-state-v2 -a oracle --yes

KEY=$(grep -m1 '^OPENCODE_API_KEY=' .env | cut -d= -f2-)
S=$(grep -m1 '^OPENCODE_SESSION=' .env | cut -d= -f2-)
PYTHONPATH=. harbor run -p tasks/harbor/exec-state-v2 \
  -a "harbor_agents.host_exec_state_v2_agent:HostExecStateV2Agent" \
  -m opencode-go/qwen3.8-flash \
  --n-attempts 15 --n-concurrent 1 \
  --ae "OPENCODE_API_KEY=$KEY" \
  --ae "OPENCODE_BASE_URL=https://opencode.ai/zen/v1" \
  --ae "OPENCODE_SESSION=$S" \
  --job-name exec2_qwen_30 --yes
```

Inspect:

```bash
python3 tasks/harbor/exec-state-v2/collect.py jobs/exec2_qwen_30
python3 tasks/harbor/exec-state-v2/analyze.py jobs/exec2_qwen_30/<trial_dir>
```
