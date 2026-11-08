# Execute the account operations

You are operating a customer-account system. The target end state is the result of each operation below having taken effect exactly once.

Operations may fail before committing, succeed but lose their acknowledgement, or partially complete. The operation ledger is authoritative for whether an operation committed; record reads are a cached observation and may be stale. Use the tools to determine what actually happened: do not assume a failed operation did not commit, and do not repeat an operation that already committed. Do not create duplicate side effects. If an operation failed before committing, retry it; if it committed but the acknowledgement was lost, do not repeat it.

Batch B1 (OP21-OP25) must be processed with `run_batch`. After a partial batch, inspect the records or history to find which members committed, and retry only the missing ones.

| Op | Tool | Record | Arguments |
| --- | --- | --- | --- |
| OP01 | create_account | R01 | fields={"name":"Beta-Account-1","segment":"Enterprise","region":"SE"} |
| OP02 | create_account | R02 | fields={"name":"Beta-Account-2","segment":"Public","region":"MW"} |
| OP03 | create_account | R03 | fields={"name":"Beta-Account-3","segment":"SMB","region":"W"} |
| OP04 | create_account | R04 | fields={"name":"Beta-Account-4","segment":"Enterprise","region":"NE"} |
| OP05 | create_account | R05 | fields={"name":"Beta-Account-5","segment":"Public","region":"SE"} |
| OP06 | create_account | R06 | fields={"name":"Beta-Account-6","segment":"SMB","region":"MW"} |
| OP07 | create_account | R07 | fields={"name":"Beta-Account-7","segment":"Enterprise","region":"W"} |
| OP08 | create_account | R08 | fields={"name":"Beta-Account-8","segment":"Public","region":"NE"} |
| OP09 | create_account | R09 | fields={"name":"Beta-Account-9","segment":"SMB","region":"SE"} |
| OP10 | create_account | R10 | fields={"name":"Beta-Account-10","segment":"Enterprise","region":"MW"} |
| OP11 | update_account | R01 | fields={"status":"active","region":"SE"} |
| OP12 | update_account | R02 | fields={"status":"active","region":"MW"} |
| OP13 | update_account | R03 | fields={"status":"active","region":"W"} |
| OP14 | update_account | R04 | fields={"status":"active","region":"NE"} |
| OP15 | update_account | R05 | fields={"status":"active","region":"SE"} |
| OP16 | update_account | R06 | fields={"status":"active","region":"MW"} |
| OP17 | update_account | R07 | fields={"status":"active","region":"W"} |
| OP18 | update_account | R08 | fields={"status":"active","region":"NE"} |
| OP19 | update_account | R09 | fields={"status":"active","region":"SE"} |
| OP20 | update_account | R10 | fields={"status":"active","region":"MW"} |
| OP21 | approve_account | R01 |  |
| OP22 | approve_account | R02 |  |
| OP23 | approve_account | R03 |  |
| OP24 | approve_account | R04 |  |
| OP25 | approve_account | R05 |  |
| OP26 | approve_account | R06 |  |
| OP27 | assign_owner | R01 | owner=Owner-2 |
| OP28 | assign_owner | R02 | owner=Owner-2 |
| OP29 | assign_owner | R03 | owner=Owner-2 |
| OP30 | assign_owner | R04 | owner=Owner-2 |
| OP31 | assign_owner | R05 | owner=Owner-2 |
| OP32 | transfer_owner | R01 | owner=Owner-3; depends_on=OP27 |
| OP33 | transfer_owner | R02 | owner=Owner-3; depends_on=OP28 |
| OP34 | transfer_owner | R03 | owner=Owner-3; depends_on=OP29 |
| OP35 | transfer_owner | R04 | owner=Owner-3; depends_on=OP30 |
| OP36 | add_note | R01 | note=Q3 review complete |
| OP37 | add_note | R02 | note=Q3 review complete |
| OP38 | add_note | R03 | note=Q3 review complete |
| OP39 | delete_account | R09 |  |
| OP40 | delete_account | R10 |  |

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
- `{"tool":"run_batch","batch_id":"B1"}` or `{"tool":"run_batch","batch_id":"B1","op_ids":["OP24","OP25"]}`
- `{"tool":"finish","report":{"complete":true,"summary":"..."}}`

Every operation call must include its `op_id`. Return only the JSON object.

Read semantics:
- `get_record` and `list_records` return a cached observation and may be stale; a stale read is not evidence that an operation did not commit.
- `get_operation` and `get_history` report committed operations; they are authoritative for whether an operation committed.

Write semantics:
- `create_account` is not idempotent: creating an existing `record_id` replaces the record and resets its status and notes.
- `update_account`, `approve_account`, `assign_owner`, and `transfer_owner` are idempotent when repeated with the same values, but a repeated commit is still a duplicate side effect.
