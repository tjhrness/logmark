# Implementation task 31 — Immutable answer key and startup gate

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Immutable answer key and startup gate
Authoritative sections: §2.3 --selftest, §7.5, §11.1, §11.5, §10 E8

Implementation scope:
Implement all 11 answer-key K1–K11 as self-contained shared assertions against pure application math; use EXACT constants/expected values from spec. `python hitl_planner.py --selftest` prints one PASS/FAIL per case and exits 0 only if all pass, before server launch. At every normal startup run same key and cache integrity status. On any failure print failing identifiers, show red all-tab banner, disable `POST /api/plans` and actuals recording server-side even for forged clients, disable Save and Record UI; leave calculation and Method available with untrusted warning. Expose status via GET `/api/method`. NEVER 'fix' case failures by editing expected numbers.

Tests to write FIRST:
Test selftest process prints 11 PASS lines and exit0; monkeypatch bad Z or function -> failing case list and exit1; startup method failure banner, direct save/actuals POST rejected, old records left intact; intact calculation passes 11/11. No fake flags.

Acceptance condition:
Statistical integrity becomes an enforceable runtime gate, not a cosmetic label.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
