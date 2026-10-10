# Implementation task 05 — Headline, review counts, and capacity

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Headline, review counts, and capacity
Authoritative sections: §4.3 F5–F7, §4.8, §11.1 K10–K11, §11.2

Implementation scope:
Wire a coherent plan calculation from the existing mathematical helpers. F5: with certify on and n_assure<=N choose max(n_cochran,n_assure); otherwise n=n_cochran; binding assurance only when feasible and strictly larger than n_cochran, cochran on ties. F6 double reviews: `DR=min(n,max(F,ceil_safe(s*n)))`. F7 reviews=n+DR, hours=reviews*M/60, capacity=S*H; `fits(a,b)` means a<=b+1e-9 with unrounded numbers. Return named values suitable for API/report reuse; preserve n_assure even when infeasible. No HTTP calculations or duplicate arithmetic.

Tests to write FIRST:
Red: binding cases assurance/cochran/tie/certify-off/W7 condition; K10 DR(40)=40 DR(400)=60 at s=.15 F50; DR=0 with s=F=0; DR<=n; equality fits and just-above capacity fails; N1. Assert return data contains n, binding, reviews, hours, capacity, verdict.

Acceptance condition:
Integrated pure calculation yields one authoritative source for reviews/capacity; no UI or persistence yet.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
