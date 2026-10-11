# Implementation task 24 — Actuals calculations and W8–W10

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Actuals calculations and W8–W10
Authoritative sections: §4.6–4.8, §5 W8–W10, §11.2

Implementation scope:
Implement pure actuals calculation keyed to a specific saved plan version. Validate reviewed integer 1…N, issues integer 0…reviewed, agreement 0–1 decimal, notes free text. Return observed rate issues/reviewed. For 0<obs<1 calculate reverse margin F9 with p=obs (plus relative margin when planned mode relative); for zero issues return no margin and `true rate below T_at(reviewed)` C-bound; for all issues return no margin and `true rate above 1-T_at(reviewed)`; certification statuses: off not planned; on with issues>0 not applicable; on with zero issues met if inverse threshold<=T else not met. W8 reviewed<n_planned, W9 obs>2*p_planned OR obs<.5*p_planned (strict inequalities), W10 agreement<.80. Return planned-vs-actual comparison for report.

Tests to write FIRST:
Red: zero/one/all issue cases, n=1 and census, relative margin, W8/W9/W10 strict edge pairs (agreement .8 vs .799, observed exactly x2/x.5), certification met/not met/not planned/issues found, invalid counts/error-map, no modification to referenced plan.

Acceptance condition:
All actuals metrics reuse F9/F10 and are correctly interpretable in extreme outcomes.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
