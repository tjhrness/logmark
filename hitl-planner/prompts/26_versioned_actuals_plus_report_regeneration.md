# Implementation task 26 — Versioned actuals plus report regeneration

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Versioned actuals plus report regeneration
Authoritative sections: §3.1, §8.3–8.4, §9, §11.3

Implementation scope:
Implement POST `/api/plans/<plan_id>/actuals` to validate actuals, lock in reference to selected plan version, compute outputs/W8–W10, and atomically create immutable `actuals_v<N>.json` with offset-aware recorded_at and tool/schema/method version. Version increments on subsequent recordings; never edit existing actuals or plan files. Recreate report.html using latest plan and latest actuals; actuals block includes observed rate/achieved margin or bound, planned-vs-actuals, certify, agreement, notes and warnings. Update GET plan detail to return latest actuals for relevant version; maintain clear reference semantics if plan_version differs.

Tests to write FIRST:
Red: v1 and v2 actuals, v1 bytes unchanged, correct plan_version persisted, latest report contains Actuals plus notes properly escaped, zero-issues bounds, 400/404, simulated write failure leaves JSON immutable and surfaces recoverable report error. No duplicate statistics.

Acceptance condition:
Actuals recording is durable and immediately visible in latest report and read API.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
