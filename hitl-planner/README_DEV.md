# HITL Sample Size Planner — Codex development kit

This package contains the original **spec v1.0**, an implementation blueprint, a comprehensive `todo.md` checklist, and **36 complete, self-contained, code-tagged `text` prompts for ChatGPT Codex**. **It does not contain the completed Python application or passing application tests.**

**Start with [`CODEX_START_HERE.md`](CODEX_START_HERE.md).** It describes GitHub + ChatGPT Codex cloud and Codex CLI workflows, how to run a single step, and how to review/merge before starting the next.

## Contents

- `AGENTS.md`: permanent Codex repository guardrails preserving the non-negotiables from spec §12.
- `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf`: immutable source specification.
- `docs/SPEC_TEXT.txt`: machine-extracted, searchable convenience copy; PDF controls disagreements.
- `BLUEPRINT.md`: method contract, decomposition, architecture and 36 step sequence.
- `PROMPTS.md`: all complete prompts, fenced as `text`.
- `prompts/01_*.md` … `prompts/36_*.md`: standalone prompt files for one Codex task each.
- `todo.md`: milestone checkboxes, subchecks, task review gates, PR/commit tracking.
- `TRACEABILITY.md`: formula, answer key, warnings, endpoint, persistence and test coverage.
- `ACCEPTANCE.md`: target Windows manual acceptance; `DECISIONS.md`: port/environment decisions.
- `.gitignore`, `requirements.txt` (Flask), `requirements-dev.txt` (pytest): starting repository metadata.

## Critical rules

Use one prompt at a time on the last reviewed Git revision. Write failing tests before production changes where feasible; test; review the diff; merge one green Codex change before the next. **Never rewrite the eleven answer-key expectations** and never claim that a Windows test was run in a Linux cloud environment.

The `5062` port remains **provisional**, pending check against existing Pareto/IMR tools on the target Windows machine. No new runtime modules or out-of-scope v2 features are authorized.
