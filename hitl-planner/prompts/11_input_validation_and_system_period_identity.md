# Implementation task 11 — Input validation and system-period identity

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Input validation and system-period identity
Authoritative sections: §3.1–3.3, §4.7, §10 E1, §11.2

Implementation scope:
Build centralized validation for I1–I15 and actual date labels. Required: month/week with valid YYYY-MM or ISO YYYY-Www, system 1–60 chars, N>=1 int, confidence in .90/.95/.99, absolute/relative, margin abs .005–.25 or relative .05–.50, p .001–.999, SME count>=1, net hours>0, minutes>0, DR share [0,1], DR floor int>=0, certify bool, threshold .0001–.50. API inputs are decimals, UI inputs visually percentages; refuse out-of-range values with per-field errors, never clamp. Provide default initial form state with statistical defaults; N/S/H/M remain empty. Period defaults use local date; no carried-over N.

Tests to write FIRST:
Red: both ends and just outside every numeric limit, invalid non-finite numbers, booleans masquerading as integers, invalid ISO week including week 53 where invalid, malformed month, blank fields and system length, missing dict keys, unknown fields safely handled, valid exact endpoints. `validate_plan` returns typed normalized fields or `{field:reason}` without mutating inputs.

Acceptance condition:
All entry points can reuse validation, and tests prove bad inputs never reach statistics.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
