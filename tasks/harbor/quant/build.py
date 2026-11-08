"""Build the quantitative rebate aggregation task."""
from __future__ import annotations
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = []
for i in range(1, 25):
    acc = f"ACC-{i:02d}"
    tier = ["A", "B", "C"][i % 3]
    q1 = 100 + i * 7
    q2 = 120 + i * 5
    returns = (i * 3) % 15
    ROWS.append({"account_id": acc, "tier": tier, "units_q1": q1, "units_q2": q2, "returns_q2": returns})

RATES = {"A": 12, "B": 8, "C": 5}
EXCLUDED = {"ACC-12"}
EXCEPTION = {"ACC-07": 15}

def rebate(row):
    if row["account_id"] in EXCLUDED:
        return 0
    rate = EXCEPTION.get(row["account_id"], RATES[row["tier"]])
    net_q2 = row["units_q2"] - row["returns_q2"]
    if row["returns_q2"] > 0.10 * row["units_q2"] and row["account_id"] not in EXCEPTION:
        rate = rate / 2
    return row["units_q1"] * RATES[row["tier"]] + net_q2 * rate

gold_rebate = sum(rebate(r) for r in ROWS)
gold_units = sum(r["units_q1"] + r["units_q2"] - r["returns_q2"] for r in ROWS)
GOLD = {"total_rebate_usd": gold_rebate, "total_net_units": gold_units, "excluded_accounts": sorted(EXCLUDED)}
REF = GOLD

INSTRUCTION = """# Q3 rebate aggregation

Read `/data/rebates.csv` and `/data/rules.md`. Compute the totals exactly.

Rules:
- Tier rebate per unit: A = $12, B = $8, C = $5.
- Q1 rebate = units_q1 × the account's tier rate.
- Q2 rebate = (units_q2 − returns_q2) × the account's tier rate.
- If returns_q2 is greater than 10% of units_q2, the account's Q2 rate is halved. Apply this to the Q2 rebate only.
- ACC-07 has a contractual Q2 rate of $15 per unit instead of its tier rate. The return-penalty rule does not apply to ACC-07.
- ACC-12 is a government account and is excluded from all rebates.
- Total net units = sum over all accounts of (units_q1 + units_q2 − returns_q2).

Return ONLY JSON:
```json
{"total_rebate_usd": <number>, "total_net_units": <number>, "excluded_accounts": ["..."]}
```
Do not round the rebate unless it has cents; report the exact sum.
"""


def main():
    d = HERE / "quant-rebate"
    (d / "environment" / "data").mkdir(parents=True, exist_ok=True)
    (d / "solution").mkdir(exist_ok=True)
    (d / "tests").mkdir(exist_ok=True)
    with (d / "environment" / "data" / "rebates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ROWS[0]))
        writer.writeheader()
        writer.writerows(ROWS)
    (d / "environment" / "data" / "rules.md").write_text(
        "Tier rebate per unit: A = $12, B = $8, C = $5.\n"
        "Q1 rebate = units_q1 × tier rate.\n"
        "Q2 rebate = (units_q2 − returns_q2) × tier rate.\n"
        "If returns_q2 > 10% of units_q2, halve the Q2 rate for that account.\n"
        "ACC-07 has a contractual Q2 rate of $15/unit; the return penalty does not apply.\n"
        "ACC-12 is excluded from all rebates.\n"
        "Total net units = Σ(units_q1 + units_q2 − returns_q2).\n"
    )
    (d / "instruction.md").write_text(INSTRUCTION)
    (d / "task.toml").write_text('''schema_version = "1.4"
artifacts = []

[task]
name = "micro1/quant-rebate"
version = "1.0.0"
description = "24-account tiered rebate aggregation with an exception and an exclusion"
authors = [{ name = "micro1-eval-hackathon" }]
keywords = ["quantitative", "aggregation", "rebate"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 900.0

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
''')
    (d / "environment" / "Dockerfile").write_text(
        "FROM python:3.13-slim\n\nRUN apt-get update && apt-get install -y --no-install-recommends "
        "bash curl ca-certificates && rm -rf /var/lib/apt/lists/*\n\nWORKDIR /app\nCOPY data /data\nRUN mkdir -p /output\n"
    )
    (d / "tests" / "gold.json").write_text(json.dumps(GOLD, indent=2) + "\n")
    (d / "tests" / "score.py").write_text((HERE / "score_template.py").read_text())
    (d / "tests" / "test.sh").write_text(
        "#!/bin/bash\nset -u\nmkdir -p /logs/verifier\npython3 /tests/score.py || true\n"
        "if [ ! -s /logs/verifier/reward.txt ]; then echo 0 > /logs/verifier/reward.txt; fi\nexit 0\n"
    )
    (d / "solution" / "reference_answer.json").write_text(json.dumps(REF, indent=2) + "\n")
    (d / "solution" / "solve.sh").write_text(
        '#!/bin/bash\nset -euo pipefail\nmkdir -p /output\n'
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'cp "$HERE/reference_answer.json" /output/answer.json\n'
    )
    (d / "tests" / "test.sh").chmod(0o755)
    (d / "solution" / "solve.sh").chmod(0o755)
    print("built quant-rebate", GOLD)


if __name__ == "__main__":
    main()
