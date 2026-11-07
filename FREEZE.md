# Freeze record

The two earlier pilots are frozen. The audit pilot is a separate directory and does not modify their tasks, gold, scorer, or recorded results.

## Frozen pilot 1 — compact adjudication (D1-S)

- Task files: `tasks/T1.json`, `tasks/T2.json`
- Harness: `src/`
- Raw runs: `runs/`
- Graded results: `results/`
- Report: `PILOT_REPORT.md`
- Decision: **NO-GO**
- Key result: open production 100% for DeepSeek V4.1 Flash and Qwen 3.8 Flash; no recognition–production gap.

Do not edit these files to rescue the result. If a future experiment uses the same tasks, record it as a new run with a new run ID.

## Frozen pilot 2 — Harbor long-horizon generation

- Task: `tasks/harbor/board-brief/`
- Oracle: 1.000
- Clean model run: Qwen 3.8 Flash, reward **1.000**, 1,924 words
- First run: 0.927 (17-word overrun plus two grader false fails, since fixed)
- Report: `tasks/harbor/board-brief/PILOT_REPORT.md`
- Decision: **NO-GO** on expanding as written; the instruction enumerated the 13 findings, so the model filled a checklist.

Do not change the board-brief task, scorer, or transcript to make the result look different. Corrections to a scorer belong in a new task version with a note.

## New pilot — surface-compliance audit

- Directory: `tasks/harbor/audit/`
- Four tasks: retention clean/defective, incident clean/defective.
- Oracle: 4/4 at 1.000.
- Report: `tasks/harbor/audit/PILOT_REPORT.md` (written after the model runs).
- This pilot asks a different question and is not a rerun of the frozen pilots.

## Git history

Commit `19b6007` contains the frozen pilots. Later commits add the audit pilot and its reports. No frozen result was rewritten.
