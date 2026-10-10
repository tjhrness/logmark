# AGENTS.md — HITL Sample Size Planner (Codex)

This root-level file gives Codex the project's non-negotiable development rules. The original specification's §12 calls the corresponding file `CLAUDE.md`; for ChatGPT Codex they are carried forward here **without changing the method**. The original PDF remains authoritative.

## Non-negotiables from specification §12 (verbatim rules)

1. One file: hitl_planner.py. Tests in test_hitl_planner.py. No other modules, no packages.
2. Flask only. Standard library for everything else. No other pip installs without asking.
3. Bind to 127.0.0.1 only. No outbound HTTP, no CDN assets, no telemetry. Must work offline.
4. All statistics are computed in Python. The browser only sends inputs and paints results.
5. Formulas F1–F10 and the constants Z = 1.645 / 1.960 / 2.576 are exactly as specified.
   Never substitute another sample-size method, never use "more precise" z-values,
   never change rounding (every n rounds UP via ceil_safe).
6. THE ANSWER KEY (spec §11.1, 11 cases) IS THE CONTRACT. A failing test means the code is
   wrong. Never edit an expected value. Stop and report instead of adjusting a formula.
7. Saved plan and actuals JSON files are immutable: never opened for writing. New versions only.
   plans_log.csv and report.html are generated from the JSON; never appended, never hand-edited.
8. All file writes are atomic (temp file + os.replace).
9. No inputs, outputs, warnings, statements, tabs or files beyond the spec without asking.
10. No deletion of user data from the UI or the code.
11. One blueprint step per session. Run the tests after every step. Commit only when green.

## Codex execution and review protocol

- Follow the current task only (one `prompts/NN_*.md` at a time). Do not implement future tasks, and do not create unconnected speculative scaffolding.
- Read only the specification sections pertinent to the task, plus the relevant current code and tests. For extraction/search convenience, `docs/SPEC_TEXT.txt` mirrors the original PDF; **the PDF wins** if discrepancies appear. Never alter the contract to make a test pass.
- Test-first where feasible: show failing test(s), implement minimal code, rerun all appropriate tests, inspect changed files. Run `python -m pytest -q` on each task; also `python hitl_planner.py --selftest` when implemented.
- A failure of any K1–K11 acceptance case is a hard stop. Do not adjust numerical expectations or silently skip failing checks.
- A cloud Codex environment may be Linux rather than the target Windows desktop. Make cross-platform unit/integration tests hermetic; clearly report Windows-only launcher, os.startfile, Excel, print/browser and port-collision checks as **not verified** until run by the owner on Windows. Never claim a test was run if it was not.
- In cloud Codex, prepare one reviewable branch/change set per task, show evidence and request review/PR. Do not treat a generated PR as merged or completed. The owner checks a task in `todo.md` only after review and merge. For Codex CLI/local runs, commit one focused green change at a time.
- Avoid network calls from the **application**; dependency installation during initial development is distinct from the offline runtime requirement.
- Keep this AGENTS.md concise. The blueprint, complete source specification, checklist and single-task prompt carry details; don't duplicate the full project requirements here.
