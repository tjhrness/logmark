# Implementation task 28 — Generated plans_log.csv and rebuild API

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Generated plans_log.csv and rebuild API
Authoritative sections: §8.5, §9 GET /api/log/rebuild, §11.3

Implementation scope:
Implement pure workspace scan to rebuild `plans_log.csv` from readable immutable JSON on every plan/actuals save and GET `/api/log/rebuild`. One row per folder using latest plan and latest actuals; exact 43-column order in spec §8.5, sorted period_label descending then system ascending; `utf-8-sig` Excel BOM; standard `csv` quoting; warnings codes separated by semicolon; actuals cells empty when none; unreadable folders skipped with console warning. Write CSV atomically, never append or let it supersede JSON. If log rebuild fails after an immutable record saved, report partial success clearly and support explicit rebuild—do not claim save was rolled back.

Tests to write FIRST:
Red: three plans, one with actuals -> three rows, correct header names/order, UTF8 BOM, commas and multiline notes round-trip, W2;W6, deterministic sorting, no blank extra rows, re-running rebuild idempotent, corrupt folder skipped, retry after simulated failure, route returns `{path,rows}`.

Acceptance condition:
CSV is reliable derived read model for spreadsheet inspection and history.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
