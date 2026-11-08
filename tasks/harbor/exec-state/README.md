# Execution-state divergence

Tests whether an agent maintains a correct model of a persistent system when
tool outcomes are uncertain: the operation committed but the acknowledgement was
lost, the operation failed before commit, a batch partially completed, a read was
stale, or a dependency was not satisfied.

This is an execution-reliability test, not a quiz about idempotency. The agent
must use tools, act, and leave a verifiably correct final state.

## Environment

The host agent (`harbor_agents/host_exec_state_agent.py`) owns a persistent
account store and an operation ledger. The model never runs shell and never
writes the verifier files. Each turn it emits one JSON tool call.

Read tools:
- `list_records` — cached snapshot of all records (may be stale)
- `get_record` — cached snapshot of one record (may be stale; one record returns
  a true pre-update snapshot once)
- `get_operation` — committed status for one operation, or committed/failed
  counts for a batch; authoritative
- `get_history` — committed/failed events for a record; authoritative

Write tools:
- `create_account` (not idempotent; re-creating replaces the record and resets
  status/notes)
- `update_account`, `approve_account`, `assign_owner`, `transfer_owner`,
  `add_note`, `delete_account`
- `run_batch` (whole batch, or a named subset after a partial)

Terminal:
- `finish` with a `complete` claim

## Operations and faults

Each variant has 40 operations: 10 creates, 10 updates, 6 approvals, 5 assigns,
4 transfers (each depending on its assign), 3 notes, 2 deletes.

The fault schedule is fixed and hidden from the model. Both variants currently
use the same schedule; they differ in record naming (`Alpha`/`Beta`). Each
scenario has a viable recovery path.

| Fault | Operations |
| --- | --- |
| Lost acknowledgement after commit | OP03 (create R03), OP14 (update R04), OP36 (note R01) |
| Fail before commit | OP07 (create R07), OP27 (assign R01), OP31 (assign R05) |
| Partial batch | B1 = OP21–OP25, first 3 commit, last 2 fail |
| Stale observation | first read of R04 after OP14 returns the true pre-update snapshot |
| Dependency failure | OP32 (transfer R01) requires OP27 (assign R01) committed |

## Oracle

`score_template.py` reads the authoritative state/history/report/events the host
agent writes, never the model's narrative. It computes:

- final-state field accuracy (50–60 points)
- missing/extra fields (10)
- duplicate commits (15)
- recovered pre-commit failures (5)
- dependency violation (5)
- false completion (5)
- independent verification, i.e. at least one read (5)
- metrics: retries after clean success, after ambiguous outcome, after
  pre-commit error; abandoned failures

The reference solution scores 100. The Harbor oracle runs both variants at 1.0.

## Running

```bash
# oracle
harbor run -p tasks/harbor/exec-state -a oracle --yes

# one model, N attempts per variant, serial
KEY=$(grep -m1 '^OPENCODE_API_KEY=' .env | cut -d= -f2-)
S=$(grep -m1 '^OPENCODE_SESSION=' .env | cut -d= -f2-)
PYTHONPATH=. harbor run -p tasks/harbor/exec-state \
  -a "harbor_agents.host_exec_state_agent:HostExecStateAgent" \
  -m opencode-go/qwen3.8-flash \
  --n-attempts 5 --n-concurrent 1 \
  --ae "OPENCODE_API_KEY=$KEY" \
  --ae "OPENCODE_BASE_URL=https://opencode.ai/zen/v1" \
  --ae "OPENCODE_SESSION=$S" \
  --job-name exec_qwen_rep5 --yes
```

Inspect a trial:

```bash
python3 tasks/harbor/exec-state/analyze.py jobs/<job>/<trial_dir>
python3 tasks/harbor/exec-state/collect.py jobs/<job>
```
