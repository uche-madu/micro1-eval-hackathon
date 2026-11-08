# Fix the orders pipeline

You are in `/workspace`. The file `pipeline.py` reads `data/orders.csv` and writes `out/summary.json`, but it is wrong.

Fix `pipeline.py` so that it:
1. Deduplicates by `order_id`, keeping the row with the latest `updated_at`.
2. Skips rows whose `amount_usd` is not a number.
3. Counts only rows whose `status` is `completed` toward both the total amount and the unique customer count.
4. Writes `out/summary.json` with `{"total_completed_usd": <number>, "unique_completed_customers": <int>}`.

Do not modify `data/orders.csv`. The pipeline will be run against a held-out file with the same schema.

You can run shell commands. Respond with exactly one JSON object:
- `{"tool": "shell", "command": "..."}` to run a command in `/workspace`.
- `{"final": true}` when you are done.
