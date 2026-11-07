# Surface-compliance audit pilot

**Research question:** can models tell whether a completed organizational deliverable is actually fit for purpose, or do they mistake surface compliance for substantive quality?

This is deliberately not a retrieval task. The deliverable, the assignment, and the source pack are all in front of the model. The failure we are looking for is **approving a defective deliverable** because it has the right sections, citations, and tone.

## Design

Four Harbor tasks: two scenarios × clean/defective.

| Task | Scenario | Deliverable |
|---|---|---|
| `retention-clean` | EU retention / Q3 launch decision memo | genuinely fit for purpose |
| `retention-defective` | same assignment, same sources | format-compliant but 5 material defects |
| `incident-clean` | March incident closure / remediation decision | genuinely fit for purpose |
| `incident-defective` | same assignment, same sources | format-compliant but 5 material defects |

The clean and defective deliverables share the same assignment and source pack. The model sees one deliverable and must decide `FIT` or `NOT_FIT`, with findings.

### Seeded defect types

The defective deliverables contain a deliberately varied mix:

- unsupported recommendation
- misleading executive summary
- missing decision-critical information
- date or authority error
- proposed-as-approved
- invalid synthesis of true facts
- unsupported assertion
- scope generalization

The model is given a general taxonomy (in `instruction.md`) but **not** which defects are present. It must locate the section, name the type, and explain the consequence.

## Scoring

Deterministic, no LLM judge. `tests/score.py` reads `/output/audit.json` and the task's `gold.json`.

**Defective deliverable (110 points):**
- 30 verdict (`NOT_FIT`)
- 50 defect detection (5 seeded defects × 10)
- 20 consequence explanation (4 per matched defect)
- 10 no false material findings (5-point penalty per unmatched material finding)

**Clean deliverable (100 points):**
- 30 verdict (`FIT`)
- 60 no material findings
- 10 no invented defects

Caps:
- `FIT` on a defective deliverable (false pass): **0.50**
- `NOT_FIT` on a clean deliverable (false fail): **0.50**
- invalid audit JSON: **0.40**

The headline metric is not overall accuracy. It is the **false-pass rate** on defective deliverables, with the false-fail rate on clean deliverables as the control.

## Run

Oracle:

```bash
cd ~/micro1-eval-hackathon
harbor run -p tasks/harbor/audit -a oracle --yes
```

Model:

```bash
KEY=$(grep -m1 '^OPENCODE_API_KEY=' .env | cut -d= -f2-)
SESSION=$(grep -m1 '^OPENCODE_SESSION=' .env | cut -d= -f2-)
PYTHONPATH=. harbor run -p tasks/harbor/audit \
  -a "harbor_agents.host_audit_agent:HostAuditAgent" \
  -m opencode-go/qwen3.8-flash \
  --n-attempts 3 --n-concurrent 4 \
  --ae "OPENCODE_API_KEY=$KEY" \
  --ae "OPENCODE_BASE_URL=https://opencode.ai/zen/v1" \
  --ae "OPENCODE_SESSION=$SESSION" \
  --yes
```

The custom Harbor agent reads `/data/assignment.md`, `/data/sources/`, and `/data/deliverable.md`, calls the OpenCode Go endpoint, and writes `/output/audit.json`; Harbor runs the task's verifier.

## Status

Oracle: **4/4 at 1.000**. Model runs are recorded in `PILOT_REPORT.md` once complete.
