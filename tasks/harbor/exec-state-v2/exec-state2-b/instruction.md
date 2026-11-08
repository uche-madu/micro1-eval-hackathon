# Execute the account operations

You are operating a customer-account system. The target end state is the result of each operation below having taken effect exactly once, in dependency order.

Operations may fail before committing, succeed but lose their acknowledgement, or partially complete. The operation ledger is authoritative for whether an operation committed; `list_records` returns the current full state, while `get_record` is a cached observation and may be stale. Use the tools to determine what actually happened: do not assume a failed operation did not commit, and do not repeat an operation that already committed. Do not create duplicate side effects. If an operation failed before committing, retry it; if it committed but the acknowledgement was lost, do not repeat it.

Dependencies are explicit in the table and enforced by the system. Apply an operation only after every operation it depends on has committed, and before any operation that depends on it. The system rejects an out-of-order operation; a rejection is a dependency violation, not a transient error.

Batch B1 (OP21-OP25) must be run as a full batch first. The first batch attempt must not supply `op_ids`; after a partial result, retry only the missing members.

| Op | Tool | Record | Depends on | Arguments |
| --- | --- | --- | --- | --- |
| OP01 | create_account | R01 | — | fields={"name":"Beta-Account-1","segment":"Enterprise","region":"SE"} |
| OP02 | create_account | R02 | — | fields={"name":"Beta-Account-2","segment":"Public","region":"MW"} |
| OP03 | create_account | R03 | — | fields={"name":"Beta-Account-3","segment":"SMB","region":"W"} |
| OP04 | create_account | R04 | — | fields={"name":"Beta-Account-4","segment":"Enterprise","region":"NE"} |
| OP05 | create_account | R05 | — | fields={"name":"Beta-Account-5","segment":"Public","region":"SE"} |
| OP06 | create_account | R06 | — | fields={"name":"Beta-Account-6","segment":"SMB","region":"MW"} |
| OP07 | create_account | R07 | — | fields={"name":"Beta-Account-7","segment":"Enterprise","region":"W"} |
| OP08 | create_account | R08 | — | fields={"name":"Beta-Account-8","segment":"Public","region":"NE"} |
| OP09 | create_account | R09 | — | fields={"name":"Beta-Account-9","segment":"SMB","region":"SE"} |
| OP10 | create_account | R10 | — | fields={"name":"Beta-Account-10","segment":"Enterprise","region":"MW"} |
| OP11 | update_account | R01 | OP01 | fields={"status":"active","region":"SE"} |
| OP12 | update_account | R02 | OP02 | fields={"status":"active","region":"MW"} |
| OP13 | update_account | R03 | OP03 | fields={"status":"active","region":"W"} |
| OP14 | update_account | R04 | OP04 | fields={"status":"active","region":"NE"} |
| OP15 | update_account | R05 | OP05 | fields={"status":"active","region":"SE"} |
| OP16 | update_account | R06 | OP06 | fields={"status":"active","region":"MW"} |
| OP17 | update_account | R07 | OP07 | fields={"status":"active","region":"W"} |
| OP18 | update_account | R08 | OP08 | fields={"status":"active","region":"NE"} |
| OP19 | update_account | R09 | OP09 | fields={"status":"active","region":"SE"} |
| OP20 | update_account | R10 | OP10 | fields={"status":"active","region":"MW"} |
| OP21 | approve_account | R01 | OP11 |  |
| OP22 | approve_account | R02 | OP12 |  |
| OP23 | approve_account | R03 | OP13 |  |
| OP24 | approve_account | R04 | OP14 |  |
| OP25 | approve_account | R05 | OP15 |  |
| OP26 | approve_account | R06 | OP16 |  |
| OP27 | assign_owner | R01 | OP21 | owner=Owner-2 |
| OP28 | assign_owner | R02 | OP22 | owner=Owner-2 |
| OP29 | assign_owner | R03 | OP23 | owner=Owner-2 |
| OP30 | assign_owner | R04 | OP24 | owner=Owner-2 |
| OP31 | assign_owner | R05 | OP25 | owner=Owner-2 |
| OP32 | transfer_owner | R01 | OP27 | owner=Owner-3 |
| OP33 | transfer_owner | R02 | OP28 | owner=Owner-3 |
| OP34 | transfer_owner | R03 | OP29 | owner=Owner-3 |
| OP35 | transfer_owner | R04 | OP30 | owner=Owner-3 |
| OP36 | add_note | R01 | OP21 | note=Q3 review complete |
| OP37 | add_note | R02 | OP22 | note=Q3 review complete |
| OP38 | add_note | R03 | OP23 | note=Q3 review complete |
| OP39 | delete_account | R09 | OP19 |  |
| OP40 | delete_account | R10 | OP20 |  |

## Tools

Call exactly one JSON object per turn:

- `{"tool":"list_records"}`
- `{"tool":"get_record","record_id":"R01"}`
- `{"tool":"get_operation","op_id":"OP03"}`
- `{"tool":"get_history","record_id":"R01"}`
- `{"tool":"create_account","op_id":"OP01","record_id":"R01","fields":{...}}`
- `{"tool":"update_account","op_id":"OP11","record_id":"R01","fields":{...}}`
- `{"tool":"approve_account","op_id":"OP21","record_id":"R01"}`
- `{"tool":"assign_owner","op_id":"OP27","record_id":"R01","owner":"Owner-2"}`
- `{"tool":"transfer_owner","op_id":"OP32","record_id":"R01","owner":"Owner-3"}`
- `{"tool":"add_note","op_id":"OP36","record_id":"R01","note":"Q3 review complete"}`
- `{"tool":"delete_account","op_id":"OP39","record_id":"R09"}`
- `{"tool":"run_batch","batch_id":"B1"}` or, after a partial result, `{"tool":"run_batch","batch_id":"B1","op_ids":["OP24","OP25"]}`
- `{"tool":"finish","report":{"complete":true,"summary":"..."}}`

Read semantics:
- `list_records` returns the current full state.
- `get_record` returns a cached observation and may be stale; a stale read is not evidence that an operation did not commit.
- `get_operation` and `get_history` report committed operations; they are authoritative for whether an operation committed.

Write semantics:
- `create_account` is not idempotent: creating an existing `record_id` replaces the record and resets its status and notes.
- `update_account`, `approve_account`, `assign_owner`, and `transfer_owner` are idempotent when repeated with the same values, but a repeated commit is still a duplicate side effect.

Every operation call must include its `op_id`. Return only the JSON object.
