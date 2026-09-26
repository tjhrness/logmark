# IMR Control Chart Tool — Build Blueprint & TDD Prompt Series

**Source:** `SPEC.md` — IMR Control Chart Tool Specification **v1.1** (26 September 2026: standard moving-range sigma; all eight rules on both charts)
**Companion:** `todo.md` — the tick-box checklist for this document
**Pattern:** the Pareto Chart Tool pattern. One Python file (`imr.py`), a local Flask server, a browser page, `pytest`, one prompt per `/step`, `/clear` between steps, a git commit after every green step, and the AI's plain-English summary pasted back for a sanity check.

This document turns the specification into an executable build plan: the architecture and build order, two rounds of chunking down to right-sized steps, a right-sizing review, and 22 standalone prompts for a code-generation LLM (Claude Code) working entirely on a local Windows machine. No GitHub, no CI, no network — every step is written, tested and run locally.

---

## Part 0 — How to run this build

1. Do everything in `todo.md` section 0 first. Use **SPEC.md v1.1**, delivered with this blueprint — not v1.0. Changing a default after Step 1 means re-running steps.
2. Open the repository in VS Code with Claude Code. `CLAUDE.md` loads automatically every session; it carries the non-negotiables.
3. For each step, in order: `/clear` → `/step N` (or paste the prompt from Part 4) → wait for it to finish → check the last line of the test run says `passed` with no `failed` or `error` → read its plain-English summary → tick the step in `todo.md` → one line in your build log.
4. If a step ends red, or the summary mentions something it "decided", paste the summary (not the code) to Riya before moving on.
5. Every prompt is self-contained: it says what already exists, what to build, which tests to write first, and when it is done. Never run two steps in one session, and never skip ahead — each prompt assumes the previous ones exist on disk and are green.
6. The AI commits at the end of every step except Step 21, where you verify the answer key by hand before it is committed (SPEC.md §11.4).

If your `/step` command reads prompts out of this file, it relies on the `### Step N — Title` heading followed by a single ```` ```text ```` block. Keep that shape if you ever edit a prompt.

---

## Part 1 — Blueprint

### 1.1 Stack (fixed for the whole build)

Python 3.11 on Windows. Flask for the local server, with page templates held as strings inside `imr.py`. matplotlib with the Agg backend for static PNG charts. Standard library only for everything else: `csv`, `statistics`, `io`, `base64`, `re`, `dataclasses`, `webbrowser`, `threading`, `socket`. No pandas; numpy is present only as matplotlib's dependency and is never imported directly. `pytest` plus Flask's test client for every test. `requirements.txt` pins `flask`, `matplotlib`, `pytest` to the versions used in the build. (SPEC.md §9.1)

### 1.2 Repository layout

```
imr-chart-tool/
  imr.py                 — the whole application, nine banner sections in fixed order (§9.2)
  requirements.txt
  README.md
  CLAUDE.md              — build guardrails (Appendix of this document; create before Step 1)
  SPEC.md                — the specification
  BLUEPRINT.md           — this document
  todo.md                — the checklist
  docs/
    answer_key_check.md  — the owner's Excel check sheet (Step 21)
  sample/
    sample_imr.csv       — 40 rows, one column per rule + a clean column + an ignored Notes column
    sample_answer_key.csv
  tests/
    conftest.py
    test_guardrails.py   — enforces CLAUDE.md mechanically
    test_stats.py
    test_rules.py
    test_parsing.py
    test_render.py
    test_builders.py     — CSV/HTML builders
    test_pipeline.py     — the analyse() pipeline
    test_routes.py
    test_sample.py
```

The nine sections of `imr.py`, each behind a banner comment the guardrail test looks for:

| # | Banner | Holds |
|---|---|---|
| 1 | `# ===== SECTION 1: CONSTANTS =====` | Rule thresholds, tolerance, prefix, limits, figure sizing, port range, rule names |
| 2 | `# ===== SECTION 2: DATA CLASSES =====` | `Series`, `Observation`, `ChartStats`, `ChartResult`, `ColumnResult`, `AnalysisResult`, `ValidationIssue`, `ParsedColumn`, `ParsedFile`, `ValidationErrors` |
| 3 | `# ===== SECTION 3: PARSING AND VALIDATION =====` | bytes → `ParsedFile` or `ValidationErrors` (V02–V09) |
| 4 | `# ===== SECTION 4: STATISTICS =====` | mean, moving ranges, MR̄, sigma, seven lines, display formatting |
| 5 | `# ===== SECTION 5: RULE ENGINE =====` | predicates, eight rule functions, `detect_all` |
| 6 | `# ===== SECTION 6: RENDERING =====` | series → PNG bytes |
| 7 | `# ===== SECTION 7: REPORT AND CSV BUILDERS =====` | observations CSV, column-section HTML, standalone report, and (sub-banner 7.3) the analysis pipeline |
| 8 | `# ===== SECTION 8: FLASK APP AND ROUTES =====` | the page, `/analyze`, the three downloads; the only place Flask is imported |
| 9 | `# ===== SECTION 9: ENTRY POINT =====` | port fallback, browser open, `main()` |

Sections 3–7 never import Flask and are tested without it.

### 1.3 Why this build order

1. **Statistics first, engine second, before any input or screen exists.** The rule engine is where a wrong-but-plausible answer hides: a chart that "looks right" with a mis-detected run is worse than a crash. The engine is built on hand-supplied lines (mean 0, SD 1) and locked against the spec's fourteen worked examples (§5.9) before a single CSV is parsed. The standard moving-range sigma (SPEC.md §4) is built in from the very first line of arithmetic, and a guardrail test from Step 1 keeps the plain sample SD and the rounded shortcut constants out for the rest of the build.
2. **The engine is built in the order of algorithmic risk, one helper at a time.** Predicates and tolerance semantics get their own step (they cause most bugs in this kind of tool). Rule 1 introduces the observation format. Rule 2 introduces the maximal-run helper that Rules 7, 8, 3 and 4 then reuse. The window rules (5, 6) — the only merging algorithm — come last, and `detect_all` closes the engine with the worked examples as its acceptance test.
3. **Parsing after the engine.** Its tests are mechanical (one per validation code) and it is low-risk; until the engine exists there is nothing meaningful to feed.
4. **Rendering isolated, then the builders, then one pipeline step.** `analyse()` is the single integration point; every pure section is proven before it, so the Flask layer stays thin and the "big-bang integration" risk is confined to one step with its own tests.
5. **Flask in two steps (page, then downloads) and the entry point last.** Each is independently clickable.
6. **Sample data in two steps with the owner in between.** The sample and its "each column triggers its rule" tests come first; the answer key and the row-for-row acceptance test come next — and are not committed until the owner has recomputed a column in Excel (§11.4). An answer key copied back from the engine only guards against future regressions; the hand check is what makes "all tests pass" mean anything.

### 1.4 Testing posture

Every step is test-first: the prompt names the tests before the code. Unit tests dominate the statistics, rule engine, parsing and builders (deterministic, no I/O). The rendering tests check PNG validity, sizing and determinism, not pixels. Route tests use Flask's test client — no browser automation. The end-to-end acceptance test compares the tool's observations CSV against the hand-verified answer key row for row (§12.8). The manual checklist in §12.9 is run once at the end, by the owner, with no code reading.

### 1.5 Names fixed for the whole build

Every prompt restates what it needs, but these names are the contract that keeps 22 standalone prompts consistent. Riya can check any step's summary against this list.

- **Section 1:** `D2_CONSTANT=1.128`, `MR_SIGMA_FACTOR=0.7557`, `RULE_2_MIN_RUN=9`, `RULE_3_MIN_RUN=6`, `RULE_4_MIN_RUN=14`, `RULE_5_WINDOW=3`, `RULE_5_MIN_COUNT=2`, `RULE_6_WINDOW=5`, `RULE_6_MIN_COUNT=4`, `RULE_7_MIN_RUN=15`, `RULE_8_MIN_RUN=8`, `ON_LINE_TOLERANCE=1e-9`, `IMR_PREFIX`, `MAX_UPLOAD_BYTES`, `MIN_DATA_ROWS=3`, `WARN_BELOW_POINTS=20`, `MAX_BAD_CELLS_LISTED=20`, `DECIMALS=3`, `FIG_MIN_WIDTH_IN`, `FIG_WIDTH_PER_POINT_IN`, `FIG_HEIGHT_IN`, `FIG_DPI`, `TICK_EVERY_POINT_UP_TO`, `PORT_CANDIDATES`, `LINE_KS`, `RULE_NAMES`
- **Section 2:** `Series(point_numbers, values)`; the §9.4 dataclasses, with `ChartStats(n, mean, mr_bar, sigma, lines)`; `ValidationIssue(code, severity, message)`; `ParsedColumn(name, index, values)`; `ParsedFile(source_filename, stem, n_rows, columns)`; `ValidationErrors(Exception)` with `.issues`
- **Section 3:** `read_table` (returns header, rows and a list of V05–V07 issues), `sanitise_name`, `stem_of`, `NUMBER_RE`, `parse_number`, `parse_csv`
- **Section 4:** `mean_of`, `moving_ranges`, `lines_for`, `i_chart_stats`, `mr_chart_stats`, `fmt`, `individuals_series`, `moving_range_series`, `lines_below_zero`
- **Section 5:** `on_line`, `above_mean`, `below_mean`, `beyond_above`, `beyond_below`, `within_1`, `outside_1`, `diff_sign`, `diff_signs`, `line_name`, `fmt_pairs`, `fmt_points`, `fmt_values`, `fmt_span`, `maximal_runs`, `window_observations`, `rule_1` … `rule_8` (each `rule_k(series, lines, field="", chart="")`), `detect_all`, `pattern_points`
- **Section 6:** `figure_width_inches`, `render_chart`
- **Section 7:** `points_field`, `build_observations_csv`, `warning_text`, `build_summary_table_html`, `build_observations_html`, `build_column_section_html`, `build_report_html`, `timestamp_text`, `analyse_column`, `analyse`
- **Section 8:** `LAST_RESULT`, `PAGE_TEMPLATE`, `create_app`, `reset_state`
- **Section 9:** `find_free_port`, `open_browser_later`, `main`

### 1.6 Decisions this blueprint makes — veto before Step 1

The spec leaves these to the developer, or says "may". A build with standalone prompts cannot leave them open, so they are fixed here. Any one can be changed before Step 1 by editing the prompts; after Step 1 it is a re-run.

| ID | Decision |
|---|---|
| BD1 | Every generated string uses the plain ASCII hyphen-minus for negatives and for the line names `-1 SD`, `-2 SD`, `-3 SD` — page, chart labels, descriptions and CSV alike. The typographic minus appears nowhere. The em dash (`Rule 1 — …`) and the en dash in point spans (`points 1–12`) in the §5.5 sentences are kept exactly; they are punctuation, not signs. (§4.5 permits this; it removes an Excel and testing headache.) |
| BD2 | `ColumnResult.index` / `ParsedColumn.index` is the 0-based position among the *charted* columns in file order — the number the PNG download route uses. |
| BD3 | The pipeline (`analyse_column`, `analyse`) lives at the end of section 7 under a sub-banner, so it stays Flask-free and unit-testable. |
| BD4 | A completely blank line *between* data rows is a ragged row (0 cells) and rejects the file with V07; it is not silently skipped, because skipping would break the row-number ↔ point-number relationship the error messages rely on. Completely blank lines at the very *end* of the file (after the last non-blank row) are ignored, because Excel and text editors leave them behind. |
| BD5 | V07 lists at most 20 offending rows, then "… and m more", the same courtesy the spec gives V08. V08 is one line per bad cell (up to 20) plus one "… and m more" line. |
| BD6 | Timestamps are local time, `YYYY-MM-DD HH:MM:SS`. |
| BD7 | The observations CSV uses `\n` line endings and the `csv` module's default RFC 4180 quoting. |
| BD8 | The optional legend (circle = data point, triangle = Nelson pattern point) is included on both charts. |
| BD9 | A guardrail test (`tests/test_guardrails.py`) enforces CLAUDE.md mechanically from Step 1: banner order; 1.128 and 0.7557 appear exactly once each (their definitions) and 2.66 / 3.267 never; no "stdev", "pstdev" or "variance" text; no pandas, no direct numpy; Flask imported only in section 8; standard thresholds. |
| BD10 | Nine test files, as listed in SPEC v1.1 §9.6 — including `test_guardrails.py`, `test_builders.py` and `test_pipeline.py`, which v1.0 did not name. |
| BD11 | Unexpected errors (§7.4) are caught by a try/except inside the `/analyze` route only; no application-wide error handler. |
| BD12 | The equal-values tolerance for differences (§5.1 `diff_i`) is symmetric: `abs(a − b) ≤ 1e-9 × max(1, |a|, |b|)`. |
| BD13 | The upload form's file field is named `file`; the page's download link texts are "Download report (HTML)", "Download observations (CSV)" and "Download PNG". |
| BD14 | Rule functions take `field` and `chart` as optional keyword arguments and stamp them onto their observations; `detect_all` passes them through. Tests can omit them. |
| BD15 | The AI commits at the end of every step, except Step 21 (answer key), which the owner commits after the hand check. |
| BD16 | Anything printed to the Windows console (startup line, port message) is plain ASCII, because legacy console code pages choke on dashes. |
| BD17 | Chart pixel width is not asserted exactly: `bbox_inches="tight"` trims whitespace, so tests check the `figure_width_inches(n)` formula directly and that pixel width grows with N (§12.6 nuance). |
| BD18 | A rejected or failed upload clears the previous result. What is on screen and what the download links serve are therefore always from the same file, and downloads after a failed upload return the §7.3 404. |
| BD19 | The zone predicates take a value and the lines dict (`above_mean(v, lines)`), not a position; the rule functions loop over positions. Same semantics as §5.1, simpler to test. |
| BD20 | The results page embeds chart images as base64 data URIs (the same bytes the PNG route serves). Download links are added to the page in Step 18, the same step that creates the routes they point at, so no link ever points at a missing route. |
| BD21 | The file-size check (V03) is done in the parser on the uploaded bytes; Flask's own `MAX_CONTENT_LENGTH` is not set, because it would reply with a generic 413 instead of the V03 message. |

### 1.7 Spec corrections — already in SPEC v1.1

Found while planning, and folded into SPEC.md v1.1 so the spec and the tests agree:

1. **Sigma method.** D1 and D2 reversed on 26 Sep 2026: sigma comes from the average moving range (`MR̄ ÷ 1.128` on the I chart, `0.7557 × MR̄` on the MR chart). D3 (all eight rules on the MR chart) kept, with its rationale recorded. V11 retired — it can no longer occur.
2. **E5 (§5.9) no longer claims Rule 2 fires.** It has 8 points and Rule 2 needs 9.
3. **E4 and E5 list every observation they trigger.** With mean 0 and SD 1 supplied, values of 4–7 are several SDs above the mean, so Rules 1, 5, 6 and 8 fire on E4, and Rules 1, 5 and 6 on E5. §12.3 asks for the complete set.
4. **E14 also fires Rule 2** (all fifteen values are above the mean).
5. **§12.6 pixel width** is no longer asserted exactly under `bbox_inches="tight"` (BD17).
6. **V07 lists at most 20 rows** (BD5); **trailing blank lines** are ignored (BD4); **hyphen-minus everywhere** (BD1); three extra test files and the pipeline sub-banner (BD3, BD10).

---

## Part 2 — Chunking

### Round 1 — chunks (too big to build safely in one pass)

| # | Chunk | Spec refs |
|---|---|---|
| A | Scaffold: layout, dependencies, constants, data model, guardrail test | §9.1, §9.2, §9.4, §9.6, §13.3, §5.2 |
| B | Statistics: moving ranges, MR̄, sigma, lines, display formatting | §4.1–4.5 |
| C | Rule engine: predicates, eight rules, `detect_all`, worked examples | §5, §12.2–12.4 |
| D | Parsing and validation: file-level and cell-level checks | §3, §7.1 V02–V09, §7.2 |
| E | Rendering: PNG per chart | §6.2, §10 |
| F | Builders and pipeline: observations CSV, section HTML, report, `analyse()` incl. V10/W01 | §4.6, §6.1, §6.3–6.7, §7.3 |
| G | Web app and entry point: page, `/analyze`, downloads, port fallback, browser | §2.2, §7.1 V01, §7.3, §7.4, §8, §9.3, §9.5 |
| H | Sample data, answer key, acceptance | §11, §12.8, §12.9, §13 |

### Round 2 — steps

Each chunk splits on its natural seams: one helper or one validation layer per step, so a failing test points at one thing.

| Chunk | Steps |
|---|---|
| A | 1 Scaffold, constants, data model, guardrail test |
| B | 2 Moving ranges, I-chart statistics and display formatting · 3 MR series and MR-chart statistics |
| C | 4 Zone predicates · 5 Rule 1 and observation formatting · 6 Maximal runs and Rule 2 · 7 Rules 7 and 8 · 8 Rules 3 and 4 · 9 Rules 5 and 6 · 10 `detect_all` and the fourteen worked examples |
| D | 11 File-level parsing (V02–V07) · 12 Cell values and `parse_csv` (V08, V09) |
| E | 13 Chart rendering |
| F | 14 Observations CSV · 15 Column-section HTML and standalone report · 16 The analysis pipeline (V10, W01) |
| G | 17 Upload page and `/analyze` · 18 Downloads · 19 Entry point and README |
| H | 20 Sample dataset · 21 Answer key and acceptance test (owner gate) · 22 Final audit and tag |

---

## Part 3 — Right-sizing review

Each step was checked against two failure modes: **too big** (more than one untested concern, or unverifiable until the next step exists) and **too small** (code with no caller — orphaned until something later wires it in). Adjustments made in review:

- **Constants and data classes merged into Step 1.** Both are declarations; separately they are too small, and the guardrail test needs both to exist.
- **Predicates kept separate from Rule 1.** The tolerance rule ("exactly on a line belongs to neither side") decides E9 and E14 and breaks runs in five rules. It deserves its own tests before any rule uses it.
- **Rule 2 alone, then Rules 7 + 8.** Rule 2 introduces `maximal_runs`, which three more rules reuse; proving the helper on the simplest labels first is cheaper than debugging it inside a two-rule step. Rules 7 and 8 then share one step because they are the same shape with different predicates.
- **Rules 3 + 4 together, Rules 5 + 6 together.** Same reasoning: shared mechanism (difference signs; windows with merging), different thresholds.
- **`detect_all` is its own step.** The fourteen examples need every rule present; encoding them one rule at a time would test fragments and miss the "also fires" cases.
- **Parsing split file-level / cell-level.** `read_table` is fully testable, returns its V05–V07 issues instead of raising them, and stays as the inner function `parse_csv` calls — no orphan.
- **CSV builder before the report builder.** The CSV is the acceptance artefact; the report reuses the same observation data and is bigger. Each is unit-tested on hand-built results before the pipeline exists, then the pipeline calls both.
- **The pipeline is a step, not a paragraph in the Flask step.** It is where V10/W01 live and where every section meets; testing it without HTTP keeps the Flask step thin.
- **Flask split page / downloads.** Step 17 is clickable on its own; Step 18 adds three routes and the links that point at them, so no link ever points at a route that does not exist.
- **Sample and answer key kept apart** because §11.4 puts the owner between them.
- **Step 22 stays.** Pinning, audit and tag are small but they are the "done" definition of §13.1.

No step leaves dead code: every function written in a step is called by that step's tests and, by Step 16, by the running pipeline; every route is reachable from the page by Step 18.

**Final step list (22 steps):**

1. Scaffold, constants, data model, guardrail test
2. Moving ranges, I-chart statistics and display formatting
3. MR series and MR-chart statistics
4. Zone predicates and difference signs
5. Rule 1 and observation formatting
6. Maximal runs and Rule 2
7. Rules 7 and 8
8. Rules 3 and 4
9. Rules 5 and 6
10. `detect_all`, `pattern_points`, and the fourteen worked examples
11. File-level parsing and validation (V02–V07)
12. Cell values and `parse_csv` (V08, V09)
13. Chart rendering
14. Observations CSV builder
15. Column-section HTML and the standalone report
16. The analysis pipeline (V10, W01)
17. Upload page and `/analyze`
18. Downloads
19. Entry point and README
20. Sample dataset
21. Answer key and acceptance test — owner verification gate
22. Final audit, pinning and tag

---

## Part 4 — Prompts for a code-generation LLM

Each prompt is self-contained. Paste one per session, in order; verify the suite is green; move to the next. Every prompt ends the same way: the whole suite green, a commit, and a plain-English summary.

### Step 1 — Scaffold, constants, data model, guardrail test

```text
You are building the IMR Control Chart Tool: a personal, single-user, local web application in Python 3.11 on Windows. The owner uploads a CSV in a browser page and gets an Individuals (I) chart and a Moving Range (MR) chart for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts and every detected pattern written out. The whole application lives in ONE file, imr.py; tests, sample data and documents live beside it. Everything is local: no GitHub, no CI, no network — you verify by running pytest yourself.

Before doing anything, read CLAUDE.md (non-negotiable guardrails) and SPEC.md (the full specification) in the repository root. They already exist, as do BLUEPRINT.md and todo.md. Never modify any of those four files. A git repository is already initialised with those files committed.

This step creates the skeleton every later step builds on: the file layout, the dependency list, the constants, the data model, and a guardrail test that mechanically enforces CLAUDE.md for the rest of the build. No business logic yet.

1. Create requirements.txt listing flask, matplotlib and pytest. Install them into the active Python environment, then pin each line to the exact version that got installed (e.g. flask==3.0.3). Nothing else goes in this file: no pandas, no numpy line (numpy arrives only as matplotlib's own dependency and is never imported directly).

2. Create imr.py with, in this order:
   - a module docstring (one paragraph: what the tool is, "python imr.py" to run, "pytest" to test)
   - an import block containing only standard-library modules (base64, csv, dataclasses, html, io, re, socket, statistics, sys, threading, time, traceback, webbrowser; from dataclasses import dataclass, field; from datetime import datetime) plus "import matplotlib" followed immediately by matplotlib.use("Agg") and then "import matplotlib.pyplot as plt". Do NOT import flask here: Flask is imported only inside section 8, later in the build.
   - nine banner comments, exactly these strings, in exactly this order, each on its own line, with the section's code (or nothing yet) beneath it:
     # ===== SECTION 1: CONSTANTS =====
     # ===== SECTION 2: DATA CLASSES =====
     # ===== SECTION 3: PARSING AND VALIDATION =====
     # ===== SECTION 4: STATISTICS =====
     # ===== SECTION 5: RULE ENGINE =====
     # ===== SECTION 6: RENDERING =====
     # ===== SECTION 7: REPORT AND CSV BUILDERS =====
     # ===== SECTION 8: FLASK APP AND ROUTES =====
     # ===== SECTION 9: ENTRY POINT =====
   - Section 9 contains only a placeholder: if __name__ == "__main__": print("IMR Control Chart Tool: the server is not built yet. Run pytest.")

3. Section 1 — constants, module-level, named exactly:
   RULE_2_MIN_RUN = 9; RULE_3_MIN_RUN = 6; RULE_4_MIN_RUN = 14; RULE_5_WINDOW = 3; RULE_5_MIN_COUNT = 2; RULE_6_WINDOW = 5; RULE_6_MIN_COUNT = 4; RULE_7_MIN_RUN = 15; RULE_8_MIN_RUN = 8
   ON_LINE_TOLERANCE = 1e-9
   IMR_PREFIX = "IMR_Field"
   MAX_UPLOAD_BYTES = 10 * 1024 * 1024; MIN_DATA_ROWS = 3; WARN_BELOW_POINTS = 20; MAX_BAD_CELLS_LISTED = 20
   DECIMALS = 3
   FIG_MIN_WIDTH_IN = 10.0; FIG_WIDTH_PER_POINT_IN = 0.2; FIG_HEIGHT_IN = 4.5; FIG_DPI = 100; TICK_EVERY_POINT_UP_TO = 50
   PORT_CANDIDATES = range(5000, 5011)
   LINE_KS = (-3, -2, -1, 0, 1, 2, 3)
   D2_CONSTANT = 1.128        — with a one-line comment: I-chart sigma = average moving range / D2_CONSTANT (SPEC.md §4.2)
   MR_SIGMA_FACTOR = 0.7557   — with a one-line comment: MR-chart sigma = MR_SIGMA_FACTOR x average moving range (SPEC.md §4.3)
   These two are the only place the numbers 1.128 and 0.7557 may ever appear in imr.py; everything else refers to them by name.
   RULE_NAMES: dict[int, str] mapping 1..8 to exactly these strings: "One point beyond 3 SD"; "Nine or more points on one side of the mean"; "Six or more points steadily rising or falling"; "Fourteen or more points alternating up and down"; "Two of three points beyond 2 SD (same side)"; "Four of five points beyond 1 SD (same side)"; "Fifteen or more points within 1 SD of the mean"; "Eight or more points beyond 1 SD, either side"
   These thresholds are the standard Nelson values. They are never exposed in the interface and never changed.

4. Section 2 — dataclasses (use @dataclass; plain lists, dicts and sets; no methods beyond what @dataclass gives):
   Series(point_numbers: list[int], values: list[float])
   Observation(field: str, chart: str, rule_no: int, rule_name: str, direction: str, points: list[int], values: list[float], span: tuple[int, int], line_or_window: str, description: str)
   ChartStats(n: int, mean: float, mr_bar: float, sigma: float, lines: dict[int, float])   — mean is the centre line (the plain mean on the I chart, the average moving range on the MR chart)
   ChartResult(kind: str, point_numbers: list[int], values: list[float], stats: ChartStats, observations: list[Observation], pattern_points: set[int], png: bytes)
   ColumnResult(name: str, index: int, n: int, warning: str | None, rejected_reason: str | None, individuals: ChartResult | None, moving_range: ChartResult | None)
   AnalysisResult(source_filename: str, stem: str, analysed_at: datetime, columns: list[ColumnResult], report_html: str, observations_csv: str)
   ValidationIssue(code: str, severity: str, message: str)   — severity is "F", "C" or "W"
   ParsedColumn(name: str, index: int, values: list[float])   — index is the 0-based position among the charted columns, in file order
   ParsedFile(source_filename: str, stem: str, n_rows: int, columns: list[ParsedColumn])
   class ValidationErrors(Exception): constructed with a list of ValidationIssue, stored on self.issues; __str__ returns the messages joined by newlines.

5. tests/conftest.py: insert the repository root at the front of sys.path so every test can "import imr".

6. Tests first, in tests/test_guardrails.py (read imr.py as text with pathlib for the source-level checks; import imr for the rest):
   - the nine banners are present, each exactly once, in the order above
   - imr.D2_CONSTANT == 1.128 and imr.MR_SIGMA_FACTOR == 0.7557
   - the numbers 1.128 and 0.7557 each appear exactly once in imr.py as standalone numbers, and that one occurrence is before the SECTION 2 banner (their definition). Use a regex with lookarounds so 11.128 or 1.1280 are not false matches; comments count too, so no stray copy can creep in
   - the rounded shortcuts 2.66 and 3.267 appear nowhere in imr.py as standalone numbers (same regex approach)
   - the text "stdev", "pstdev" and "variance" appears nowhere in imr.py — the plain sample SD must never be used for the lines (SPEC.md §4.4)
   - no line of imr.py imports pandas; no line imports numpy (matplotlib may import it internally; imr.py may not)
   - no "import flask" or "from flask" statement appears before the SECTION 8 banner (search the text before the banner with a regex anchored at line start)
   - every rule threshold constant has the standard value listed in item 3
   - every dataclass in item 4 exists with exactly the field names listed, in that order (dataclasses.fields)
   - ValidationErrors is an Exception subclass and str() of one built from two issues contains both messages
   Write the tests, run them and watch them fail, then create the files until they pass.

Rules for this step
- Touch only the files named above.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it now or later.

Done when
- pytest passes in full, and "python imr.py" prints the placeholder line and exits.
- Commit: git add -A && git commit -m "Step 1: scaffold, constants, data model, guardrail test"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 2 — Moving ranges, I-chart statistics and display formatting

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: imr.py with nine banner sections (# ===== SECTION 1: CONSTANTS ===== through # ===== SECTION 9: ENTRY POINT =====), section 1 constants (including LINE_KS = (-3, -2, -1, 0, 1, 2, 3), DECIMALS = 3 and D2_CONSTANT = 1.128), section 2 dataclasses including ChartStats(n, mean, mr_bar, sigma, lines: dict[int, float]) and Series(point_numbers, values), tests/conftest.py, and tests/test_guardrails.py which enforces CLAUDE.md mechanically. Sections 3–9 are empty apart from a placeholder print in section 9.

This step implements the moving ranges and the Individuals-chart statistics of SPEC.md §4.1–4.2, and the display formatting of §4.5, in SECTION 4: STATISTICS. Nothing else.

The tool uses the standard IMR method: sigma is estimated from the average moving range, NOT from the plain sample standard deviation of the column. This matters: a shift or a spike inflates the plain SD and hides the very signals the tool exists to find, while the average moving range barely moves.

Implement, in section 4:
- mean_of(values: list[float]) -> float — the ordinary arithmetic mean (statistics.mean is fine).
- moving_ranges(values: list[float]) -> list[float] — [abs(values[i] - values[i-1]) for i = 1 … N−1]: N − 1 numbers. Raise ValueError if fewer than 2 values.
- lines_for(centre: float, sigma: float) -> dict[int, float] — {k: centre + k * sigma for k in LINE_KS}.
- i_chart_stats(values: list[float]) -> ChartStats — n = N; mean = mean_of(values); mr_bar = mean_of(moving_ranges(values)); sigma = mr_bar / D2_CONSTANT; lines = lines_for(mean, sigma). Refer to D2_CONSTANT by name — the number 1.128 must not be typed in section 4. When every value is identical, mr_bar and sigma are exactly 0.0 and all seven lines equal the mean; do not raise — the caller decides what a zero sigma means.
- fmt(x: float) -> str — the number to exactly DECIMALS (3) decimal places, fixed notation (42.3 → "42.300", -0.5 → "-0.500"), plain ASCII hyphen-minus for negatives, and negative zero normalised so it never prints "-0.000". Every displayed number in the whole tool goes through this helper. It is used for display only — nothing that is compared is ever rounded.

Tests first, in tests/test_stats.py. Compute every expected value independently in the test (by hand or with the literal 1.128) — never by calling imr's own constants — so the test would catch a wrong constant:
- moving_ranges([1, 4, 2, 2, 9]) == [3, 2, 0, 7]; its length is N − 1; one value raises ValueError; negatives work: moving_ranges([-1.5, 2.0, -0.5]) == [3.5, 2.5].
- mean_of agrees with statistics.mean on integers, decimals, negatives and a mixed series such as [3.2, -1.5, 0.0, 7.75, 2.1].
- lines_for(10.0, 2.0) returns exactly seven keys -3..3 with values 4, 6, 8, 10, 12, 14, 16 (pytest.approx).
- i_chart_stats([10, 12, 9, 11, 13]): n 5, mean 11.0, mr_bar 2.25, sigma == pytest.approx(2.25 / 1.128) (about 1.994681), lines[3] ≈ 16.984043 and lines[-3] ≈ 5.015957.
- i_chart_stats([3.2, -1.5, 0.0, 7.75, 2.1]): mr_bar == pytest.approx((4.7 + 1.5 + 7.75 + 5.65) / 4) and sigma == pytest.approx(mr_bar / 1.128).
- Not the plain SD: for ten 10s followed by ten 20s, mr_bar == pytest.approx(10 / 19), and sigma is less than one fifth of statistics.stdev of the same values (the shift barely moves the moving-range sigma).
- i_chart_stats([5, 5, 5, 5]): mr_bar == 0.0 and sigma == 0.0 exactly, all seven lines equal 5.0.
- fmt(42.3) == "42.300"; fmt(-0.5) == "-0.500"; fmt(1/3) == "0.333"; fmt(2.00049) == "2.000"; fmt(2.0006) == "2.001"; fmt(0) == "0.000"; fmt(-0.0) == "0.000".
Write the tests, watch them fail, then implement until green.

Rules for this step
- Change only section 4 of imr.py and tests/test_stats.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 2: moving ranges, I-chart statistics and fmt"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 3 — MR series and MR-chart statistics

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: sections 1–2 (constants including D2_CONSTANT = 1.128 and MR_SIGMA_FACTOR = 0.7557; dataclasses including Series(point_numbers: list[int], values: list[float]) and ChartStats(n, mean, mr_bar, sigma, lines)), section 4 with mean_of, moving_ranges, lines_for(centre, sigma), i_chart_stats and fmt, tests/test_stats.py and tests/test_guardrails.py.

This step adds the two chart series and the Moving Range chart's statistics (SPEC.md §4.1, §4.3) to SECTION 4: STATISTICS.

Implement, in section 4:
- individuals_series(values: list[float]) -> Series — point_numbers [1 … N], values unchanged, so both charts are handled by the same Series type.
- moving_range_series(values: list[float]) -> Series — values = moving_ranges(values); point_numbers [2, 3, …, N], so the gap between points 16 and 17 is MR point 17. There is never an MR point 1. Raise ValueError if fewer than 2 values.
- mr_chart_stats(values: list[float]) -> ChartStats — takes the ORIGINAL column values (not the moving ranges). n = N − 1; mr_bar = mean of the moving ranges; mean = mr_bar (the MR chart is centred on the average moving range); sigma = MR_SIGMA_FACTOR * mr_bar; lines = lines_for(mr_bar, sigma). Refer to MR_SIGMA_FACTOR by name — the number 0.7557 must not be typed in section 4, and the shortcut 3.267 must not appear at all. When every value is identical, mr_bar and sigma are exactly 0.0; do not raise.
- lines_below_zero(stats: ChartStats) -> list[int] — the k values, ascending, whose line value is strictly below 0. Used later so the MR chart can compute with these lines but not draw them.

Tests first, appended to tests/test_stats.py. As before, compute expected values independently (by hand or with the literal 0.7557), never from imr's constants:
- individuals_series([1, 4, 2, 2, 9]) has point_numbers [1, 2, 3, 4, 5] and the same values.
- moving_range_series([1, 4, 2, 2, 9]) has values [3, 2, 0, 7] and point_numbers [2, 3, 4, 5]; one value raises ValueError.
- mr_chart_stats([1, 4, 2, 2, 9]): n 4, mean 3.0, mr_bar 3.0, sigma ≈ 2.2671, lines[3] ≈ 9.8013, lines[1] ≈ 5.2671, lines[-1] ≈ 0.7329, lines[-2] ≈ -1.5342, lines[-3] ≈ -3.8013 (pytest.approx, abs=1e-4).
- For a 10-value series with decimals and negatives: mr_chart_stats(x).mr_bar == i_chart_stats(x).mr_bar; the +3 line is within 0.0002 × mr_bar of 3.267 × mr_bar (the textbook upper limit; 1 + 3 × 0.7557 = 3.2671); lines_below_zero returns exactly [-3, -2]; lines[-1] > 0.
- A perfectly straight line (1, 3, 5, 7, 9, 11) is NOT degenerate: every moving range is 2, mr_chart_stats sigma == pytest.approx(0.7557 * 2) and i_chart_stats sigma == pytest.approx(2 / 1.128).
- mr_chart_stats([5, 5, 5]) has mr_bar == 0.0 and sigma == 0.0 exactly.
- lines_below_zero(i_chart_stats([50, 51, 49, 50, 52])) == [].

Rules for this step
- Change only section 4 of imr.py and tests/test_stats.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 3: MR series and MR-chart statistics"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 4 — Zone predicates and difference signs

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: sections 1–2 (constants including ON_LINE_TOLERANCE = 1e-9; dataclasses), section 4 statistics (mean_of, moving_ranges, lines_for(centre, sigma) -> {k: centre + k*sigma for k in -3..3}, i_chart_stats, mr_chart_stats, fmt, individuals_series, moving_range_series, lines_below_zero), tests/test_stats.py and tests/test_guardrails.py.

This step starts SECTION 5: RULE ENGINE with the zone predicates of SPEC.md §5.1. They are the ONLY way any Nelson rule may compare a value with a line or with its neighbour — every rule written later must call them, never compare with > or < directly. They decide the most error-prone behaviour in the tool: comparisons are strict, and a value exactly on a line (within tolerance) belongs to neither side, so it breaks runs.

Each predicate takes one value and a lines dict of the shape lines_for returns ({-3: …, …, 0: mean, …, 3: …}):
- on_line(v, line_value) -> bool: abs(v - line_value) <= ON_LINE_TOLERANCE * max(1, abs(line_value)).
- above_mean(v, lines): v > lines[0] and not on_line(v, lines[0]). below_mean(v, lines): v < lines[0] and not on_line(v, lines[0]).
- beyond_above(v, lines, k) for k in 1, 2, 3: v > lines[k] and not on_line(v, lines[k]). beyond_below(v, lines, k): v < lines[-k] and not on_line(v, lines[-k]). Note: k is always positive; beyond_below looks at the line -k.
- within_1(v, lines): lines[-1] < v < lines[1], and v is on neither the -1 line nor the +1 line.
- outside_1(v, lines): beyond_above(v, lines, 1) or beyond_below(v, lines, 1).
- diff_sign(a, b) -> str: "0" when abs(a - b) <= ON_LINE_TOLERANCE * max(1, abs(a), abs(b)); otherwise "+" when b > a and "-" when b < a. (a is the earlier value, b the later.)
- diff_signs(values) -> list[str]: [diff_sign(values[i], values[i+1]) for each adjacent pair] — n − 1 signs.
Consequences to keep in mind (tests below prove them): a value exactly on the +1 SD line is neither within_1 nor outside_1; a value exactly on the mean is neither above nor below it; equal neighbours give "0".

Tests first, in tests/test_rules.py (create it), using L = lines_for(0.0, 1.0) so lines sit at -3..3:
- 1.0 is neither within_1 nor outside_1; -1.0 likewise.
- 1.0 + 1e-12 counts as on the +1 line (on_line true, outside_1 false, within_1 false).
- 1.0 + 1e-6 is outside_1 and beyond_above(…, 1); -1.0 - 1e-6 is outside_1 and beyond_below(…, 1).
- 0.0 is neither above_mean nor below_mean; 0.5 is above_mean and within_1; -0.5 is below_mean and within_1.
- 3.0 is not beyond_above(…, 3); 3.0001 is; -3.0001 is beyond_below(…, 3); 2.5 is beyond_above(…, 2) but not (…, 3).
- Tolerance scales with the line: with lines_for(1000.0, 10.0) the +3 line is 1030; 1030 + 5e-7 is on it (tolerance 1.03e-6) and 1030 + 5e-6 is beyond_above(…, 3).
- diff_sign(2, 2) == "0"; diff_sign(2, 2 + 1e-12) == "0"; diff_sign(1, 2) == "+"; diff_sign(2, 1) == "-"; diff_signs([1, 2, 2, 1]) == ["+", "0", "-"]; diff_signs([5]) == [].

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 4: zone predicates and difference signs"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 5 — Rule 1 and observation formatting

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: section 1 constants (including RULE_NAMES, a dict 1..8 → rule name), section 2 dataclasses including Series(point_numbers, values) and Observation(field, chart, rule_no, rule_name, direction, points, values, span, line_or_window, description), section 4 statistics (lines_for, fmt(x) → 3-decimal string with ASCII hyphen-minus), section 5 zone predicates (on_line, above_mean, below_mean, beyond_above(v, lines, k), beyond_below(v, lines, k), within_1, outside_1, diff_sign, diff_signs), and tests in tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step adds the shared formatting helpers every rule uses and the first rule, Rule 1 (SPEC.md §5.5), in SECTION 5: RULE ENGINE.

Two conventions for every rule function in this tool:
- A rule function reports POINT NUMBERS taken from series.point_numbers, never list positions. On the MR chart the first point is 2, not 1, and the same engine serves both charts.
- Every text is built with fmt() for numbers. Negative signs and the line names "-1 SD", "-2 SD", "-3 SD" use the plain ASCII hyphen-minus everywhere. The em dash after the rule number ("Rule 1 — …", U+2014) and the en dash in point spans ("1–12", U+2013) in descriptions are kept exactly as SPEC.md writes them. The CSV-style line_or_window field uses a plain hyphen in spans ("window 7-9").

Formatting helpers, in section 5:
- line_name(k) -> "Mean" for 0; otherwise the signed label: "+1 SD", "+2 SD", "+3 SD", "-1 SD", "-2 SD", "-3 SD".
- fmt_pairs(points, values) -> "14=3.100, 15=2.900" (point=value pairs joined by comma-space).
- fmt_points(points) -> "1, 3, 4".
- fmt_values(values) -> "2.500, 2.500".
- fmt_span(a, b) -> "a–b" with an en dash.

Rule 1 — rule_1(series, lines, field="", chart="") -> list[Observation]:
For each position, in order: if beyond_above(v, lines, 3) produce one observation with direction "above"; if beyond_below(v, lines, 3) produce one with direction "below". Consecutive out-of-limit points are separate observations (Rule 1 is not a run rule). Fields: field and chart as passed in; rule_no 1; rule_name RULE_NAMES[1]; points [p]; values [v]; span (p, p); line_or_window "+3 SD=" + fmt(lines[3]) (or "-3 SD=" + fmt(lines[-3])); description exactly:
Rule 1 — One point beyond 3 SD: point {p} (value {fmt(v)}) is {above|below} the {+3 SD|-3 SD} line ({fmt(line)}).
Example with lines_for(0, 1) and value 3.5 at point 3: "Rule 1 — One point beyond 3 SD: point 3 (value 3.500) is above the +3 SD line (3.000)."

Tests first, appended to tests/test_rules.py (use L = lines_for(0.0, 1.0) and Series built directly):
- line_name for all seven k; fmt_pairs([14, 15], [3.1, 2.9]) == "14=3.100, 15=2.900"; fmt_points; fmt_values; fmt_span(1, 12) == "1–12" (en dash).
- E1 from SPEC.md §5.9: values [0, 0, 3.5], point numbers [1, 2, 3] → exactly one observation, point 3, direction "above", span (3, 3), line_or_window "+3 SD=3.000", and the exact description above.
- Below side: [-3.5] → direction "below", line_or_window "-3 SD=-3.000", description ends "is below the -3 SD line (-3.000)."
- A value exactly 3.0 → no observation; 3.0 + 1e-6 → one.
- [3.5, 3.5, 0, -3.5] → three observations in point order (two above, one below).
- MR numbering: Series(point_numbers=[2, 3, 4], values=[0, 0, 3.5]) reports point 4, not 3.
- field="IMR_Field_X", chart="MR" are copied onto every observation; omitted, they default to "".

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 5: rule 1 and observation formatting"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 6 — Maximal runs and Rule 2

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (including RULE_2_MIN_RUN = 9 and RULE_NAMES), dataclasses (Series, Observation), statistics (lines_for, fmt), and in section 5 the zone predicates (above_mean, below_mean, … , diff_signs), the formatting helpers (line_name, fmt_pairs, fmt_points, fmt_values, fmt_span with an en dash) and rule_1(series, lines, field="", chart=""). Rule functions report point numbers from series.point_numbers, never positions. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step adds the maximal-run helper that four more rules will reuse, and Rule 2, in SECTION 5: RULE ENGINE.

maximal_runs(labels: list) -> list[tuple[object, int, int]]:
Returns every maximal run of equal, adjacent labels as (label, start_position, end_position), end inclusive, in order. A None label never forms a run and always separates runs. "Maximal" means the run cannot be extended in either direction. Example: ["A", "A", None, "B", "B", "B", "A"] → [("A", 0, 1), ("B", 3, 5), ("A", 6, 6)]. [] → [].

Rule 2 — rule_2(series, lines, field="", chart="") -> list[Observation] (SPEC.md §5.3, §5.5):
Label each position "A" if above_mean, "B" if below_mean, otherwise None (a value on the mean breaks the run). Every maximal run of length ≥ RULE_2_MIN_RUN becomes EXACTLY ONE observation covering every point of the run — a 12-point run is one entry listing 12 points, never four overlapping entries and never only the last nine. Fields: rule_no 2; rule_name RULE_NAMES[2]; direction "above" or "below"; points and values of the whole run; span (first point, last point); line_or_window "mean=" + fmt(lines[0]); description exactly:
Rule 2 — Nine or more points on one side of the mean: {len} consecutive points {above|below} the mean ({fmt(lines[0])}), points {a}–{b}. Values: {fmt_pairs}.
(the span uses fmt_span, i.e. an en dash).

Tests first, appended to tests/test_rules.py (L = lines_for(0.0, 1.0)):
- maximal_runs on the example above, on [], on [None, None], and on ["A"] * 4.
- Exactly nine 0.5s → one observation, points 1–9, direction "above", span (1, 9), line_or_window "mean=0.000"; assert the complete description string for this case.
- Eight 0.5s → nothing.
- E2 from SPEC.md §5.9: twelve 0.5s → exactly one observation covering points 1–12 (not four).
- Nine -0.5s → one observation, direction "below".
- E3: 0.5 × 5, 0, 0.5 × 5 → nothing (the point on the mean splits the run into two runs of 5).
- Two separate qualifying runs (0.5 × 9, then -0.5 × 9) → two observations in point order.
- MR numbering: a Series with point_numbers 2..10 and nine 0.5s reports points 2–10.

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 6: maximal runs and rule 2"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 7 — Rules 7 and 8

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (including RULE_7_MIN_RUN = 15, RULE_8_MIN_RUN = 8, RULE_NAMES), dataclasses, statistics (lines_for, fmt), and in section 5: zone predicates (within_1, outside_1, beyond_above(v, lines, k), beyond_below(v, lines, k), …), formatting helpers (line_name, fmt_pairs, fmt_span with an en dash, …), maximal_runs(labels) -> [(label, start_pos, end_pos)] where None never forms a run, rule_1 and rule_2. Every rule function has the signature rule_k(series, lines, field="", chart="") -> list[Observation], reports point numbers from series.point_numbers, and produces one observation per maximal run that meets its threshold. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step adds Rules 7 and 8 (SPEC.md §5.3, §5.5) to SECTION 5: RULE ENGINE. Both are run rules with the same shape as Rule 2 and must reuse maximal_runs.

Rule 7 — rule_7: label each position True if within_1 else None. Each maximal run of length ≥ RULE_7_MIN_RUN → one observation covering all its points. direction "within"; span (first, last); line_or_window "-1 SD=" + fmt(lines[-1]) + "; +1 SD=" + fmt(lines[1]); description exactly:
Rule 7 — Fifteen or more points within 1 SD of the mean: {len} consecutive points, {a}–{b}, all between the -1 SD line ({fmt(lines[-1])}) and the +1 SD line ({fmt(lines[1])}). Values: {fmt_pairs}.

Rule 8 — rule_8: label each position True if outside_1 else None. Each maximal run of length ≥ RULE_8_MIN_RUN → one observation. direction "either"; count how many points in the run are beyond_above(…, 1) (n_above) and how many beyond_below(…, 1) (n_below); line_or_window as Rule 7; description exactly:
Rule 8 — Eight or more points beyond 1 SD on either side: {len} consecutive points, {a}–{b}, none within 1 SD ({n_above} above, {n_below} below). Values: {fmt_pairs}.

Remember: a value exactly on the ±1 SD line is neither within_1 nor outside_1, so it breaks both kinds of run.

Tests first, appended to tests/test_rules.py (L = lines_for(0.0, 1.0)):
- Rule 7: fifteen values alternating 0.5, -0.5 → one observation, points 1–15, direction "within", line_or_window "-1 SD=-1.000; +1 SD=1.000"; assert the complete description.
- Rule 7: fourteen such values → nothing. Eighteen → exactly one observation covering 1–18.
- Rule 7, E14 from SPEC.md §5.9: 0.5 × 7, 1.0, 0.5 × 7 → nothing (the point exactly on +1 SD splits the run into two 7-point runs).
- Rule 8, E8: 1.5, -1.5 repeated 4 times → one observation, points 1–8, direction "either", "(4 above, 4 below)" in the description; assert the complete description.
- Rule 8: seven such values → nothing; eleven → one covering 1–11 with the correct counts.
- Rule 8, E9: 1, -1 repeated 7 times → nothing (every value is exactly on a ±1 line, so none is outside_1).
- Rule 8 all on one side: 1.5 × 8 → "(8 above, 0 below)".
- MR numbering for one case of each rule (point_numbers starting at 2).

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 7: rules 7 and 8"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 8 — Rules 3 and 4

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (including RULE_3_MIN_RUN = 6, RULE_4_MIN_RUN = 14, RULE_NAMES), dataclasses, statistics, and in section 5: zone predicates including diff_sign(a, b) -> "+", "-" or "0" (equal within tolerance) and diff_signs(values) -> n − 1 signs; formatting helpers (fmt_pairs, fmt_span with an en dash, …); maximal_runs(labels) -> [(label, start_pos, end_pos)] with None never forming a run; rule_1, rule_2, rule_7, rule_8. Every rule function has the signature rule_k(series, lines, field="", chart="") -> list[Observation], reports point numbers from series.point_numbers, and produces one observation per maximal run that meets its threshold. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step adds the two trend rules, Rules 3 and 4 (SPEC.md §5.5), to SECTION 5: RULE ENGINE. They work on the differences between neighbours, not on the lines — the lines argument is accepted for a uniform signature but not used. Both are about POINTS, while they are computed over DIFFERENCES: m consecutive differences span m + 1 points. Getting this off by one is the classic bug here; the tests pin it.

Rule 3 — rule_3: take diff_signs(series.values); map "0" to None; find maximal runs of "+" and of "-" with maximal_runs. A run over difference positions s..e covers point positions s..e+1, i.e. e − s + 2 points. If that is ≥ RULE_3_MIN_RUN → one observation covering all those points; direction "rising" for "+", "falling" for "-". A "0" difference (equal neighbours) ends a run. A peak or valley point can belong to both a rising and a falling observation. line_or_window ""; description exactly:
Rule 3 — Six or more points steadily {rising|falling}: {len} consecutive points, {a}–{b}. Values: {fmt_pairs}.

Rule 4 — rule_4: find maximal segments of the difference list in which every difference is non-zero and every adjacent pair of differences has opposite signs. A single non-zero difference is a segment of one. Two equal signs in a row, or a "0", end a segment. A segment over difference positions s..e covers e − s + 2 points; if ≥ RULE_4_MIN_RUN → one observation, direction "alternating", line_or_window "", description exactly:
Rule 4 — Fourteen or more points alternating up and down: {len} consecutive points, {a}–{b}. Values: {fmt_pairs}.

Tests first, appended to tests/test_rules.py (values given directly; L = lines_for(0.0, 1.0) passed but irrelevant):
- Rule 3: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] → one observation "rising", points 1–6; assert the complete description. Five rising points → nothing. Nine rising points → one observation covering 1–9. Six falling points → "falling".
- Rule 3, E4 from SPEC.md §5.9: 1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1 → exactly two observations: rising 1–7 and falling 7–13, point 7 in both.
- Rule 3, E5: 1, 2, 3, 3, 4, 5, 6, 7 → nothing (the tie splits it into a 3-point and a 5-point run).
- Rule 4, E6: 0.5, -0.5 repeated 7 times (14 points) → one observation 1–14; assert the complete description. Thirteen points → nothing. Seventeen alternating points → one covering 1–17.
- Rule 4, E9: 1, -1 repeated 7 times → one observation 1–14.
- Rule 4: a repeated value in the middle of an otherwise 20-point alternating series (so two neighbours are equal) splits it; construct it so both halves are under 14 → nothing.
- Rule 4: two rises in a row in the middle break the alternation in the same way.
- MR numbering for one case of each rule (point_numbers starting at 2).

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 8: rules 3 and 4"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 9 — Rules 5 and 6

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (including RULE_5_WINDOW = 3, RULE_5_MIN_COUNT = 2, RULE_6_WINDOW = 5, RULE_6_MIN_COUNT = 4, RULE_NAMES), dataclasses (Series, Observation), statistics (lines_for, fmt), and in section 5: zone predicates (beyond_above(v, lines, k), beyond_below(v, lines, k), …), formatting helpers (line_name → "+2 SD"/"-2 SD" with ASCII hyphen-minus, fmt_points → "1, 3, 4", fmt_values → "2.500, 2.500", fmt_span → "a–b" with an en dash), maximal_runs, and rule_1, rule_2, rule_3, rule_4, rule_7, rule_8, each rule_k(series, lines, field="", chart="") -> list[Observation] reporting point numbers from series.point_numbers. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step adds the two window rules, Rules 5 and 6, via one shared helper, in SECTION 5: RULE ENGINE. This is the only merging algorithm in the tool (SPEC.md §5.4); read that section before starting.

window_observations(series, lines, k, width, min_count, rule_no, field="", chart="") -> list[Observation], applied to the "above" side and then, independently, to the "below" side (points on opposite sides never count together):
1. flag each position: beyond_above(v, lines, k) for the above side, beyond_below(v, lines, k) for the below side.
2. slide a window of `width` consecutive positions s..s+width−1 over the series (no windows if the series is shorter than width). A window qualifies when it holds ≥ min_count flagged positions (so 3 of 3 and 5 of 5 qualify too).
3. merge qualifying windows of the same side that share at least one position into one span [first, last]. Windows that are adjacent but share no position stay separate.
4. one observation per merged span: points and values are ONLY the flagged positions inside the span (unflagged points inside it are neither listed nor marked); span = (point number at the span's first position, point number at its last position) — the span may extend past the last flagged point; direction "above"/"below"; rule_name RULE_NAMES[rule_no]; line_or_window = line_name(±k) + "=" + fmt(line) + "; window " + f"{a}-{b}" (plain hyphen, e.g. "+2 SD=2.000; window 1-5").
Return the observations sorted by their first listed point.

rule_5(series, lines, field="", chart="") = window_observations with k=2, width=RULE_5_WINDOW, min_count=RULE_5_MIN_COUNT, rule_no=5; description exactly:
Rule 5 — Two of three points beyond 2 SD: points {fmt_points} (values {fmt_values}) are {above|below} the {+2 SD|-2 SD} line ({fmt(line)}); window {a}–{b}.
rule_6: k=1, width=RULE_6_WINDOW, min_count=RULE_6_MIN_COUNT, rule_no=6; description exactly:
Rule 6 — Four of five points beyond 1 SD: points {fmt_points} (values {fmt_values}) are {above|below} the {+1 SD|-1 SD} line ({fmt(line)}); window {a}–{b}.
(Note the descriptions use the shorter names without "(same side)" exactly as SPEC.md §5.5 writes them, while rule_name uses RULE_NAMES.)

Tests first, appended to tests/test_rules.py (L = lines_for(0.0, 1.0)):
- E10 from SPEC.md §5.9: [2.5, 0, 2.5] → one Rule 5 observation, points [1, 3], span (1, 3), line_or_window "+2 SD=2.000; window 1-3"; assert the complete description: "Rule 5 — Two of three points beyond 2 SD: points 1, 3 (values 2.500, 2.500) are above the +2 SD line (2.000); window 1–3."
- E11: [2.5, 0, 2.5, 2.5, 0, 0] → exactly one observation, points [1, 3, 4], span (1, 5) (windows 1–3, 2–4, 3–5 qualify and overlap; 4–6 does not); point 5 is inside the span but not listed.
- Adjacent, non-overlapping: [2.5, 2.5, 0, 0, 2.5, 2.5] → two observations: points [1, 2] span (1, 3), and points [5, 6] span (4, 6).
- Threshold minus one: [2.5, 0, 0, 2.5] → nothing. 3 of 3: [2.5, 2.5, 2.5] → one observation, points [1, 2, 3].
- Below side: [-2.5, 0, -2.5] → direction "below", line_or_window "-2 SD=-2.000; window 1-3".
- Same side only: [2.5, -2.5, 0] → nothing.
- A value exactly 2.0 is not flagged: [2.0, 0, 2.5] → nothing.
- E12: [1.5, 1.5, 0, 1.5, 1.5] → one Rule 6 observation, points [1, 2, 4, 5], span (1, 5); assert the complete description.
- Rule 6: [1.5, 1.5, 0, 1.5, 0] (3 of 5) → nothing; [1.5] * 5 → one observation (5 of 5); a 4-point series → nothing.
- MR numbering: Series(point_numbers=[2, 3, 4], values=[2.5, 0, 2.5]) → points [2, 4], span (2, 4), "window 2-4".

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 9: rules 5 and 6"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 10 — `detect_all`, `pattern_points`, and the fourteen worked examples

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants, dataclasses (Series, Observation), statistics (lines_for, moving_range_series, fmt), and in section 5 all eight rule functions rule_1 … rule_8, each rule_k(series, lines, field="", chart="") -> list[Observation], reporting point numbers from series.point_numbers, plus the predicates and formatting helpers they use. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step closes the rule engine with the single entry point the rest of the tool will call, and proves the whole engine against SPEC.md §5.9's fourteen worked examples with their COMPLETE expected output.

In SECTION 5: RULE ENGINE:
- detect_all(series, lines, field="", chart="") -> list[Observation]: run rule_1 … rule_8 with field and chart passed through, concatenate, and return sorted by (rule_no, first listed point); keep the order stable for ties. This is the order used everywhere the observations appear (SPEC.md §5.8).
- pattern_points(observations) -> set[int]: the union of every observation's points. A point caught by several rules is drawn once but listed under every rule that caught it (§5.7).

Tests first, appended to tests/test_rules.py. Use L = lines_for(0.0, 1.0) and Series with point numbers 1..n. For each example assert the COMPLETE list of observations as (rule_no, direction, points, span) tuples in detect_all order — no more, no fewer.

IMPORTANT: several of these sets are larger than you might expect, because with mean 0 and SD 1 supplied, values such as 4, 5, 6, 7 are several SDs above the mean and also satisfy the zone rules. SPEC.md v1.1 §5.9 lists the same complete sets (v1.0 listed only the rule being illustrated; E5 in v1.0 wrongly said Rule 2 fires — it has only 8 points). The sets below were worked by hand and cross-checked with an independent reference implementation. If your engine disagrees with any line below, do NOT change the test to match the engine: recompute that example by hand, and report the disagreement and your reasoning in your summary.

E1  [0, 0, 3.5] → (1, above, [3], (3,3)).
E2  twelve 0.5s → (2, above, [1..12], (1,12)).
E3  0.5×5, 0, 0.5×5 → nothing.
E4  [1,2,3,4,5,6,7,6,5,4,3,2,1] → thirteen observations: Rule 1 above at each of points 4, 5, 6, 7, 8, 9, 10 (seven separate observations, span (p,p)); (2, above, [1..13], (1,13)); (3, rising, [1..7], (1,7)); (3, falling, [7..13], (7,13)); (5, above, [3..11], (2,12)); (6, above, [2..12], (1,13)); (8, either, [2..12], (2,12)) with 11 above and 0 below.
E5  [1,2,3,3,4,5,6,7] → six observations: Rule 1 above at points 5, 6, 7, 8; (5, above, [3..8], (2,8)); (6, above, [2..8], (1,8)). No Rule 2, no Rule 3, no Rule 8.
E6  0.5, -0.5 repeated 7 times → (4, alternating, [1..14], (1,14)) only.
E7  E6 plus one more 0.5 → (4, alternating, [1..15], (1,15)); (7, within, [1..15], (1,15)).
E8  1.5, -1.5 repeated 4 times → (8, either, [1..8], (1,8)) with 4 above and 4 below, only.
E9  1, -1 repeated 7 times → (4, alternating, [1..14], (1,14)) only.
E10 [2.5, 0, 2.5] → (5, above, [1,3], (1,3)).
E11 [2.5, 0, 2.5, 2.5, 0, 0] → (5, above, [1,3,4], (1,5)).
E12 [1.5, 1.5, 0, 1.5, 1.5] → (6, above, [1,2,4,5], (1,5)).
E13 0.5, -0.5 repeated 8 times → (4, alternating, [1..16], (1,16)); (7, within, [1..16], (1,16)).
E14 0.5×7, 1.0, 0.5×7 → (2, above, [1..15], (1,15)) only. Rule 7 does not fire (the point on +1 SD splits it).

Additional tests:
- pattern_points on E7's observations == set(range(1, 16)); point 3 appears in both the Rule 4 and the Rule 7 observation but once in the set.
- detect_all stamps field and chart on every observation.
- MR numbering end to end: take x = [0, 3, 0, 3, 0, 3, 0, 3, 0, 3], build moving_range_series(x) (point numbers 2..10) and run detect_all with lines_for(0.0, 1.0); every reported point lies in 2..10 and the Rule 2 observation covers points 2–10 (all nine moving ranges are 3.0, i.e. above the mean).
- Ordering: on E4, the rule numbers in detect_all's output are non-decreasing and, within Rule 1, the points increase.

Rules for this step
- Change only section 5 of imr.py and tests/test_rules.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 10: detect_all and the fourteen worked examples"
- Then write a short plain-English summary: what you built, how many tests now pass, whether any worked example disagreed with your engine (and your hand reasoning if so), and any decision you had to make that these instructions did not cover.
```

### Step 11 — File-level parsing and validation (V02–V07)

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: section 1 constants (including IMR_PREFIX = "IMR_Field", MAX_UPLOAD_BYTES = 10 MB, MAX_BAD_CELLS_LISTED = 20), section 2 dataclasses (including ValidationIssue(code, severity, message) and ValidationErrors(Exception) carrying .issues), the statistics in section 4 and the complete rule engine in section 5. Section 3 is still empty. Tests: tests/test_stats.py, tests/test_rules.py, tests/test_guardrails.py.

This step implements the file-level half of SPEC.md §3 and §7.1 in SECTION 3: PARSING AND VALIDATION: turning uploaded bytes into a header and rows, with every file-level problem reported in plain language. Cell values come in the next step. V01 (no file in the request) is checked later by the web route, not here. Section 3 must never import Flask.

Implement, in section 3:
- sanitise_name(text) -> str: replace every character outside A–Z a–z 0–9 _ - with "_" (SPEC.md §6.6).
- stem_of(filename) -> str: the filename without its directory and without its final extension, then sanitised. "Q3 data.csv" → "Q3_data".
- read_table(data: bytes, filename: str) -> tuple[list[str], list[list[str]], list[ValidationIssue]]: returns (header, data_rows, issues). It RAISES ValidationErrors only for V02–V04, which stop everything; V05–V07 are RETURNED in the issues list, together with the rows, so that parse_csv (next step) can still check cells and count rows and report every problem in one go. Checks, in this order:
  V02 (severity "F") — the extension is not .csv, case-insensitive (".CSV" is fine). Stop. Message: "{filename} is not a .csv file. Only comma-separated .csv files are accepted."
  V03 — len(data) > MAX_UPLOAD_BYTES. Stop. "{filename} is larger than 10 MB. This tool is built for files of a few hundred rows."
  V04 — remove one leading UTF-8 byte-order mark if present, then decode as UTF-8; failure stops. "{filename} could not be read as UTF-8 text. Re-save it from Excel as \"CSV UTF-8\" and try again."
  Then parse with the csv module (comma delimiter, io.StringIO(text, newline="")). Row 1 is the header. Strip leading/trailing whitespace from each header cell. Drop completely blank lines at the very END of the file (after the last non-blank row); a completely blank line BETWEEN rows is kept and counts as a row with 0 cells.
  From here, collect every problem found into the issues list — do NOT raise (the owner fixes the file once, not one problem per upload; parse_csv raises them all together):
  V05 — there is no header row, or no header starts with IMR_PREFIX (exact, case-sensitive; "IMR_Field", "IMR_FieldA" and "IMR_Field_Sales" match; "imr_field_x" and "Sales_IMR_Field" do not). "No column starting with IMR_Field was found. Columns present: {comma-separated headers, or (none)}. Rename the columns to chart so they start with IMR_Field."
  V06 — two or more IMR_Field headers are identical; one issue per duplicated name. "Column name {name} appears more than once. Make every IMR_Field column name unique."
  V07 — a data row's cell count differs from the header's. {r} is the spreadsheet row number (header = row 1, first data row = row 2). "Row {r} has {k} cells but the header has {h}. Fix the row (a stray comma or a missing value is the usual cause)." List at most MAX_BAD_CELLS_LISTED such rows, then one further issue "… and {m} more rows with the wrong number of cells." (an ellipsis character).
  Always return the stripped header (an empty list when there is no header row), the data rows (cell text untouched — trimming cell values happens in the next step) and the issues list (empty when nothing is wrong).
- Every message says what happened, where, and what to do; never a Python exception name or traceback (SPEC.md §7.2).

Tests first, in tests/test_parsing.py (create it). Build CSV bytes inline in each test:
- A well-formed file with a BOM returns the header without the BOM character, the right rows and an empty issues list.
- V02 for "data.txt" is raised as ValidationErrors; "DATA.CSV" is accepted.
- V03 for MAX_UPLOAD_BYTES + 1 bytes is raised (the message names the file).
- V04 for bytes b"IMR_Field_A\n\xff\xfe\n" is raised (the message contains "CSV UTF-8").
- V05 is returned in the issues list when no header matches, with the present column names listed in the message; V05 for empty bytes; "imr_field_x" alone triggers V05 (the prefix is case-sensitive); " IMR_Field_A " (padded) is accepted as IMR_Field_A.
- V06 for two columns both named IMR_Field_A; a duplicated non-IMR column name is fine.
- V07 names row 3 when the second data row has one cell too many; a blank line between rows 2 and 4 triggers V07 for row 3 with "has 0 cells"; blank lines at the end of the file are ignored.
- V07 with 25 ragged rows: exactly 20 row issues plus one "… and 5 more" issue.
- V05, V06 and V07 found in one file are all returned together in one issues list (assert the set of codes), nothing is raised, and the rows are still returned; every issue has severity "F".
- sanitise_name("Sales (EU) %") == "Sales__EU___"; stem_of("C:\\data\\Q3 data.csv") == "Q3_data".

Rules for this step
- Change only section 3 of imr.py and tests/test_parsing.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 11: file-level parsing and validation"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 12 — Cell values and `parse_csv` (V08, V09)

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (IMR_PREFIX, MIN_DATA_ROWS = 3, MAX_BAD_CELLS_LISTED = 20, …), dataclasses (ValidationIssue, ValidationErrors, ParsedColumn(name, index, values), ParsedFile(source_filename, stem, n_rows, columns)), statistics, the full rule engine, and in section 3: sanitise_name, stem_of, and read_table(data, filename) which returns (header, data_rows, issues) — issues being a list of V05–V07 ValidationIssue — and raises ValidationErrors only for V02–V04. Tests: tests/test_parsing.py plus the stats, rules and guardrail tests.

This step finishes SECTION 3: PARSING AND VALIDATION with the cell rules of SPEC.md §3.3 and the single parsing entry point the rest of the tool will call.

Implement, in section 3:
- NUMBER_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
- parse_number(text) -> float | None: strip leading/trailing whitespace; if the result matches NUMBER_RE return float(result), otherwise None. This deliberately rejects empty cells, thousands separators ("1,234"), currency and percent symbols, text, and "nan", "inf", "infinity" in any casing — Python's float() would accept those last three; the regex keeps them out. Negative numbers and zero are fine.
- parse_csv(data: bytes, filename: str) -> ParsedFile — the one function the rest of the tool calls. It calls read_table. If read_table raises (V02, V03 or V04), let that propagate unchanged. Otherwise start from read_table's returned issues (V05–V07), add the checks below, and if the combined list is not empty raise all of them together in one ValidationErrors:
  V08 (severity "F") — a cell in an IMR_Field column is blank or not a number per parse_number. Check only rows whose cell count matches the header (ragged rows are already V07). Order: by column in file order, then by row. One issue per bad cell: 'Column {name}, row {r} (point {p}) contains "{text}", which is not a number. Every cell in an IMR_Field column must be a plain number.' where {r} is the spreadsheet row (first data row = 2) and {p} = r − 1 is the point number. List at most MAX_BAD_CELLS_LISTED, then one issue "… and {m} more cells that are not numbers."
  V09 — fewer than MIN_DATA_ROWS data rows: "Only {n} data rows found; at least {MIN_DATA_ROWS} are needed. Add more rows — 20 or more gives reliable limits." — build the number from the MIN_DATA_ROWS constant, never type it, so changing the minimum is a one-constant edit.
  If there are no issues, return ParsedFile(source_filename=filename, stem=stem_of(filename), n_rows=number of data rows, columns=[ParsedColumn(name, index, values) for each IMR_Field column in file order]), where index is the 0-based position among the charted columns (0, 1, 2 …), not the position in the file. Non-IMR columns are ignored completely, whatever they contain.
Because blanks are rejected, every charted column has exactly n_rows values.

Tests first, appended to tests/test_parsing.py:
- parse_number: "12.5" and "  12.5  " → 12.5; "-3.2e2" → -320.0; ".5" → 0.5; "5." → 5.0; "+7" → 7.0; "0" → 0.0; each of "", "  ", "1,234", "$5", "5%", "abc", "nan", "NaN", "inf", "-Infinity", "1e", "--1" → None.
- parse_csv on a good file with columns Notes, IMR_Field_B, Other, IMR_Field_A returns two columns named IMR_Field_B (index 0) and IMR_Field_A (index 1) in that order, with float values, and n_rows correct; stem computed from the filename.
- A Notes column full of text, blanks and commas inside quotes does not cause any issue.
- V08 for a blank cell names the column, "row 3" and "(point 2)", and quotes the text; "nan" and "1,234" are each rejected with V08.
- Several bad cells across two columns are all reported, column by column.
- 25 bad cells → 20 cell issues plus one "… and 5 more" issue.
- V09 with 2 data rows; exactly 3 data rows is accepted.
- V05 and V09 together (no IMR column and only 1 data row) are reported together.
- V02 still propagates from parse_csv unchanged (severity "F", code "V02").

Rules for this step
- Change only section 3 of imr.py and tests/test_parsing.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 12: cell values and parse_csv"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 13 — Chart rendering

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: matplotlib imported at the top of imr.py with the Agg (non-GUI) backend set before pyplot; section 1 constants (FIG_MIN_WIDTH_IN = 10.0, FIG_WIDTH_PER_POINT_IN = 0.2, FIG_HEIGHT_IN = 4.5, FIG_DPI = 100, TICK_EVERY_POINT_UP_TO = 50, LINE_KS); dataclasses (Series, ChartStats(n, mean, mr_bar, sigma, lines)); section 4 statistics (i_chart_stats(values), mr_chart_stats(values), individuals_series, moving_range_series, lines_below_zero(stats) -> k values whose line is below 0); the full rule engine in section 5 (detect_all, pattern_points, line_name(k) -> "Mean", "+1 SD" … "-3 SD"); parsing in section 3. Tests: test_stats, test_rules, test_parsing, test_guardrails.

This step implements SECTION 6: RENDERING — one static PNG per chart, per SPEC.md §6.2 and §10. Section 6 must never import Flask.

Implement, in section 6:
- figure_width_inches(n_points_on_i_chart) -> float: max(FIG_MIN_WIDTH_IN, FIG_WIDTH_PER_POINT_IN * n).
- render_chart(series, stats, pattern_pts: set[int], title: str, y_label: str, n_total: int, hide_ks: list[int] | None = None) -> bytes, returning PNG bytes. n_total is the number of points on the I chart (N) and is used for BOTH charts so they align when stacked. hide_ks lists line k values not to draw (the MR chart passes lines_below_zero(stats); the I chart passes nothing and draws all seven lines even if some are negative).
  - fig, ax = plt.subplots(figsize=(figure_width_inches(n_total), FIG_HEIGHT_IN), dpi=FIG_DPI); always plt.close(fig) afterwards, even on error (try/finally), so memory does not grow across uploads.
  - Horizontal lines across the full x-range: the mean in black dotted; ±1 SD and ±2 SD in red dotted; ±3 SD in red solid; all at z-order 1. Each drawn line gets a small label (fontsize 7) at its right-hand end, x = n_total + 0.5, ha="left", va="center", clip_on=False, text line_name(k) ("Mean", "+1 SD", … "-3 SD", ASCII hyphen-minus). Widen the right margin (fig.subplots_adjust) so the labels are visible.
  - A thin solid black connecting line through all points in order (z-order 2).
  - Points NOT in pattern_pts: black filled circles, marker "o", markersize 6 (z-order 3). Points in pattern_pts: red filled triangles, marker "^", markersize 8, drawn instead of the circle (z-order 4).
  - Every point carries its point number as a label: ax.annotate(str(p), (p, v), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=7, zorder=5).
  - x-axis from 0.5 to n_total + 0.5; ticks at every point number when n_total <= TICK_EVERY_POINT_UP_TO, otherwise at 1, 5, 10, 15, … up to n_total. x label "Point number"; y label as given.
  - y-axis: automatic with a margin, always including every drawn line and every point; when hide_ks is not empty (the MR chart) the lower bound is exactly 0.
  - A small legend: a black circle labelled "Data point" and a red triangle labelled "Nelson pattern point" (use proxy Line2D handles so the legend is the same whether or not any pattern exists).
  - Title as given. (The caller will pass "{column} — Individuals (I) chart" and "{column} — Moving Range (MR) chart", with an em dash.)
  - Save with fig.savefig(buf, format="png", bbox_inches="tight", metadata={"Software": None}) into io.BytesIO and return the bytes. No randomness anywhere: the same inputs must give identical bytes.

Tests first, in tests/test_render.py (create it). Build inputs with individuals_series / moving_range_series / i_chart_stats / mr_chart_stats / detect_all from a fixed list such as 30 hand-typed values:
- The I chart and the MR chart each return bytes starting with the PNG signature b"\x89PNG\r\n\x1a\n" and larger than 5 000 bytes.
- figure_width_inches(10) == 10.0, (50) == 10.0, (100) == 20.0, (150) == 30.0.
- The PNG pixel width (read from the IHDR chunk: bytes 16–20, big-endian) for N = 100 is greater than for N = 30 (exact pixel width is not asserted because bbox_inches="tight" trims whitespace).
- No exception when every point is a pattern point, when none is, and for N = 3.
- The MR chart renders without error with hide_ks = lines_below_zero(mr stats) (normally [-3, -2]), and also when hide_ks contains -3, -2 and -1.
- Determinism: rendering the same inputs twice gives identical bytes.
- Memory hygiene: after rendering, plt.get_fignums() is empty.

Rules for this step
- Change only section 6 of imr.py and tests/test_render.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import (matplotlib may use numpy internally; imr.py must not import it); no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Save one sample I chart and one MR chart to the system temp folder, open them yourself, and describe them in your summary (colours, line styles, labels, number labels, triangles) so the owner can compare with SPEC.md §6.2. Do not add those images to the repository.
- Commit: git add -A && git commit -m "Step 13: chart rendering"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 14 — Observations CSV builder

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants, dataclasses (Observation(field, chart, rule_no, rule_name, direction, points, values, span, line_or_window, description); ChartStats; ChartResult(kind, point_numbers, values, stats, observations, pattern_points, png); ColumnResult(name, index, n, warning, rejected_reason, individuals, moving_range)), parsing (section 3), statistics with fmt (section 4), the full rule engine with detect_all (section 5), and render_chart (section 6). Every Observation's line_or_window and description strings are already fully formatted by the rule engine. Section 7 is empty. Tests: test_stats, test_rules, test_parsing, test_render, test_guardrails.

This step starts SECTION 7: REPORT AND CSV BUILDERS with the observations CSV (SPEC.md §6.7). It is the build's acceptance artefact: later, the whole tool is judged by comparing this CSV against a hand-verified answer key row for row. Section 7 must never import Flask.

Implement, in section 7:
- points_field(points) -> str: one point → "17"; two or more points that are consecutive integers (each one more than the last) → "a-b" with a plain hyphen, e.g. "14-25"; anything else → comma-separated without spaces, e.g. "7,9".
- build_observations_csv(columns: list[ColumnResult]) -> str: written with the csv module (default RFC 4180 quoting, lineterminator="\n") into io.StringIO. Header row exactly: field,chart,rule_no,rule_name,direction,points,values,line_or_window,description. Then, for each column in the given (file) order that is not rejected (rejected_reason is None), the individuals chart's observations followed by the moving-range chart's observations, each in the order already stored. Per observation: field; chart ("I" or "MR"); rule_no; rule_name; direction; points_field(points); values as fmt(v) joined by ";" in point order, e.g. "41.100;40.800"; line_or_window; description. Rejected columns contribute no rows. Warnings never appear in this CSV. With no observations at all, the result is the header row only.

Tests first, in tests/test_builders.py (create it). Build the ColumnResult / ChartResult / Observation objects by hand (png can be b"", stats any ChartStats):
- points_field([17]) == "17"; ([14, 15, 16]) == "14-16"; ([7, 9]) == "7,9"; ([1, 3, 4]) == "1,3,4"; ([3, 4]) == "3-4".
- Header row exactly as above.
- Two columns, each with I and MR observations: rows appear column by column, I before MR, in stored order.
- Values joined with ";" at 3 decimals, negatives with an ASCII hyphen.
- A description containing commas and an em dash round-trips intact when read back with csv.reader (quoting works, UTF-8 characters survive).
- A rejected column contributes no rows.
- With no observations anywhere: header only.
- Real observations from detect_all on SPEC.md §5.9 example E11 ([2.5, 0, 2.5, 2.5, 0, 0], lines_for(0.0, 1.0), field "IMR_Field_T", chart "I") produce the row: IMR_Field_T, I, 5, Two of three points beyond 2 SD (same side), above, 1,3,4, 2.500;2.500;2.500, +2 SD=2.000; window 1-5, and the Rule 5 description.

Rules for this step
- Change only section 7 of imr.py and tests/test_builders.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 14: observations CSV builder"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 15 — Column-section HTML and the standalone report

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: constants (WARN_BELOW_POINTS = 20, LINE_KS, …), dataclasses (ChartStats, ChartResult(kind, point_numbers, values, stats, observations, pattern_points, png), ColumnResult(name, index, n, warning, rejected_reason, individuals, moving_range), AnalysisResult), parsing, statistics (fmt, lines_below_zero), rule engine, render_chart, and in section 7 points_field and build_observations_csv. Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_guardrails.

This step adds the HTML builders to SECTION 7: REPORT AND CSV BUILDERS: one column's section (used both by the results page later and by the downloadable report) and the complete standalone report (SPEC.md §6.1, §6.3–6.6, §7.3). Build HTML with plain Python strings; pass every piece of user-supplied text (column names, file names, messages, descriptions) through html.escape. No JavaScript. Section 7 must never import Flask.

Implement, in section 7:
- warning_text(n) -> "Only {n} points. Control limits based on fewer than 20 points are unreliable; treat every pattern below as indicative."
- build_summary_table_html(chart: ChartResult) -> str: a <table> with rows, in order: Points (stats.n); Mean (stats.mean — the centre line); Average moving range (MR-bar) (stats.mr_bar); a sigma row (stats.sigma) labelled f"Sigma (MR-bar / {D2_CONSTANT})" on the I chart and f"Sigma ({MR_SIGMA_FACTOR} x MR-bar)" on the MR chart — built from the named constants, never typed as numbers, so they render as "Sigma (MR-bar / 1.128)" and "Sigma (0.7557 x MR-bar)"; +3 SD; +2 SD; +1 SD; -1 SD; -2 SD; -3 SD; Patterns detected (number of observations). Every number through fmt except the two counts. On the MR chart the Mean and MR-bar rows show the same number by design. For the MR chart only (chart.kind == "MR"), each of the -1/-2/-3 SD rows whose line is below zero shows the value followed by " (below 0, not drawn)". Row labels use the ASCII hyphen-minus.
- build_observations_html(chart: ChartResult) -> str: heading "Nelson patterns detected (I chart)" or "Nelson patterns detected (MR chart)", then one list item per observation containing its description verbatim (escaped); when there are none, the single line "No Nelson patterns detected."
- build_column_section_html(column: ColumnResult, include_downloads: bool = False) -> str: a <section> with, in order: an <h2> heading with the column name; if the column is rejected, a red box (class "rejected") containing rejected_reason and NOTHING else; otherwise, if column.warning is set, a warning box (class "warning") with the warning text; then the I chart as <img src="data:image/png;base64,…" alt="{column} I chart">; when include_downloads is True, a link "Download PNG" to /download/png/{column.index}/I directly under the image; the I summary table; the I observations; then the MR chart image (link /download/png/{column.index}/MR when include_downloads), MR summary table, MR observations. Images wider than the viewport sit inside a horizontally scrolling container (a div with overflow-x: auto).
- build_report_html(source_filename: str, analysed_at_text: str, columns: list[ColumnResult]) -> str: a complete standalone HTML5 document: <meta charset="utf-8">; <title>IMR report — {filename} — {timestamp}</title>; a short inline <style> block (red box for .rejected, amber box for .warning, table borders, the scroll container); an <h1> with the same filename and timestamp; then build_column_section_html(column, include_downloads=False) for every column in order. It contains no upload form, no download links, no <script>, no <link> tags, and no external URL of any kind — it must work with the network off.

Tests first, appended to tests/test_builders.py. Build ColumnResult objects by hand; for png use real bytes from render_chart on a small fixed series so the base64 is realistic:
- Summary table: contains all eleven row labels in order and fmt values; the I table's sigma label reads "Sigma (MR-bar / 1.128)" and the MR table's "Sigma (0.7557 x MR-bar)"; an MR chart whose -2 and -3 lines are negative shows "(below 0, not drawn)" on exactly those two rows; an I chart with negative lines never shows it.
- Observations block: headings for I and MR; descriptions verbatim; "No Nelson patterns detected." when empty; a description containing "<" is escaped.
- Column section: heading present; a warning column shows the warning box before the first <img>; a rejected column shows the rejected box and contains no <img> and no <table>; include_downloads=False contains no "/download/"; include_downloads=True contains "/download/png/{index}/I" and "/download/png/{index}/MR".
- Report: starts with "<!DOCTYPE html>", contains the filename and timestamp in <title> and <h1>, one <section> per column, and images as data URIs; contains no "<form", no "/download/", no "<script", no "<link", no "http://" and no "https://"; a column name containing "&" is escaped.

Rules for this step
- Change only section 7 of imr.py and tests/test_builders.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 15: column-section HTML and standalone report"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 16 — The analysis pipeline (V10, W01)

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green, all Flask-free: section 3 parse_csv(data, filename) -> ParsedFile(source_filename, stem, n_rows, columns: list[ParsedColumn(name, index, values)]) or raises ValidationErrors; section 4 individuals_series, moving_range_series, i_chart_stats(values), mr_chart_stats(values), lines_below_zero, fmt (ChartStats has n, mean, mr_bar, sigma, lines); section 5 detect_all(series, lines, field, chart) and pattern_points; section 6 render_chart(series, stats, pattern_pts, title, y_label, n_total, hide_ks); section 7 build_observations_csv(columns), warning_text(n), build_column_section_html(column, include_downloads), build_report_html(source_filename, analysed_at_text, columns). Dataclasses include ChartResult, ColumnResult and AnalysisResult(source_filename, stem, analysed_at, columns, report_html, observations_csv). Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_guardrails.

This step adds the single integration point that joins every section: the analysis pipeline. Put it at the end of SECTION 7, under the sub-banner comment "# ----- 7.3 Analysis pipeline -----", so it stays Flask-free and unit-testable. It is also where the column-level check V10 and the W01 warning live (SPEC.md §4.6, §7.1). V11 is retired in SPEC v1.1 and must not be implemented.

Implement:
- timestamp_text(dt: datetime) -> str: local time as "YYYY-MM-DD HH:MM:SS".
- analyse_column(column: ParsedColumn) -> ColumnResult:
  1. I chart: series = individuals_series(values); stats = i_chart_stats(values). If stats.mr_bar == 0 (every value identical — under the moving-range method the only way a sigma can be zero) → reject (severity C, V10) with rejected_reason "All {n} values in {name} are identical ({fmt(value)}), so there is no variation to chart and no limits can be drawn for this column." — both charts None.
  2. MR chart: mr = moving_range_series(values); mr_stats = mr_chart_stats(values) (the original values, not mr.values). No separate rejection: a column with identical gaps, such as a straight line, is charted normally.
  3. warning = warning_text(n) when n < WARN_BELOW_POINTS, else None (W01; processing continues).
  4. Observations: detect_all(series, stats.lines, field=name, chart="I") and detect_all(mr, mr_stats.lines, field=name, chart="MR"). All eight rules run on BOTH charts with identical thresholds — this is deliberate (SPEC.md Appendix B, D3); do not restrict the MR chart to Rule 1.
  5. PNGs: render_chart for the I chart with title f"{name} — Individuals (I) chart", y label "Value", n_total = n, no hidden lines; for the MR chart with title f"{name} — Moving Range (MR) chart", y label "Moving range", n_total = n, hide_ks = lines_below_zero(mr_stats).
  6. Return ColumnResult(name, index, n, warning, None, ChartResult("I", …, pattern_points(i_obs), png), ChartResult("MR", …)).
- analyse(parsed: ParsedFile, analysed_at: datetime | None = None) -> AnalysisResult: analysed_at defaults to datetime.now(); analyse every column in order; build observations_csv with build_observations_csv and report_html with build_report_html(parsed.source_filename, timestamp_text(analysed_at), columns). Report and CSV are built here, once, and held in the result so a download never recomputes anything (SPEC.md §6.6).

Tests first, in tests/test_pipeline.py (create it). Feed parse_csv with CSV bytes built inline from hand-typed values (no random numbers):
- A two-column, 25-row file analyses fully: two ColumnResults in order, no warnings, no rejections, both ChartResults present, MR point numbers 2..25, stats.n 25 and 24, PNGs non-empty.
- pattern_points of each ChartResult equals the union of its observations' points; every observation's field and chart are set correctly.
- Sigma follows the moving-range method: for one column, compute the moving ranges and their mean by hand in the test; the I chart's stats.sigma == pytest.approx(mr_bar / 1.128) and the MR chart's stats.sigma == pytest.approx(0.7557 * mr_bar), with the MR chart's stats.mean equal to mr_bar (use the literal numbers in the test, not imr's constants).
- A column of identical values is rejected with the V10 text (name and value present), both charts None; the other column in the same file still analyses normally.
- A straight-line column (1, 3, 5, …, 49 — 25 rows) is NOT rejected: its I chart includes a Rule 3 rising observation covering points 1–25, and its MR chart's only observation is Rule 7 covering MR points 2–25 (every moving range equals the average, so all sit inside ±1 SD).
- A 15-row file carries the W01 warning text on every column and still has charts and observations.
- observations_csv equals build_observations_csv(result.columns); report_html contains every column name and no "/download/".
- Passing analysed_at=datetime(2026, 9, 26, 14, 30, 5) puts "2026-09-26 14:30:05" in the report.
- Same input twice → identical observations_csv and identical PNG bytes (determinism, SPEC.md §8).

Rules for this step
- Change only section 7 of imr.py and tests/test_pipeline.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 16: analysis pipeline with V10 and W01"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 17 — Upload page and `/analyze`

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green, all Flask-free: parse_csv(data, filename) -> ParsedFile or raises ValidationErrors (whose .issues are ValidationIssue(code, severity, message)); analyse(parsed, analysed_at=None) -> AnalysisResult(source_filename, stem, analysed_at, columns, report_html, observations_csv); timestamp_text(dt); build_column_section_html(column, include_downloads=False); all statistics, rules and rendering. Section 8 (# ===== SECTION 8: FLASK APP AND ROUTES =====) is empty. Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_guardrails (which requires that Flask is imported nowhere before the section 8 banner).

This step builds the browser page and the analyse action (SPEC.md §2.2, §6.1, §7.1 V01, §7.3, §7.4, §9.3). Downloads come in the next step — this page shows NO download links yet, so nothing on it points at a route that does not exist.

In SECTION 8 (this is the only place Flask is imported: put "from flask import Flask, request, Response" at the top of section 8):
- LAST_RESULT: module-level variable holding the most recent AnalysisResult, or None. reset_state() sets it back to None (tests call it).
- PAGE_TEMPLATE: the page as a Python string (no template files). Plain, functional HTML; appearance is explicitly unimportant (SPEC.md §1.3). It contains: a title "IMR Control Chart Tool"; when there are errors, a red error box ABOVE the form listing every issue message as a list item; the upload form — method POST, action /analyze, enctype multipart/form-data, one file input named "file" accepting .csv, a submit button "Analyze" — always present; then, when a result exists, a results header showing the source filename and the analysis timestamp, followed by build_column_section_html(column, include_downloads=False) for every column. Insert pre-built HTML fragments as-is (they are already escaped by the builders); escape everything else with html.escape. Fill it with str.replace or simple formatting — no Jinja features are needed.
- create_app() -> Flask: a new Flask app with these routes (debug off; do NOT set MAX_CONTENT_LENGTH — the parser reports oversized files itself with the V03 message):
  GET / → 200, the page with the form, plus the results of LAST_RESULT if there is one.
  POST /analyze →
    - no "file" part in the request, or an empty filename → V01: status 400, page with the error box "No file was selected. Choose a .csv file and click Analyze."
    - otherwise read the bytes and call parse_csv; on ValidationErrors → status 400, page with every issue message in the error box. On success call analyse, store the result in LAST_RESULT, and return status 200 with the page showing the results.
    - any failure (validation or unexpected) clears LAST_RESULT first, so what is on screen always comes from one file.
    - any unexpected exception → status 500 with a plain page: "Something went wrong while analysing {filename}. The details have been printed in the console window." and the full traceback printed to the console (traceback.print_exc()). No stack trace, no Python exception name ever reaches the browser.
- The server keeps nothing on disk: the uploaded bytes live only for the request; LAST_RESULT lives in memory until the next upload.

Tests first, in tests/test_routes.py (create it). Use app = create_app(); client = app.test_client(); call reset_state() in a fixture before each test. Build uploads with data={"file": (io.BytesIO(csv_bytes), "name.csv")} and content_type="multipart/form-data". Use small inline CSVs built from hand-typed values (25 rows, two IMR_Field columns and one Notes column):
- GET / → 200, contains a <form with action="/analyze" and an input named "file", and no results.
- POST a good file → 200; the page contains each IMR_Field column heading, the source filename, an <img src="data:image/png;base64, and does not contain the Notes column as a heading; no "rejected" box.
- GET / afterwards still shows the same results.
- POST with no file part → 400 with the V01 message; POST with an empty filename → 400 as well.
- POST a .txt file → 400 with the V02 message; POST a file with two problems (a bad cell and a ragged row) → 400 and both messages appear.
- A failed upload after a good one clears the previous results (the earlier column heading is gone).
- A second good upload replaces the first (the first file's column headings are gone, the second's present).
- Monkeypatch imr.analyse to raise RuntimeError("boom") → 500, the body contains "Something went wrong while analysing" and does not contain "RuntimeError", "boom" or "Traceback".
- The page contains no "/download/" link yet.

Rules for this step
- Change only section 8 of imr.py and tests/test_routes.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls; no files written by the server. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 17: upload page and analyze route"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 18 — Downloads

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: the complete Flask-free core (parse_csv, analyse -> AnalysisResult(source_filename, stem, analysed_at, columns, report_html, observations_csv), sanitise_name, build_column_section_html(column, include_downloads=False) which, when include_downloads=True, adds "Download PNG" links to /download/png/{column.index}/I and /MR; ColumnResult has index, rejected_reason and ChartResults holding png bytes), and in section 8: LAST_RESULT, reset_state(), PAGE_TEMPLATE, and create_app() with GET / and POST /analyze. The page currently shows no download links. Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_routes, test_guardrails.

This step adds the three downloads (SPEC.md §6.6, §7.3, §9.3) and the links that point at them. Everything served comes from LAST_RESULT; nothing is recomputed and nothing is written to disk.

In section 8, add to create_app():
- GET /download/report → LAST_RESULT.report_html, content type "text/html; charset=utf-8", Content-Disposition: attachment; filename="{stem}_IMR_report.html".
- GET /download/observations → LAST_RESULT.observations_csv encoded UTF-8, content type "text/csv; charset=utf-8", Content-Disposition: attachment; filename="{stem}_observations.csv".
- GET /download/png/<int:column_index>/<chart> → chart must be "I" or "MR"; column_index is the 0-based position among the charted columns (ColumnResult.index); returns that ChartResult's png bytes with content type "image/png", Content-Disposition: attachment; filename="{stem}_{sanitise_name(column name)}_{chart}.png". An unknown chart, an index out of range, or a rejected column → 404 with a short plain message.
- Any download before a successful analysis (LAST_RESULT is None) → 404 with the body "Nothing has been analysed yet. Upload a file first."
Then update the page: the results header gains two links, "Download report (HTML)" → /download/report and "Download observations (CSV)" → /download/observations, and each column section is now built with include_downloads=True so every chart has its "Download PNG" link. The downloadable report itself still has no links and no form (it is built by build_report_html, which is unchanged).

Tests first, appended to tests/test_routes.py (reset_state() before each test, uploads built inline from hand-typed values as in the existing tests):
- Each download before any upload → 404 with the exact message above.
- After uploading "My Data.csv" with the two columns IMR_Field_A and "IMR_Field (B)" (25 rows): /download/report → 200, text/html, filename "My_Data_IMR_report.html", body equals the stored report_html and contains no "<form"; /download/observations → 200, text/csv, filename "My_Data_observations.csv", parses with csv.reader and its header row is field,chart,rule_no,rule_name,direction,points,values,line_or_window,description; /download/png/0/I and /download/png/0/MR → 200, image/png, PNG signature, bytes equal to the stored png, filenames "My_Data_IMR_Field_A_I.png" and "My_Data_IMR_Field_A_MR.png".
- The second column's PNG filename is sanitised: /download/png/1/I → "My_Data_IMR_Field__B__I.png".
- /download/png/0/X → 404; /download/png/9/I → 404; a rejected column's PNG (e.g. a column of identical values) → 404.
- The results page now contains one link each to /download/report and /download/observations, plus /download/png/{i}/I and /download/png/{i}/MR for every non-rejected column, and no PNG links for a rejected column.
- After a failed upload, every download is 404 again.

Rules for this step
- Change only section 8 of imr.py and tests/test_routes.py. Do not touch any other section, any other test file, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls; no files written by the server. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 18: downloads"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover.
```

### Step 19 — Entry point and README

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: the complete application except startup — parsing, statistics, rule engine, rendering, builders and pipeline (sections 3–7), and in section 8 create_app() with GET /, POST /analyze and the three download routes, all tested. Section 9 (# ===== SECTION 9: ENTRY POINT =====) holds only a placeholder print. Constants include PORT_CANDIDATES = range(5000, 5011). Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_routes, test_guardrails.

This step makes "python imr.py" start the tool (SPEC.md §2.2, §8, §9.5) and writes the owner's README.

In section 9, replace the placeholder:
- find_free_port(host="127.0.0.1", candidates=PORT_CANDIDATES) -> int | None: for each candidate, try to bind a plain socket on (host, port); return the first that binds (close the test socket first); None if all are busy.
- open_browser_later(url, delay=1.0): start a daemon threading.Timer that calls webbrowser.open(url).
- main() -> int:
  1. port = find_free_port(); if None, print "Ports 5000-5010 are all in use. Close another program using them and try again." and return 1.
  2. url = f"http://127.0.0.1:{port}/"; print "IMR Control Chart Tool is running at {url} - keep this window open; press Ctrl+C to stop." (plain ASCII — the Windows console can mangle other characters).
  3. open_browser_later(url).
  4. create_app().run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=False). Always 127.0.0.1 — never 0.0.0.0 anywhere in the file.
  5. return 0.
- if __name__ == "__main__": sys.exit(main())

Write README.md for the owner, who does not read code, in plain language: what the tool does; one-time setup (python -m venv .venv, activate it, pip install -r requirements.txt); how to run (python imr.py, the browser opens by itself, keep the console window open); how to prepare a CSV (row 1 is the header, row order is time order, columns to chart start with IMR_Field — exact capitals, every cell in those columns a plain number with no blanks, commas as thousands separators or % signs; other columns are ignored; at least 3 rows, ideally 20+); how to read the output (the seven lines, red triangles = points caught by a Nelson rule, the numbered observations, the summary table, the MR chart numbering starting at 2); a short note on the method: sigma is estimated from the average moving range (average moving range ÷ 1.128 on the I chart; 0.7557 × average moving range on the MR chart, which is centred on the average moving range) — the standard IMR method, so the lines match Minitab or JMP to the precision of these constants and will NOT match a plain Excel STDEV.S calculation; and all eight rules run on the MR chart, where patterns from Rules 2–8 are "worth a look" rather than "act on it" (SPEC.md Appendix B, D3); the three downloads; how to run the tests (pytest); and that nothing is saved between runs.

Tests first, appended to tests/test_routes.py:
- find_free_port with an explicit candidate list: occupy one port by binding a socket yourself (bind to port 0, read the port it got), then call find_free_port(candidates=[that_port, another_free_port]) and assert it returns the second; with only the occupied port it returns None.
- main() with monkeypatching: replace find_free_port to return 5055, replace webbrowser.open with a recorder, replace the Flask run method (monkeypatch Flask.run on the class, or create_app) with a recorder, and replace threading.Timer's start or open_browser_later so the test does not wait; assert run was called with host "127.0.0.1", port 5055, debug False, and main returns 0.
- main() when find_free_port returns None returns 1 and prints the ports message (capsys).
Append to tests/test_guardrails.py:
- the text "0.0.0.0" does not appear in imr.py.

Rules for this step
- Change only section 9 of imr.py, README.md, tests/test_routes.py and tests/test_guardrails.py (append only). Do not touch any other section, CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Tests first: write them, run them and watch them fail, then implement until they pass. Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls; no files written by the server. Running all eight Nelson rules on both charts is deliberate (SPEC.md Appendix B, D3) — do not "correct" it.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 19: entry point and README"
- Then write a short plain-English summary: what you built, how many tests now pass, and any decision you had to make that these instructions did not cover. End the summary with the exact two commands the owner should type to start the tool for the first time.
```

### Step 20 — Sample dataset

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: the complete application — parse_csv(data, filename) -> ParsedFile, analyse(parsed) -> AnalysisResult whose columns are ColumnResults with individuals and moving_range ChartResults (each with observations, a list of Observation with rule_no, direction, points …) and observations_csv; the Flask page and downloads; "python imr.py" starts the server. Both charts' lines use the standard moving-range sigma (I chart: average moving range ÷ 1.128; MR chart: centred on the average moving range with sigma 0.7557 × average moving range), and all eight Nelson rules run on both charts. Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_routes, test_guardrails.

This step creates the bundled sample dataset (SPEC.md §11.1–11.3). The answer key and the end-to-end acceptance test come in the next step, after the owner has checked the numbers — do NOT create sample/sample_answer_key.csv in this step.

Create sample/sample_imr.csv, UTF-8 without a BOM, 40 data rows, with these columns in this order: IMR_Field_Rule1, IMR_Field_Rule2, IMR_Field_Rule3, IMR_Field_Rule4, IMR_Field_Rule5, IMR_Field_Rule6, IMR_Field_Rule7, IMR_Field_Rule8, IMR_Field_Clean, Notes.
Requirements:
- IMR_Field_RuleK triggers Rule K on its I chart at least once, for every K from 1 to 8.
- IMR_Field_Clean triggers NOTHING on either chart (I or MR) — no rule at all.
- Notes is ignored by the tool; fill it with short free text, some blanks, and at least one value containing a comma (quoted) to prove non-IMR columns can contain anything.
- Other incidental triggers are acceptable (a Rule 1 spike often also satisfies Rule 5; a strong I-chart pattern usually produces something on the MR chart). They will be recorded in the answer key next step.
- Every value is a fixed, hand-typed number with at most 2 decimals — no random generation, no generator script left in the repository — so the file is reproducible and checkable in Excel.
How to build it (SPEC.md §11.3): sigma comes from the average moving range, which a level shift or a slow trend barely moves, but every sharp jump adds a large moving range and widens sigma. Start each column from a stable baseline of small, irregular noise around a round number (for example 50 ± 1), inject the pattern, run the engine, and adjust the pattern's size or length until the target rule fires. Useful tactics: Rule 7 needs 15+ consecutive points hugging the mean in a column whose moving ranges are larger elsewhere (a jumpier stretch raises the average moving range and so widens the ±1 SD band); Rule 8 is easiest with blocks — several points well above +1 SD, then several well below -1 SD, none in between — not rapid alternation, because alternation creates huge moving ranges that widen sigma; Rule 4 needs 14+ strictly alternating up/down moves; Rule 2 needs a sustained level shift; Rule 3 needs 6+ strictly rising or falling values with no ties; the Clean column must avoid 15 consecutive points inside ±1 SD, 14 alternating moves, 9 on one side, 6 steady moves, and must keep its MR chart quiet too — the moving ranges of plain noise are skewed (many small, a few large), so their MR chart readily shows 9+ in a row below the average moving range or 15+ inside ±1 SD; vary the gap sizes deliberately and check that chart first. You may use a throwaway Python snippet in the terminal to check your work; do not commit it.

Tests first, in tests/test_sample.py (create it). Load the file with parse_csv(Path("sample/sample_imr.csv").read_bytes(), "sample_imr.csv") and run analyse:
- exactly nine charted columns, in the order above; Notes is not among them; n_rows == 40.
- no column is rejected and no column has a warning (40 ≥ 20).
- for each K in 1..8, IMR_Field_RuleK's individuals observations include at least one with rule_no == K (parametrise over K).
- IMR_Field_Clean has zero observations on both charts.
- every value in the charted columns has at most 2 decimal places (check the raw text of the file).

Rules for this step
- Create only sample/sample_imr.csv and tests/test_sample.py. Do not change imr.py or any other file, and never modify CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md. If you believe the engine is wrong while building the data, stop and report it — do not change the engine.
- Tests first: write them, run them and watch them fail, then create the data until they pass.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls.

Done when
- pytest passes in full — the whole suite, not only this step's file.
- Commit: git add -A && git commit -m "Step 20: sample dataset"
- Then write a short plain-English summary: for each of the nine columns, which rows hold the injected pattern and every rule (on each chart) that the column triggers, including incidental ones; how many tests now pass; and any decision you had to make that these instructions did not cover.
```

### Step 21 — Answer key and acceptance test (owner verification gate)

```text
You are continuing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: the complete application (parse_csv, analyse -> AnalysisResult with observations_csv in the schema field,chart,rule_no,rule_name,direction,points,values,line_or_window,description; the Flask page and downloads; "python imr.py"), sample/sample_imr.csv (40 rows: IMR_Field_Rule1 … IMR_Field_Rule8, IMR_Field_Clean, Notes) and tests/test_sample.py proving each RuleK column triggers rule K on its I chart and the Clean column triggers nothing. Tests: test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_routes, test_sample, test_guardrails.

This step creates the answer key and the build's acceptance test (SPEC.md §11.1, §11.4, §12.8) — and deliberately stops before committing, because an answer key copied from the engine only protects against future regressions; it cannot tell a right implementation from a wrong one. The owner will check the numbers by hand in Excel and commit.

1. Generate sample/sample_answer_key.csv: run parse_csv + analyse on sample/sample_imr.csv and write the observations_csv exactly (UTF-8, no BOM). Before accepting it, check it yourself by hand, not with the engine: for IMR_Field_Rule5 and IMR_Field_Rule7, recompute from the raw numbers the mean, the moving ranges, the average moving range, sigma = average moving range / 1.128, the seven lines, and which points should trigger the target rule, and confirm every row of the key for those two columns (I chart) is what the rule definitions in SPEC.md §5 say. If anything disagrees, stop and report — do not adjust the key to match the engine.
2. Append to tests/test_sample.py the acceptance test: run the full pipeline on sample/sample_imr.csv and compare its observations CSV with sample/sample_answer_key.csv as parsed rows (csv.reader on both, so line endings do not matter) — equal row for row, including the header. Also assert the key has the §6.7 header, at least one row for every rule number 1–8, and no row for IMR_Field_Clean.
3. Write docs/answer_key_check.md — a one-page sheet for the owner, who will verify in Excel without reading code. For IMR_Field_Rule5 (I chart, data in column E) list, step by step: the mean (=AVERAGE(E2:E41)); the moving ranges in an empty column, e.g. L3 =ABS(E3-E2) filled down to L41 (row 3 = MR point 2); the average moving range (=AVERAGE(L3:L41)); sigma (=average moving range/1.128); the seven lines (mean + k × sigma); the expected value of each to 3 decimals; and the rows/points that should trigger Rule 5 with their values and which line they cross. Do the same for IMR_Field_Rule7 (column G). Add a third, short section for the MR chart of IMR_Field_Rule1 (column A): the moving ranges (=ABS(A3-A2) filled down), the average moving range, sigma (=0.7557 × average moving range), its seven lines (average moving range + k × sigma), and which of them are below zero. State at the top of the sheet that the tool deliberately does NOT use Excel's STDEV.S.
4. Run the full suite. Then stage the new files (git add -A) but DO NOT COMMIT. The owner commits after checking.

Rules for this step
- Create only sample/sample_answer_key.csv and docs/answer_key_check.md, and append to tests/test_sample.py. Do not change imr.py or sample/sample_imr.csv, and never modify CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md.
- Never edit an existing test to make new code pass — if you believe a test is wrong, stop and say so.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls.

Done when
- pytest passes in full — the whole suite.
- The files are staged and NOT committed.
- Then write a short plain-English summary: the number of rows in the answer key and how many per rule; the result of your own hand check of Rule5 and Rule7; and this exact instruction for the owner: "Open docs/answer_key_check.md and sample/sample_imr.csv in Excel, type the formulas, and compare. If every number matches to 3 decimals, run: git commit -m \"Step 21: answer key (owner-verified)\". If anything differs, do not commit — bring the difference back."
```

### Step 22 — Final audit, pinning and tag

```text
You are finishing the IMR Control Chart Tool: one Python 3.11 file, imr.py, that runs a local Flask page where the owner uploads a CSV and gets Individuals (I) and Moving Range (MR) control charts for every column whose header starts with IMR_Field, with all eight Nelson rules applied to both charts. Everything is local (no GitHub, no CI, no network) and verified with pytest. Read CLAUDE.md (guardrails) and SPEC.md (specification) in the repository root before doing anything, and never modify them, BLUEPRINT.md or todo.md.

Already on disk and green: the complete application (sections 1–9 of imr.py), README.md, requirements.txt, sample/sample_imr.csv, sample/sample_answer_key.csv (verified by the owner by hand and committed), docs/answer_key_check.md, and the tests test_guardrails, test_stats, test_rules, test_parsing, test_render, test_builders, test_pipeline, test_routes, test_sample.

This step is an audit, not new features. Its job is to prove SPEC.md §13.1 "done" and leave the repository in a clean, tagged state.

1. Coverage audit against the testing plan. Walk through SPEC.md §12.1 to §12.8 bullet by bullet. For each bullet, find the test that covers it. Where one is missing, add it to the matching test file (test_stats, test_rules, test_parsing, test_render, test_routes or test_sample; tests for the builders and pipeline go in test_builders / test_pipeline). Only add tests; if a new test fails, stop and report — do not change application code in this step.
2. Performance (SPEC.md §2.3), in tests/test_pipeline.py: build a 10-column × 100-row CSV in the test from a deterministic formula (for example value = 50 + ((i * 7 + c * 3) % 11) / 4 for row i and column c — no random numbers), and assert that parse_csv + analyse completes in under 5 seconds, and that parse_csv alone completes in under 1 second.
3. Guardrail audit: read CLAUDE.md line by line and confirm each rule holds in the code; list any rule not already enforced by tests/test_guardrails.py and add a check for it where it can be checked mechanically.
4. requirements.txt: confirm every line is pinned (==) to the version actually installed (pip freeze for flask, matplotlib, pytest) and that nothing else is listed.
5. README.md: re-read it against the finished tool and correct anything that is no longer accurate.
6. Offline check: confirm imr.py contains no "http://" or "https://" apart from the local 127.0.0.1 address in section 9, and that the page and the report reference no external asset.

Rules for this step
- Change only test files, README.md and requirements.txt. Do not change imr.py or the sample files; never modify CLAUDE.md, SPEC.md, BLUEPRINT.md or todo.md. If the audit reveals a bug in imr.py, stop and report it with the failing test — the fix gets its own session.
- Sigma comes only from the average moving range through the named constants D2_CONSTANT and MR_SIGMA_FACTOR — never the plain sample SD (statistics.stdev), never the shortcuts 2.66 or 3.267, and never the numbers 1.128 or 0.7557 typed anywhere in imr.py except their one definition in section 1, and never the words stdev, pstdev or variance anywhere in imr.py, not even in a comment or docstring; no pandas; no direct numpy import; no network calls.

Done when
- pytest passes in full.
- Commit: git add -A && git commit -m "Step 22: final audit" and then tag: git tag v1.0
- Then write a short plain-English summary: the number of tests, which §12 bullets needed new tests, the timing of the performance test, anything in CLAUDE.md that could not be checked mechanically, and a reminder that the owner should now run the manual checklist in SPEC.md §12.9 (it is also in todo.md).
```

---

## Appendix — CLAUDE.md (create in the repository root before Step 1)

A copy is provided as a separate `CLAUDE.md` file. It restates SPEC.md §13.3 plus the build-process rules and the blueprint decisions the code must honour.

```text
# CLAUDE.md — IMR Control Chart Tool

These rules are non-negotiable in every session. SPEC.md is the specification; BLUEPRINT.md holds the step prompts; todo.md is the owner's checklist. Never modify SPEC.md, BLUEPRINT.md, todo.md or this file.

## Architecture
1. The application is exactly one file, imr.py, with nine banner sections in fixed order (constants, data classes, parsing and validation, statistics, rule engine, rendering, report and CSV builders, Flask app and routes, entry point). Tests, sample data and documents live outside it.
2. Sections 3–7 never import Flask. Flask is imported only in section 8.
3. No pandas. No direct numpy import. Standard library + Flask + matplotlib (Agg backend) only.
4. No network access, no CDN, no external assets. The server binds to 127.0.0.1 only, never 0.0.0.0, and writes no files.

## Statistics (standard IMR method — SPEC.md §4) and the one deliberate departure (D3)
5. Sigma comes only from the average moving range (MR-bar). I chart: centre = mean, sigma = MR-bar / D2_CONSTANT. MR chart: centre = MR-bar, sigma = MR_SIGMA_FACTOR x MR-bar. D2_CONSTANT = 1.128 and MR_SIGMA_FACTOR = 0.7557 are each defined once in section 1 and referred to by name everywhere else, including display text. The rounded shortcuts 2.66 and 3.267 never appear. The plain sample SD (Excel STDEV.S) is never used for the lines, and the words stdev, pstdev and variance must not appear anywhere in imr.py, not even in a comment or docstring.
6. All eight Nelson rules run on both the I chart and the MR chart, standard thresholds, held as named constants. This is deliberate (SPEC.md Appendix B, D3). Do not restrict the MR chart to Rule 1.
7. MR points are numbered 2 … N, aligned with the I chart. There is no MR point 1.

## Rule engine
8. Comparisons are strict. A value exactly on a line (tolerance 1e-9 × max(1, |line|)) belongs to neither side and breaks runs. Equal neighbours break Rule 3 and Rule 4 runs. All comparisons go through the zone predicates.
9. Run rules produce one observation per maximal run, covering every point of the run. Window rules list only the out-of-zone points and report the merged window span.
10. Rules report point numbers, never list positions. Comparisons use unrounded values; rounding to 3 decimals happens only for display.

## Text
11. Negative numbers and line names use the plain ASCII hyphen-minus ("-1 SD"). The em dash after "Rule N" and the en dash in point spans in descriptions are kept exactly as SPEC.md §5.5 writes them. Console output is plain ASCII.
12. Every user-facing message says what happened, where, and what to do. No stack traces or Python exception names in the browser.

## Process
13. Tests first. Never edit an existing test to make new code pass; if a test looks wrong, stop and say so.
14. Stay inside the files each step names. If a change needs another file, stop and ask.
15. The whole suite must be green before a step's commit. Commit at the end of each step unless the step says otherwise.
16. End every step with a plain-English summary for a non-technical owner: what was built, how many tests pass, and any decision not covered by the instructions.
```
