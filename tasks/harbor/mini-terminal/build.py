"""Build the mini terminal pipeline task."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rows(prefix, n):
    out = []
    for i in range(1, n + 1):
        oid = f"O{prefix}{i:02d}"
        cust = f"C{i % 5}"
        status = ["completed", "refunded", "pending"][i % 3]
        amount = f"{(i * 13) % 400 + 10}.{i % 100:02d}"
        updated = f"2026-03-{i:02d}T10:00:00"
        out.append({"order_id": oid, "customer_id": cust, "status": status, "amount_usd": amount, "updated_at": updated})
    # duplicate with a later update
    out.append({"order_id": f"O{prefix}02", "customer_id": "C1", "status": "completed", "amount_usd": "999.99", "updated_at": "2026-04-01T10:00:00"})
    # malformed amount
    out.append({"order_id": f"O{prefix}04", "customer_id": "C0", "status": "completed", "amount_usd": "N/A", "updated_at": "2026-04-02T10:00:00"})
    return out


def latest(rows):
    by = {}
    for r in rows:
        oid = r["order_id"]
        if oid not in by or r["updated_at"] > by[oid]["updated_at"]:
            by[oid] = r
    return list(by.values())


def summarize(rows):
    total = 0.0
    customers = set()
    for r in latest(rows):
        try:
            amount = float(r["amount_usd"])
        except ValueError:
            continue
        if r["status"] == "completed":
            total += amount
            customers.add(r["customer_id"])
    return {"total_completed_usd": round(total, 2), "unique_completed_customers": len(customers)}


VISIBLE = rows("1", 30)
HOLDOUT = rows("9", 24)
GOLD = {"holdout": summarize(HOLDOUT)}


def csv_bytes(rows):
    from io import StringIO
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=["order_id", "customer_id", "status", "amount_usd", "updated_at"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


BUGGY = '''import csv, json, os
os.makedirs("out", exist_ok=True)
rows = list(csv.DictReader(open("data/orders.csv")))
total = sum(float(r["amount_usd"]) for r in rows)
customers = {r["customer_id"] for r in rows}
json.dump({"total_completed_usd": total, "unique_completed_customers": len(customers)}, open("out/summary.json", "w"))
'''

FIXED = '''import csv, json, os
os.makedirs("out", exist_ok=True)
rows = list(csv.DictReader(open("data/orders.csv")))
latest = {}
for r in rows:
    oid = r["order_id"]
    if oid not in latest or r["updated_at"] > latest[oid]["updated_at"]:
        latest[oid] = r
total = 0.0
customers = set()
for r in latest.values():
    try:
        amount = float(r["amount_usd"])
    except ValueError:
        continue
    if r["status"] == "completed":
        total += amount
        customers.add(r["customer_id"])
json.dump({"total_completed_usd": round(total, 2), "unique_completed_customers": len(customers)}, open("out/summary.json", "w"))
'''

INSTRUCTION = """# Fix the orders pipeline

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
"""


def main():
    d = HERE / "pipeline"
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    (d / "environment" / "data" / "orders.csv").write_text(csv_bytes(VISIBLE))
    GOLD["visible_sha256"] = hashlib.sha256((d / "environment" / "data" / "orders.csv").read_bytes()).hexdigest()
    (d / "environment" / "pipeline.py").write_text(BUGGY)
    (d / "instruction.md").write_text(INSTRUCTION)
    (d / "task.toml").write_text('''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/pipeline"
version = "1.0.0"
description = "Fix a buggy orders pipeline against a held-out CSV"
authors = [{ name = "micro1-eval-hackathon" }]
keywords = ["terminal", "tool-use", "data-pipeline"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 1200.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
''')
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /workspace\nCOPY data /workspace/data\n"
        "COPY pipeline.py /workspace/pipeline.py\nRUN mkdir -p /workspace/out /output\n"
    )
    (d / "tests" / "holdout.csv").write_text(csv_bytes(HOLDOUT))
    (d / "tests" / "gold.json").write_text(json.dumps(GOLD, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "fixed_pipeline.py").write_text(FIXED)
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/fixed_pipeline.py" /workspace/pipeline.py\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)
    print("built pipeline", GOLD)


if __name__ == "__main__":
    main()
