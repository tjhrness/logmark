# Implementation task 18 — Immutable plan saves and versions

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Immutable plan saves and versions
Authoritative sections: §3.1, §8.2, §8.7, §9, §11.3

Implementation scope:
Implement `POST /api/plans`: server-side revalidate and recalculate every plan field, derive period display/plan_id, set schema_version, tool version/method version, timestamp with local UTC offset, inputs plus p_source/prefilled_from, all outputs, warnings, seven statements, constants, formulas, arithmetic, integrity status. Save `plan_v<N>.json` with N=max(existing)+1 computed at save time. Never overwrite any existing `plan_vN`. Return `{plan_id,version,folder,report_path}` (report path populated as soon as report generation exists, or integrate a minimal immediately generated report in this step). Plan can save with W7. Ensure tampered client outputs are ignored. Saving same plan again increments version.

Tests to write FIRST:
Red: two saves create v1 and v2; v1 hash/bytes remain identical; reload object matches `/api/calc` outputs; W7 allowed to save; timestamps offset-aware; two browser requests cannot silently overwrite each other; bad inputs 400; save does not depend on browser-calculated output.

Acceptance condition:
Versioned JSON is the immutable single source of truth and functional POST route is tested.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
