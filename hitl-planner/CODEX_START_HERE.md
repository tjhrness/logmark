# Start here: build with ChatGPT Codex

**This is a project-instructions package, not a working application.** The original 34-page specification in `docs/` is the source of truth. `AGENTS.md` is the repository instruction file used for Codex; `todo.md` is the progress tracker. No coding steps have been completed.

## Use Codex in ChatGPT (cloud, with GitHub)

1. **Unzip the package** on a computer and create a **private GitHub repository** for the HITL Planner. Commit all files from this package (including `AGENTS.md`, `prompts/`, `docs/`, and the root `todo.md`). This initial docs commit becomes the project baseline. The original spec may be kept private.
2. In ChatGPT, open **Codex** and connect/authorize your GitHub repository if necessary. Create or select its working environment for this repository. The exact controls may vary by platform/account. Codex sees repository contents, **not automatically the ZIP in this chat**.
3. Ensure the Codex environment can run **Python 3.11** and install the two dependency files (`requirements.txt` for Flask, `requirements-dev.txt` for pytest). If cloud execution runs on Linux, that is fine for pure mathematics, Flask test-client and file-system tests; the finished tool must still be tested on **Windows**.
4. Start **one coding task** by pasting the entire fenced `text` prompt from `prompts/01_repository_bootstrap_config_and_health.md`. Use code/task mode rather than discussion-only mode if the product offers a choice. The prompt includes scope, exact tests, and stop rules.
5. Review Codex's diff and test output. For cloud work, create/review the change set or PR and merge it only when the required tests are green. If tests cannot run, do **not** mark the step complete: request correction or record a blocker. For local Codex, commit the green change.
6. **After merge**, check task 01 in `todo.md` and record the merged commit/PR. Open `prompts/02_...md` as a new task on the latest repository state. Repeat sequentially through task 36. Do not queue tasks 01–36 in parallel: most depend on earlier implementations.
7. On your Windows PC, perform `ACCEPTANCE.md` before the release tag: localhost-only binding, fixed-port collision with Pareto/IMR, startup/shutdown, browser report print, Excel CSV and manual numeric scenarios. Cloud execution does not verify these.

## If you prefer Codex locally (CLI/IDE)

Open Codex at the repository root, start from task 01 and paste its fenced `text` prompt. Keep `AGENTS.md` in the root. Run the same red-green-refactor cycle and make **one focused commit per green task**. Use the PowerShell commands below to test on Windows.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python hitl_planner.py --selftest
python hitl_planner.py
```

The `hitl_planner.py` and `test_hitl_planner.py` files will be created during implementation; the last three commands do not all apply to the unimplemented starter kit.

## Exact first message to Codex

Open `prompts/01_repository_bootstrap_config_and_health.md`, copy the **complete fenced text block**, and paste it as the coding task. Do not send this entire package or every prompt as one giant task. All 36 prompts are independent as instructions, but sequential as code changes.

## Review checklist after each task

- Were **tests actually run**? Is the full test result clearly stated?
- Was any value in spec §4 / §11.1 altered or an acceptance test weakened? If so, reject.
- Did Codex change only the target slice and integrate it?
- Did it add unrequested dependencies, outbound calls, data deletion, or conversation-content input? Reject.
- Did it attempt Windows-specific validation on Linux and wrongly claim success? Mark deferred and test on Windows.
- Is the PR green and merged before proceeding? Record its SHA/PR in `todo.md`.

## Files and decision boundaries

- `AGENTS.md` — automatically discovered repository guidance for Codex.
- `prompts/01_...md` to `prompts/36_...md` — complete standalone implementation prompts, code-tagged `text`.
- `PROMPTS.md` — single combined prompt collection (identical content).
- `BLUEPRINT.md` — architecture / phase breakdown; `todo.md` — session and subtask tracking.
- `DECISIONS.md` — environment choices and open owner decisions; `TRACEABILITY.md` — spec-to-test coverage; `ACCEPTANCE.md` — target-Windows sign-off.
- `docs/SPEC_TEXT.txt` — machine-extracted convenience text. **Authoritative source:** `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf`.

**Open decision:** proposed port `5062` has not been checked against the user's existing Pareto / IMR tools. Do not describe it as verified.
