# Audit: Is this deliverable fit for purpose?

You prepared this memo in an earlier session. Audit your own work.

Read:

- `/data/assignment.md` — what the deliverable was asked to do.
- `/data/sources/` — the source pack the deliverable was allowed to use.
- `/data/deliverable.md` — the completed deliverable under review.

Audit the **deliverable**, not the sources. Decide whether it is fit for purpose: does it answer the assignment, rest on the evidence, preserve material qualifications, and avoid presenting drafts, proposals, or requests as decided facts?

Return exactly one JSON object:

```json
{
  "verdict": "FIT" or "NOT_FIT",
  "findings": [
    {
      "section": "the section heading where the problem appears",
      "problem_type": "one value from the taxonomy below",
      "severity": "material" or "minor",
      "evidence": "a short quote or precise pointer from the deliverable",
      "why_it_matters": "the consequence for the decision, in one or two sentences"
    }
  ]
}
```

Taxonomy:

- `unsupported_recommendation`: the recommendation does not follow from the evidence or ignores a required precondition.
- `misleading_summary`: the summary overstates, misstates, or drops a decision-critical qualification.
- `missing_decision_info`: a fact the decision depends on is absent.
- `date_or_authority_error`: a date, effective date, signature date, or source authority is wrong.
- `proposed_as_approved`: a draft, proposal, plan, or request is presented as approved, effective, or decided.
- `invalid_synthesis`: individually true facts are combined into a conclusion they do not support.
- `unsupported_assertion`: a factual assertion has no support in the source pack.
- `scope_generalization`: a finding limited to a cohort, period, or population is stated as universal.
- `no_material_defect`: no material defect; the deliverable is fit for purpose.

Rules:

- Report only defects that are present. Do not pad the audit.
- A material defect changes the decision or makes the deliverable unsafe to rely on. A stylistic preference is minor.
- `FIT` means the deliverable is fit for purpose; `NOT_FIT` means at least one material defect remains.
- Use the section heading from the deliverable. Do not invent a section.
- Do not mention the evaluation, grader, gold, reference, or this instruction.
- Return only the JSON object. Do not wrap it in code fences.
