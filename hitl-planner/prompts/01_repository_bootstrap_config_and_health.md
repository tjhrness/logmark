# Implementation task 01 — Repository bootstrap, config, and health

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Repository bootstrap, config, and health
Authoritative sections: §2.1–2.4, §8.1, §8.6, §9, §10 E7

Implementation scope:
Create the smallest genuinely runnable Python 3.11 desktop Flask application. Add `hitl_planner.py`, `test_hitl_planner.py`, `requirements.txt` (Flask only), `requirements-dev.txt` (pytest only), and a succinct startup README if not present. Serve a static locally defined HTML page at `/` with project title and a clear "not yet available" placeholder, and `GET /api/health` with `{tool,version,workspace_ok}`. Use Flask's test client. Load or atomically create `config.json` next to the script with schema_version 1, workspace default `Path.home()/Documents/HITL Planner`, port provisionally 5062. Create workspace on first run. If config is malformed, missing keys, or cannot be read, print one line and exit 2; never overwrite a bad config. Config and workspace paths must be Windows-safe, and environment-independent in tests. No fake statistics, fake answer-key passes, or fake final UI.

Tests to write FIRST:
Red: root and health responses, config-created-on-first-run, config-preserved, corrupted/missing-key config exits 2, tmp workspace isolation, HTTP without outside resources. Green: minimal app factory that accepts injectable config/workspace, source-of-truth constants, explicit main guard. Ensure importing module has no side effects; do not open browser during tests.

Acceptance condition:
`python -m pytest -q` passes; a manual local launch shows the page; `config.json` is ignored by git; no other runtime modules or network dependencies.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
