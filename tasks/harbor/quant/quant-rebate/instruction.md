# Q3 rebate aggregation

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
