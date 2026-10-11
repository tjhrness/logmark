# Implementation task 36 — Manual acceptance, documentation, and release

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Manual acceptance, documentation, and release
Authoritative sections: §11.6, §12–13, Appendix B

Implementation scope:
Finish README.md for a non-technical Windows owner: Python3.11 environment, install Flask/pytest, start, stop, run selftest and pytest, configure port/workspace, find immutable files/CSV, browser Print to PDF, recover/backup, what tool cannot claim. Run all nine manual acceptance steps from spec §11.6 without modifying any fixed expected value. Verify proposed port5062 does not conflict with existing Pareto/IMR tools; if they are unavailable, stop and mark this an unresolved owner check, not "verified". Preserve spec version 1.0, method1.0, tool1.0.0 and no v2 features. Commit only after tests and owner acceptance, then tag `v1.0.0` only when acceptance is fully signed off.

Tests to write FIRST:
Manual checklist: K1–K4, 50k/88h case, 1m/385 case, certify slider and Adopt, save+report+print, reviewed382/issues11/agreement86, new month p prefill, Method11/11, quit/restart. README commands work in fresh Windows venv and include backup warnings.

Acceptance condition:
Ship only after all automatic and manual checks are green, port is verified, and the owner approves release.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
