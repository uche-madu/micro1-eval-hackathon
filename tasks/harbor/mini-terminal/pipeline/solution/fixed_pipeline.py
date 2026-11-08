import csv, json, os
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
