# Implementation task 04 — Assurance, detection, and reverse maths

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Assurance, detection, and reverse maths
Authoritative sections: §4.3 F4/F8/F9/F10, §4.8, §11.1 K4/K5/K7/K8/K11

Implementation scope:
Implement F4 exact assurance `ceil_safe(log(1-C)/log(1-T))`; F8 detection `1-(1-T)**n`; F9 achieved reverse margin `Z*sqrt(p*(1-p)/n * (N-n)/(N-1))` returning 0 if n>=N or N=1; F10 inverse certification threshold `1-(1-C)**(1/n)` and an explicit n=0 n/a result. Preserve raw assurance values. Do not impose artificial population clipping on n_assure: infeasibility is handled later.

Tests to write FIRST:
Red-first K4: .95/.01 ->299; K5 n200 T.01 -> .8660 (display later); K7 N5000 n357 p.5 C.95 -> .0500 at 4 dp; K8 n120 C.95 -> .0247 at 4 dp; K11 C.95 T.001 ->2995 and larger than N2000. Add n>=N, N=1, n=0 tests, monotonicity tests for power and inverse bounds.

Acceptance condition:
Five answer-key cases pass; no undefined division or math exceptions in the required edges.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
