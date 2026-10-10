# Implementation task 02 — Single-instance launcher and clean quit

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Single-instance launcher and clean quit
Authoritative sections: §2.3, §9, §10 E6

Implementation scope:
Implement the Windows launch lifecycle in `hitl_planner.py`. On `python hitl_planner.py`, read config, check configured port on 127.0.0.1: if `/api/health` identifies this tool, open its URL in the default browser and exit 0. If any other service occupies the port, print a concise error naming the port and config.json; exit 2. If free, start a controllable local server only on 127.0.0.1, open browser, and respond to Ctrl-C. Implement POST `/api/quit` returning `{ok:true}` then cleanly stopping this process. Avoid relying on deprecated/missing Werkzeug request-environ shutdown hooks. Do not bind to 0.0.0.0. Include Quit button on the basic shell.

Tests to write FIRST:
Test correct occupied-port classification using monkeypatched health/probes and a temporary socket, correct host binding, clean shutdown in a real subprocess/local test, browser-opening mocked, and Ctrl-C path. Tests may use ephemeral ports; avoid interacting with real port 5062 in automated tests.

Acceptance condition:
Launcher supports free/same-tool/foreign-port states; quit actually stops server; all endpoints stay localhost only.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
