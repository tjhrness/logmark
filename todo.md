# IMR Control Chart Tool — Build Checklist

**Companion to:** `BLUEPRINT.md` (22 steps) and `SPEC.md` (**v1.1**, 26 Sep 2026 — standard moving-range sigma)
**How to use:** tick as you go. Do not skip a section to get ahead — the ordering is the safety mechanism.

**The rule for every single step, all 22:**

1. `/clear`, then `/step N` (or paste the prompt). One step only. Wait for it to finish.
2. Look at the last line of the test run: it must say `passed` with no `failed` and no `error` — not "green except that one".
3. Read the AI's plain-English summary. If it says it "decided" something or "adjusted a test", stop and paste the summary to Riya.
4. Do the step's **Verify** items below. None of them need you to read code.
5. Tick the step here, and add one line to your build log (date, step, anything odd).

If 2–4 fail, fix it before the next step. Debt compounds across 22 steps.

---

## 0. Before you write a single line of code

### 0.1 Decisions — settled on 26 Sep 2026

- [x] **Spec defaults (Appendix A)** — no changes from you; v1.1 stands on them
- [x] **Sigma method** — D1 and D2 reversed: sigma comes from the average moving range (÷ 1.128 on the I chart; 0.7557 × on the MR chart). Recorded in SPEC.md v1.1 Appendix B
- [x] **D3 kept** — all eight rules on the MR chart; rationale recorded in Appendix B ("see every signal, judge it myself; MR Rules 2–8 are worth a look, not act on it")
- [x] **One default whose reason changed:** minimum rows stays at **3**. v1.0's reason (the plain-SD MR chart needed 2 moving ranges) is gone; the new reason is that a 1-point MR chart can show nothing. Your interview answer was 2 — say so before Step 1 if you want it back (one constant) — **kept at 3** (owner, 26 Sep 2026)
- [x] **Blueprint decisions BD1–BD21** (BLUEPRINT.md §1.6) — a two-minute veto pass. The ones most worth a look: — **no vetoes** (owner, 26 Sep 2026)
  - [x] BD1: plain hyphen for minus signs everywhere (`-1 SD`, `-3.200`), so Excel and the tests never trip on a typographic minus
  - [x] BD4: a blank line *between* rows rejects the file; blank lines at the *end* are ignored
  - [x] BD18: a failed upload wipes the previous results off the screen
  - [x] BD6: timestamps in local time, `YYYY-MM-DD HH:MM:SS`

### 0.2 Environment

- [x] Python 3.11 installed (`python --version` in a terminal shows 3.11.x) — 3.11.15 in the Claude Code cloud container
- [x] VS Code with the Claude Code extension working — *n/a: building in a Claude Code cloud session on repo `tjhrness/logmark`*
- [x] New folder `imr-chart-tool`, opened in VS Code — *n/a: building in a Claude Code cloud session on repo `tjhrness/logmark`*
- [x] Virtual environment created and activated in that folder (`python -m venv .venv`, then `.venv\Scripts\activate`) — the terminal prompt shows `(.venv)` — *n/a: building in a Claude Code cloud session on repo `tjhrness/logmark`*
- [x] `SPEC.md` (**v1.1** — the file delivered with this checklist, not the v1.0 PDF/Markdown), `BLUEPRINT.md`, `todo.md` and `CLAUDE.md` copied into the folder root — done, commit `9511686`
- [x] `git init`, then a first commit containing those four files, **before Step 1** — done, commit `9511686`, pushed to `claude/bold-curie-bev803`
- [x] A `.gitignore` with `.venv/`, `__pycache__/`, `.pytest_cache/` (ask Claude Code for it in a throwaway session, or type it yourself) — done
- [x] Your `/step` command from the Pareto build works here too (it reads `### Step N — Title` + one ```` ```text ```` block from BLUEPRINT.md). If not, paste prompts by hand — added as `.claude/commands/step.md`
- [ ] Empty build-log file created (outside the coding tool)
- [ ] Excel to hand — you need it at Step 21 and at the end

---

## 1. Guardrails — things the AI will try to "helpfully" undo

Each is a deliberate decision that a code-generation tool will read as an oversight. Most are enforced by `tests/test_guardrails.py` from Step 1, but check them by eye in the summaries, especially at the steps marked.

- [ ] **Sigma comes from the average moving range, never from STDEV.S.** I chart: average moving range ÷ 1.128. MR chart: centred on the average moving range, sigma 0.7557 × it. (Steps 1, 2, 3, 16.) If a summary mentions "sample standard deviation", "stdev" or "STDEV.S" as the basis of the lines — stop
- [ ] **1.128 and 0.7557 appear once each**, as named constants at the top of `imr.py`; the shortcuts 2.66 and 3.267 never appear. The guardrail test checks this — if the AI ever edits that test, stop
- [ ] **All eight rules on the MR chart.** Not "Rule 1 only, as Minitab does" — your deliberate choice (D3). (Steps 10, 16)
- [ ] **MR points start at 2.** There is no MR point 1. (Steps 3, 10, 13)
- [ ] **A point exactly on a line is on neither side** and breaks runs. (Steps 4–10)
- [ ] **One entry per run.** A 12-point run is one observation, never four. (Steps 6–8)
- [ ] **Window rules list only the out-of-zone points**, and name the window. (Step 9)
- [ ] **Bad cells reject the whole file.** No skipping, no "fill with the average". (Step 12)
- [ ] **One file, `imr.py`.** No `utils.py`, no `templates/` folder, no second module
- [ ] **No pandas, no numpy import, no internet, nothing saved to disk**
- [ ] **Localhost only** — `127.0.0.1`, never `0.0.0.0`. (Step 19)
- [ ] **Tests are never edited to make code pass.** If a summary says "updated the test to match", stop and ask Riya

---

## 2. Foundation (Steps 1–3)

**Step 1 — Scaffold, constants, data model, guardrail test**

- [ ] Built
- [ ] Tests green
- [ ] Verify: in the terminal, `python imr.py` prints a "not built yet" line and exits
- [ ] Verify: `requirements.txt` has exactly three lines (flask, matplotlib, pytest), each with `==` and a version number
- [ ] Verify: the summary mentions a guardrail test that checks 1.128 and 0.7557 appear once each, 2.66 / 3.267 never, and no "stdev"
- [ ] Watch for: extra files beyond `imr.py`, `requirements.txt`, `tests/conftest.py`, `tests/test_guardrails.py`

**Step 2 — Moving ranges, I-chart statistics and display formatting**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary says I-chart sigma = average moving range ÷ 1.128
- [ ] Verify: the summary mentions the "level shift" test — sigma stays small when the data jumps from 10 to 20, unlike STDEV.S
- [ ] Watch for: any mention of STDEV.S, "sample standard deviation" or "population SD" as the basis of the lines — wrong method

**Step 3 — MR series and MR-chart statistics**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary says MR point numbers start at 2
- [ ] Verify: the MR chart is centred on the average moving range, sigma = 0.7557 × it, and the +3 SD line comes out at about 3.267 × the average moving range
- [ ] Verify: a perfectly straight line is **not** treated as an error any more

---

## 3. Rule engine (Steps 4–10) — the heart of the tool

**Step 4 — Zone predicates and difference signs**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary states that a value exactly on a line counts as neither side

**Step 5 — Rule 1 and observation formatting**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary quotes the example sentence "Rule 1 — One point beyond 3 SD: point 3 (value 3.500) is above the +3 SD line (3.000)."

**Step 6 — Maximal runs and Rule 2**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary confirms twelve points above the mean give **one** entry, not four

**Step 7 — Rules 7 and 8**

- [x] Built
- [x] Tests green
- [ ] Verify: E14 (a point on the +1 SD line) does not fire Rule 7, and E9 (all points on ±1 SD) does not fire Rule 8

**Step 8 — Rules 3 and 4**

- [x] Built
- [x] Tests green
- [ ] Verify: E4's peak (point 7) is in both the rising and the falling entry; E5's tie stops Rule 3

**Step 9 — Rules 5 and 6**

- [x] Built
- [x] Tests green
- [ ] Verify: E11 is one entry listing points 1, 3, 4 with window 1–5 (point 5 inside the window but not listed)
- [ ] Verify: two windows that touch but don't overlap stay as two entries

**Step 10 — `detect_all` and the fourteen worked examples**

- [x] Built
- [x] Tests green — all fourteen examples
- [ ] Verify: the summary says **no** worked example disagreed with the engine. If it reports a disagreement, stop: bring the summary to Riya before anything else. This is the most important check in the build before Step 21
- [ ] Watch for: the AI "correcting" the E4/E5/E14 expectations back to v1.0's shorter lists (SPEC v1.1 and the Step 10 tests agree on the complete lists)
- [ ] Commit tag optional: `git tag engine-done` so you can always get back here

---

## 4. Input (Steps 11–12)

**Step 11 — File-level parsing and validation (V02–V07)**

- [x] Built
- [x] Tests green: one per code V02–V07, plus "several problems reported together"
- [ ] Verify: the summary quotes at least one message in the three-part shape (what happened · where · what to do)

**Step 12 — Cell values and `parse_csv` (V08, V09)**

- [x] Built
- [x] Tests green
- [ ] Verify: `nan`, `1,234`, `$5`, `5%` and blank cells are all rejected; `-3.2e2` and `  12.5  ` accepted
- [ ] Verify: a bad cell message gives both the Excel row **and** the point number
- [ ] Verify: minimum is 3 rows (unless you changed it in 0.1); the message no longer says it's "needed to draw a Moving Range chart"

---

## 5. Output (Steps 13–16)

**Step 13 — Chart rendering**

- [x] Built
- [x] Tests green
- [ ] Verify: the summary describes the sample images: black dotted mean; red dotted ±1 and ±2; red solid ±3; labels at the right edge; every point numbered; black circles and red triangles; legend
- [ ] Verify: no image files were added to the repository

**Step 14 — Observations CSV builder**

- [ ] Built
- [ ] Tests green
- [ ] Verify: header is exactly `field,chart,rule_no,rule_name,direction,points,values,line_or_window,description`

**Step 15 — Column-section HTML and the standalone report**

- [ ] Built
- [ ] Tests green
- [ ] Verify: the summary table has an "Average moving range (MR-bar)" row and a sigma row labelled "Sigma (MR-bar / 1.128)" (I) or "Sigma (0.7557 x MR-bar)" (MR)
- [ ] Verify: the report has no form, no download links, and no web addresses
- [ ] Verify: "(below 0, not drawn)" appears only on the MR table's negative lines

**Step 16 — The analysis pipeline (V10, W01)**

- [ ] Built
- [ ] Tests green
- [ ] Verify: identical values → the column is rejected, the others still work; a straight line → charted normally (its MR chart shows one Rule 7 pattern — expected); 15 rows → warning, charts still drawn
- [ ] Watch for: any mention of "V11" being implemented — it is retired in SPEC v1.1
- [ ] Verify: the summary says the same file twice gives identical output

---

## 6. The app (Steps 17–19)

**Step 17 — Upload page and `/analyze`**

- [ ] Built
- [ ] Tests green
- [ ] Verify: the summary confirms a crash shows a plain "Something went wrong…" page, with details only in the console

**Step 18 — Downloads**

- [ ] Built
- [ ] Tests green
- [ ] Verify: filenames follow `{file}_IMR_report.html`, `{file}_observations.csv`, `{file}_{column}_I.png` / `_MR.png`, with spaces turned into `_`

**Step 19 — Entry point and README**

- [ ] Built
- [ ] Tests green
- [ ] **First real run.** In the terminal, `python imr.py`: the browser opens by itself on the upload page, the console shows the address
- [ ] Upload any small CSV of your own with an `IMR_Field_` column: charts appear with numbered points
- [ ] Try the three downloads; each saves a file
- [ ] Ctrl+C in the terminal stops it
- [ ] Start it twice (second terminal): the second one picks port 5001 and says so
- [ ] Read README.md: could you follow it in six months without this conversation?
- [ ] README says the lines use the average moving range (standard IMR method) and will not match an Excel STDEV.S calculation

---

## 7. Sample data and the answer key (Steps 20–21)

**Step 20 — Sample dataset**

- [ ] Built
- [ ] Tests green
- [ ] Verify: the summary lists, for each of the nine columns, where the pattern is and every rule it triggers on each chart
- [ ] Open `sample/sample_imr.csv` in Excel: 40 rows, ten columns, plain numbers, a Notes column with text
- [ ] Watch for: any change to `imr.py` in this step — there should be none

**Step 21 — Answer key and acceptance test (OWNER GATE — the AI does not commit)**

- [ ] Built; files staged, **not committed**
- [ ] Tests green
- [ ] The AI's own hand check of Rule5 and Rule7 matched
- [ ] **Your check in Excel, using `docs/answer_key_check.md` (about 30 minutes — Appendix C.1).** No STDEV.S anywhere — every line comes from the moving ranges:
  - [ ] IMR_Field_Rule5 (column E): `=AVERAGE(E2:E41)` matches the mean to 3 decimals
  - [ ] IMR_Field_Rule5: moving ranges in a spare column (`=ABS(E3-E2)` filled down to row 41); their `=AVERAGE` matches the "Average moving range" row
  - [ ] IMR_Field_Rule5: sigma = average moving range ÷ 1.128 matches the sigma row
  - [ ] IMR_Field_Rule5: all seven lines match (mean + k × sigma)
  - [ ] IMR_Field_Rule5: the points listed for Rule 5 really are 2-of-3 beyond the ±2 SD line, same side
  - [ ] IMR_Field_Rule7 (column G): mean, average moving range, sigma and the ±1 SD lines match
  - [ ] IMR_Field_Rule7: the listed points really are 15+ in a row strictly between the ±1 SD lines
  - [ ] IMR_Field_Rule1 MR chart (column A): moving ranges via `=ABS(A3-A2)` filled down; centre = their average; sigma = 0.7557 × average; +3 SD ≈ 3.267 × average; −2 and −3 SD below zero
- [ ] All matched → `git commit -m "Step 21: answer key (owner-verified)"`
- [ ] Anything differed → **do not commit**; bring the difference to Riya

---

## 8. Finish (Step 22)

**Step 22 — Final audit, pinning and tag**

- [ ] Built
- [ ] Tests green, including the performance test (10 columns × 100 rows in under 5 seconds)
- [ ] Verify: the summary lists which §12 test-plan bullets needed new tests (and none failed)
- [ ] Verify: the summary lists anything in CLAUDE.md that could not be checked automatically — check those by eye
- [ ] Verify: it did not change `imr.py` (an audit step reports bugs; it doesn't fix them)
- [ ] Tagged `v1.0`

---

## 9. Manual acceptance checklist (SPEC.md §12.9) — no code reading

Do this yourself after Step 22, with `python imr.py`.

- [ ] 1. `python imr.py` opens the browser on the upload page
- [ ] 2. Upload `sample/sample_imr.csv`: nine sections appear; the Notes column is not charted
- [ ] 3. Every point on every chart carries a number; pattern points are red triangles, the rest black circles
- [ ] 4. Seven lines on the I chart: mean black dotted, ±1/±2 red dotted, ±3 red solid, each labelled at the right
- [ ] 5. The MR chart sits directly under the I chart at the same width; its first point is numbered 2
- [ ] 6. Under each chart: the summary table, then the observations (or "No Nelson patterns detected.")
- [ ] 7. IMR_Field_Clean shows no patterns on either chart
- [ ] 8. The IMR_Field_Rule5 observation lists only the out-of-zone points and names the window
- [ ] 9. For one column, recompute in Excel the mean, the moving ranges, their average, and sigma (= average ÷ 1.128) — they match the summary table to 3 decimals
- [ ] 10. Upload a file with 15 rows: the warning appears above the I chart; charts still render
- [ ] 11. Upload a file with one blank cell: file rejected; the message names the column, the Excel row and the point
- [ ] 12. Download the report; turn Wi-Fi off; open it — charts and text all intact
- [ ] 13. Download a PNG: it's the same image as on the page
- [ ] 14. Download the observations CSV; open in Excel: the columns match SPEC.md §6.7

Extra checks worth two minutes each:

- [ ] Upload a `.xlsx` by mistake: a clear "not a .csv file" message, no crash
- [ ] Upload a file with no `IMR_Field` column: the message lists the columns it did find
- [ ] Upload a file with a bad cell **and** a ragged row: both problems listed at once
- [ ] Upload a good file, then a bad one: the old results disappear
- [ ] Upload a file with a column name containing a space: the PNG downloads with `_` in its name
- [ ] Put a 30-row column of identical values beside a normal column: that column shows a red box, the other charts normally
- [ ] Put a perfectly straight column (1, 2, 3 … 30) in a file: it is charted, not rejected
- [ ] A real dataset of yours (30–100 points): the charts are readable at 100 points and the observations make sense to you as a Black Belt

---

## 10. Done (SPEC.md §13.1)

- [ ] All tests pass (§12.1–12.8)
- [ ] The answer key was independently verified by you in Excel (Step 21)
- [ ] The §12.9 checklist passed (section 9 above)
- [x] D1–D3 settled and recorded in SPEC.md v1.1 Appendix B
- [ ] Final commit and `v1.0` tag in place

---

## 11. Ongoing hygiene

Habits for the length of the build, not one-time boxes.

- [ ] One step per session. Never queue two
- [ ] `/clear` between steps
- [ ] Build log updated after every step
- [ ] Commit after every green step (the AI does it; check `git log` shows it), so you can always walk back one step
- [ ] When the tool loops on the same bug: **stop, start a fresh session**, and restate the problem in one paragraph — what should happen, what actually happens, the exact error text. Repeating the instruction louder does not work
- [ ] When the tool changes something you didn't ask for: re-prompt with explicit boundaries — "only change X; do not modify Y or Z"
- [ ] When a step touches files it wasn't told to: reject and re-scope rather than accept drift
- [ ] Every few steps, re-read section 1 (guardrails) and confirm nothing has quietly been "optimised" away
- [ ] Paste the AI's summary — not the code — to Riya whenever something feels off

---

## 12. After v1.0 (not part of this build)

- [ ] Use it on two or three real datasets before changing anything
- [ ] If you ever need to match a colleague's spreadsheet that uses STDEV.S limits, that's the trigger for an optional sigma-method switch (SPEC Appendix C.3). Write it up as a spec change first — don't bolt it on
- [ ] Packaging as a Windows `.exe` stays out of scope until you actually need to run it somewhere without Python
