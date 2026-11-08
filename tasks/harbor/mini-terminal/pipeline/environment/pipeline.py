import csv, json, os
os.makedirs("out", exist_ok=True)
rows = list(csv.DictReader(open("data/orders.csv")))
total = sum(float(r["amount_usd"]) for r in rows)
customers = {r["customer_id"] for r in rows}
json.dump({"total_completed_usd": total, "unique_completed_customers": len(customers)}, open("out/summary.json", "w"))
