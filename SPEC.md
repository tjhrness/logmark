# IMR Control Chart Tool — Developer Specification v1.1

**Product:** IMR Control Chart Tool (personal utility)
**Purpose:** Detect special causes in time-ordered data using Individuals and Moving Range charts with Nelson-rule pattern detection
**Platform:** Standalone local web application, Windows, Python 3.11, run from a single Python file
**Date:** 26 September 2026
**Supersedes:** v1.0 (26 September 2026)
**Sibling build:** Pareto Chart Tool (same build pattern: one Python file, local server, browser UI, pytest, blueprint-driven `/step` execution)

---

## Changes in v1.1

| # | Change | Sections |
|---|---|---|
| 1 | **Sigma now comes from the moving ranges (standard IMR method).** I chart: `σ_I = MR̄ ÷ 1.128`. MR chart: `σ_MR = 0.7557 × MR̄`, centred on MR̄. v1.0's plain sample SD (Excel `STDEV.S`) on both charts is withdrawn. Owner decision, 26 Sep 2026, reversing Appendix B D1 and D2 | §1, §4, §5.6, §6.3, §9.4, §11, §12, §13.3, App. A–C |
| 2 | All eight rules on the MR chart **kept** (D3), with its rationale now recorded | §5.6, App. B |
| 3 | V11 (zero MR-chart SD) **retired**: under the moving-range method it can only happen when every value is identical, which V10 already catches. A perfectly straight line is now charted normally | §4.6, §7.1 |
| 4 | Summary table shows the average moving range (MR̄) and how sigma was derived, so every line can be rechecked in Excel | §6.3 |
| 5 | Worked examples E4, E5 and E14 corrected to list **every** observation they produce (E5 cannot fire Rule 2: it has 8 points; E4 and E5 also fire Rules 1, 5, 6 and 8; E14 also fires Rule 2) | §5.9 |
| 6 | Plain hyphen-minus everywhere for negative numbers and line names; V07 lists at most 20 rows; trailing blank lines ignored; pixel-width test nuance; three extra test files; pipeline sub-banner | §3.1, §4.5, §6.2, §7.1, §9.2, §9.6, §12.6 |

---

## 0. Reading guide

This document is written to be implemented from directly. It assumes no prior conversation.

- **[CONFIRMED]** — explicitly agreed with the product owner during the 21-question specification interview
- **[DEFAULT]** — assumed by the specification author, open to challenge. Consolidated in Appendix A. Items marked *(post-interview)* were added while writing this document and have not yet been seen by the product owner
- **[DEV]** — implementation detail delegated to the developer's judgement

Sections 1–8 are requirements. Sections 9–13 are implementation guidance. Appendices carry the decision audit trail.

One decision in this specification goes against standard SPC practice: **all eight Nelson rules run on the Moving Range chart** (Appendix B, D3). It is deliberate. **Implement it as written; do not "correct" it.** The limits themselves follow the standard moving-range method (§4) — v1.0's plain-SD departures (D1, D2) were reversed in v1.1.

---

# PART I — REQUIREMENTS

## 1. Purpose and scope

### 1.1 Problem statement

The product owner has time-ordered numeric data (one or more series per file) and needs to know where each series shows evidence of a *special cause* — a change that is not ordinary noise. The standard instrument for this is the IMR chart pair with Nelson's eight rules applied to it. The tool draws the charts, applies the rules, marks the offending points, and writes down exactly which points triggered which rule, so the owner can go and investigate those points.

### 1.2 In scope

- Upload of a CSV file through a browser page
- Automatic selection of every column whose name starts with `IMR_Field`
- For each such column: an Individuals (I) chart and a Moving Range (MR) chart
- Seven horizontal lines on each chart (centre, ±1, ±2, ±3 SD), with SD estimated from the moving ranges as in any standard IMR chart (§4)
- All eight Nelson rules, standard thresholds, applied to **both** charts
- Numbered data points, pattern points drawn as red triangles
- A written list of every detected pattern under each chart, with point numbers, values, and the line or window involved
- A summary table of the statistics under each chart
- Downloads: the whole results page as a standalone HTML file, each chart as a PNG, all observations as a CSV
- A bundled sample dataset with an answer key, used both for the owner's own checking and by the automated tests

### 1.3 Explicitly out of scope

| Excluded | Rationale |
|---|---|
| Aesthetics, branding, responsive layout | Personal tool; owner explicitly deprioritised appearance **[CONFIRMED]** |
| Excel (`.xlsx`) input | CSV only **[CONFIRMED]** |
| Interactive charts (hover, zoom) | Static images chosen **[CONFIRMED]** |
| Plain sample SD (Excel `STDEV.S`) as the basis for the lines | Withdrawn in v1.1 — it is inflated by the very special causes the tool looks for. The standard moving-range sigma is used (§4; Appendix B, D1–D2) |
| Adjustable rule thresholds or switching rules on/off | Fixed standard thresholds **[CONFIRMED]** |
| Date/time axis, sorting by a time column | Row order is the time order **[CONFIRMED]** |
| Multi-user access, authentication, network access | Single user, localhost only |
| Saving results between sessions, run history | Nothing is stored; each upload replaces the previous results |
| Packaging as a Windows executable | Run with `python imr.py`, like the Pareto tool. Can be added later without changing anything in this document |

### 1.4 Terminology (plain-language glossary)

| Term | Meaning in this document |
|---|---|
| Point | One numeric value in a column, in row order. Points are numbered 1 to N from the first data row |
| Individuals (I) chart | The column's values plotted in order, one point each |
| Moving range (MR) | The size of the jump between a point and the one before it: `MR_i = |x_i − x_{i−1}|`. Always zero or positive |
| MR chart | The moving ranges plotted in order |
| Mean | Ordinary arithmetic average of the series being charted |
| Average moving range (MR̄, "MR-bar") | The mean of all the moving ranges in a column. On the MR chart it is also the centre line |
| SD (sigma, σ) | The process standard deviation **estimated from the moving ranges**, as in every standard IMR chart: `MR̄ ÷ 1.128` on the I chart and `0.7557 × MR̄` on the MR chart (§4). It is **not** the Excel `STDEV.S` of the column. Line labels say "SD" for readability |
| Line k | The horizontal line at `centre + k × SD`, for k in −3, −2, −1, 0, +1, +2, +3. The centre is the mean on the I chart and MR̄ on the MR chart |
| Zone test | A comparison of a point against one of the lines (above / below / within) |
| Run | A stretch of consecutive points that all satisfy the same test |
| Nelson rules | Eight standard tests for non-random patterns, defined in §5 |
| Observation | One written entry describing one detected pattern |

---

## 2. User and workflow

### 2.1 User

One user, the product owner, on his own Windows machine. No login, no roles. **[CONFIRMED]**

### 2.2 Primary workflow

```
1. User runs `python imr.py`; the server starts and the default browser opens the upload page
2. User selects a .csv file and clicks Analyze
3. System validates the file (§7). On any file-level problem it shows every problem found and stops
4. System computes both charts and runs all eight rules for every IMR_Field column
5. Results page renders: one section per column, in file column order
6. User reads the observations, optionally downloads the report, PNGs, or the observations CSV
7. User uploads another file; the previous results are discarded
```

### 2.3 Timing expectations **[DEFAULT]**

| Step | Budget |
|---|---|
| Upload + validation | < 1 second |
| Analysis + chart rendering, 10 columns × 100 points | < 5 seconds |
| Any download | < 1 second |

Synchronous processing inside the request is acceptable within these budgets. No background jobs.

---

## 3. Data input

### 3.1 File **[CONFIRMED: CSV only]**

- Extension `.csv` (case-insensitive) **[DEFAULT]**
- Comma delimiter; UTF-8 encoding, with or without a byte-order mark **[DEFAULT]**
- Row 1 is the header row and is required **[DEFAULT]**
- Every data row must have exactly as many cells as the header row; ragged rows reject the file (§7.1, V07) **[DEFAULT — post-interview]**. A completely blank line *between* data rows is a ragged row (0 cells); completely blank lines after the last data row are ignored, because Excel and text editors leave them behind **[DEFAULT — v1.1]**
- Upload size cap 10 MB **[DEFAULT — post-interview]**

### 3.2 Column selection **[DEFAULT]**

- A column is charted if and only if its header **starts with** the exact, case-sensitive text `IMR_Field`. `IMR_Field_Sales`, `IMR_FieldA` and `IMR_Field` all match; `imr_field_x` and `Sales_IMR_Field` do not
- Header text is compared after stripping leading/trailing whitespace only
- All other columns are ignored entirely (they may contain anything)
- Charted columns are processed and displayed in file column order
- Two IMR_Field columns with identical headers reject the file (V06) **[DEFAULT — post-interview]** — otherwise their downloads would collide
- A file with no matching column is rejected (V05)
- Each chart is titled with the full column name

### 3.3 Cell values **[DEFAULT]**

Every cell in a charted column must parse as a finite number. Rules:

- Leading/trailing whitespace is stripped first
- Accepted: optional sign, digits, optional decimal point, optional exponent — i.e. the pattern `^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$`, then Python `float()`
- Rejected: empty cells, thousands separators (`1,234`), currency or percent symbols, text, and the words `nan`, `inf`, `infinity` in any casing (Python's `float()` would accept these; the regex above excludes them deliberately) **[post-interview]**
- Values may be negative or zero
- Any rejected cell rejects the **whole file** (V08) **[CONFIRMED]**. Skipping cells was rejected because it would break the meaning of "consecutive" in the rules and create gaps in the moving range

Consequence: because blanks are not allowed, every charted column has the same number of points, N = number of data rows.

### 3.4 Sequence and numbering **[CONFIRMED]**

- Row order is the time order; no sorting
- Points are numbered 1 to N from the first data row (spreadsheet row 2 = point 1)
- The x-axis shows point numbers only; there is no label or date column

### 3.5 Scale **[CONFIRMED: 30–100 points per column]**

Implementation may assume: at most a few hundred points per column, any number of columns, everything held in memory, synchronous processing. Charts must remain readable at 100 points (§6.2 width rule).

### 3.6 Data classification **[DEFAULT]**

Personal working data, no personal data expected. Nothing is written to disk by the server; the uploaded file is held in memory for the duration of the request and the derived results are kept in memory until the next upload. No logging of content.

---

## 4. Calculations

All arithmetic in full floating-point precision. Rounding to 3 decimal places happens only at display time (§4.5).

### 4.1 Moving ranges **[CONFIRMED]**

- `MR_i = |x_i − x_{i−1}|` for i = 2 … N. There are N − 1 moving ranges
- **Numbering is aligned with the Individuals chart**: the gap between points 16 and 17 is MR point **17**. The MR series therefore carries point numbers 2 … N and shares the x-axis with the I chart. There is no MR point 1
- `MR̄ = (Σ MR_i) / (N − 1)` — the average moving range. Both charts' sigma comes from this one number

### 4.2 Individuals chart statistics **[CONFIRMED v1.1 — Appendix B, D1 reversed]**

For a column with values `x_1 … x_N`:

- `mean_I = (Σ x_i) / N`
- `σ_I = MR̄ / 1.128` — the standard IMR sigma estimate (1.128 is the SPC constant d2 for moving ranges of two points)
- Lines: `L_I(k) = mean_I + k × σ_I` for k = −3, −2, −1, 0, +1, +2, +3
- The ±3 SD lines therefore sit at `mean_I ± 2.6596 × MR̄`, the textbook "mean ± 2.66 × MR̄" limits computed without the rounded shortcut

### 4.3 Moving Range chart statistics **[CONFIRMED v1.1 — Appendix B, D2 reversed]**

- Centre line: `MR̄`
- `σ_MR = 0.7557 × MR̄` — the standard sigma of a moving range (0.7557 = d3 ÷ d2 = 0.8525 ÷ 1.128)
- Lines: `L_MR(k) = MR̄ + k × σ_MR`, same seven k values
- The +3 SD line is therefore `3.2671 × MR̄`, the textbook upper limit `D4 × MR̄ = 3.267 × MR̄` to four significant figures. The −1 SD line is `0.2443 × MR̄` (always above zero); the −2 SD and −3 SD lines are always below zero
- Any line whose value is below zero is **computed and used in the arithmetic** but **not drawn** and marked "(below 0, not drawn)" in the summary table **[DEFAULT]**. A moving range cannot be negative, so no point can ever lie beyond such a line; the rule engine needs no special case

### 4.4 Constants

| Constant | Name in code | Use | Status |
|---|---|---|---|
| 1.128 | `D2_CONSTANT` | `σ_I = MR̄ / D2_CONSTANT` | **Required** |
| 0.7557 | `MR_SIGMA_FACTOR` | `σ_MR = MR_SIGMA_FACTOR × MR̄` | **Required** |
| 2.66 | — | Rounded shortcut for `3 ÷ 1.128`; limits must be computed from `D2_CONSTANT` instead | Must not appear |
| 3.267 | — | Rounded shortcut for `1 + 3 × 0.7557`; limits must be computed from `MR_SIGMA_FACTOR` instead | Must not appear |

Each required constant is defined **once**, as a named constant in the constants section (§9.2), and referenced by name everywhere else — including in any text that displays it. The plain sample standard deviation (`statistics.stdev`, `statistics.pstdev`, `statistics.variance`) is never used to compute lines. Encode this in `CLAUDE.md` (§13.3) so it survives across build sessions.

Consequence to know: displayed limits match Minitab/JMP to the precision of these tabulated constants; on large-valued data the third decimal may differ from a calculation that uses the rounded 2.66 or 3.267 shortcuts.

### 4.5 Rounding and display **[DEFAULT]**

- All displayed numbers: 3 decimal places, fixed (`42.300`, not `42.3`)
- All comparisons in the rule engine use unrounded values
- Negative numbers and the line names (`-1 SD`, `-2 SD`, `-3 SD`) use the ordinary hyphen-minus everywhere — page, chart labels, descriptions and CSV — so text copied into Excel stays numeric **[DEFAULT — v1.1]**. The em dash after "Rule N" and the en dash in point spans in the §5.5 sentences are punctuation, not signs, and are kept

### 4.6 Degenerate cases

| Case | Handling | Tag |
|---|---|---|
| Fewer than 3 data rows | File rejected (V09). The interview agreed a minimum of 2. v1.0 raised it to **3** because the plain-SD MR chart could not be computed from one moving range; under the v1.1 method 2 rows would compute, but the MR chart would be a single point on which no rule can fire. Kept at 3; the owner may restore 2 with a one-constant change | **[DEFAULT — post-interview, changes an interview answer; reason revised in v1.1]** |
| `MR̄ = 0` (every value in the column identical) | That column is rejected with a message in its section; other columns proceed (V10). Both sigmas are zero, the zones collapse onto the centre line and every zone test becomes meaningless. Under the moving-range method this is the **only** way a sigma can be zero | **[DEFAULT]** |
| Every gap identical (e.g. a perfectly straight line) | Charted normally in v1.1 (MR̄ > 0). v1.0 rejected it as V11; that code is retired | **[v1.1]** |
| Fewer than 20 points | Warning shown above the column's charts; processing continues (W01) | **[CONFIRMED]** |

---

## 5. Nelson rule detection

### 5.1 Common definitions

The rule engine operates on a **series**: a list of point numbers `p_1 … p_n`, values `v_1 … v_n`, and a set of lines `L(k)`. For the I chart, `p_i = i` and `n = N`; for the MR chart, `p_i = i + 1` and `n = N − 1`. The rule engine does not know or care which chart it is running on.

**Consecutive** means adjacent positions in the series (`i`, `i + 1`). Because blanks are rejected there are never gaps.

**Comparisons are strict, and a point exactly on a line belongs to neither side.** **[CONFIRMED (ties) + DEFAULT #5 (on-line points)]**

Define, for point i and line index k:

| Predicate | True when |
|---|---|
| `on_line(i, k)` | `abs(v_i − L(k)) ≤ 1e-9 × max(1, abs(L(k)))` — floating-point tolerance for "exactly on the line" **[DEFAULT — post-interview]** |
| `above_mean(i)` | `v_i > L(0)` and not `on_line(i, 0)` |
| `below_mean(i)` | `v_i < L(0)` and not `on_line(i, 0)` |
| `beyond_above(i, k)` for k = 1, 2, 3 | `v_i > L(+k)` and not `on_line(i, +k)` |
| `beyond_below(i, k)` for k = 1, 2, 3 | `v_i < L(−k)` and not `on_line(i, −k)` |
| `within_1(i)` | `L(−1) < v_i < L(+1)` and not on either line |
| `outside_1(i)` | `beyond_above(i, 1)` or `beyond_below(i, 1)` |
| `diff_i` for i = 1 … n − 1 | sign of `(v_{i+1} − v_i)`: `+`, `−`, or `0` when the two values are exactly equal (same tolerance rule as `on_line`, comparing the two values) |

Note the deliberate consequence: a point on the +1 SD line is neither `within_1` nor `outside_1`, so it breaks both a Rule 7 run and a Rule 8 run. A point on the mean is on neither side, so it breaks a Rule 2 run. Equal consecutive values break Rule 3 and Rule 4 runs.

### 5.2 Rule table **[CONFIRMED: all eight, standard Nelson thresholds, fixed]**

| Rule | Name (as shown to the user) | Threshold | Kind | Points marked and listed |
|---|---|---|---|---|
| 1 | One point beyond 3 SD | 1 point | Single point | That point |
| 2 | Nine or more points on one side of the mean | ≥ 9 consecutive | Run | Every point in the full run |
| 3 | Six or more points steadily rising or falling | ≥ 6 consecutive | Run | Every point in the full run |
| 4 | Fourteen or more points alternating up and down | ≥ 14 consecutive | Run | Every point in the full run |
| 5 | Two of three points beyond 2 SD (same side) | ≥ 2 of any 3 consecutive | Window | Only the out-of-zone points; window span noted |
| 6 | Four of five points beyond 1 SD (same side) | ≥ 4 of any 5 consecutive | Window | Only the out-of-zone points; window span noted |
| 7 | Fifteen or more points within 1 SD of the mean | ≥ 15 consecutive | Run | Every point in the full run |
| 8 | Eight or more points beyond 1 SD, either side | ≥ 8 consecutive | Run | Every point in the full run |

Thresholds are constants at the top of the source file, named (`RULE_2_MIN_RUN = 9` etc.) so a future change is one edit. They are not exposed in the interface.

### 5.3 Run-type rules — how an entry is formed **[CONFIRMED — Q6]**

For Rules 2, 3, 4, 7, 8: find every **maximal** run (a run that cannot be extended in either direction). Each maximal run whose length meets the threshold becomes **exactly one** observation covering **all** its points. A 12-point run against a 9-point threshold is one entry listing all 12 points, not four overlapping entries and not the last four points only.

### 5.4 Window-type rules — how an entry is formed **[CONFIRMED — Q7]**

For Rules 5 and 6, evaluated separately for the *above* side and the *below* side:

1. Compute `flag_i = beyond_above(i, k)` (or `beyond_below`) for every point, with k = 2 (Rule 5) or k = 1 (Rule 6)
2. Slide a window of width w (3 for Rule 5, 5 for Rule 6) over positions `i … i + w − 1`. The window **qualifies** if the number of flagged points in it is ≥ the threshold count (2 or 4). Note that 3 of 3 and 5 of 5 also qualify
3. Merge qualifying windows (same side) that **share at least one point** into one span `[first, last]`. Windows that are adjacent but share no point stay separate
4. One observation per merged span. **Marked and listed points are only the flagged points inside the span**; the span itself is reported as the window (e.g. "window 7–9"). Unflagged points inside the span are neither marked nor listed **[DEFAULT — the merged span is the union of the qualifying windows, so it may extend one or more points past the last flagged point]**

### 5.5 Rule-by-rule algorithms

Each rule is a pure function `rule_k(series, lines) → list[Observation]`. In these templates every minus sign is the plain hyphen-minus (§4.5); the em dash after "Rule N" and the en dash in `{a}–{b}` are kept exactly. Text templates use `{pt}` for a point number, `{val}` for a displayed value, `{a}–{b}` for a span, and `{list}` for a comma-separated list of `pt=val` pairs (e.g. `14=3.100, 15=2.900`).

**Rule 1.** For every i with `beyond_above(i, 3)` → one observation, direction `above`, line `+3 SD`. For every i with `beyond_below(i, 3)` → one observation, direction `below`, line `-3 SD`. Consecutive out-of-limit points are separate observations (Rule 1 is not a run rule).
> Rule 1 — One point beyond 3 SD: point {pt} (value {val}) is {above|below} the {+3|-3} SD line ({line value}).

**Rule 2.** Assign each point a side: `A` if `above_mean`, `B` if `below_mean`, `–` otherwise. Maximal runs of identical `A` or `B`. Length ≥ 9 → observation, direction `above` / `below`.
> Rule 2 — Nine or more points on one side of the mean: {len} consecutive points {above|below} the mean ({mean value}), points {a}–{b}. Values: {list}.

**Rule 3.** Over `diff_1 … diff_{n-1}`, find maximal runs of `+` and maximal runs of `-`. A run of m consecutive `+` differences spans m + 1 points. Points ≥ 6 → observation, direction `rising` / `falling`. A `0` difference terminates a run. A peak or valley point can belong to both a rising and a falling observation.
> Rule 3 — Six or more points steadily {rising|falling}: {len} consecutive points, {a}–{b}. Values: {list}.

**Rule 4.** Over the differences, find maximal segments where every adjacent pair `(diff_i, diff_{i+1})` has opposite non-zero signs. A segment of m differences spans m + 1 points. Points ≥ 14 → observation, direction `alternating`. A `0` difference terminates a segment.
> Rule 4 — Fourteen or more points alternating up and down: {len} consecutive points, {a}–{b}. Values: {list}.

**Rule 5.** §5.4 with k = 2, w = 3, count ≥ 2, both sides independently.
> Rule 5 — Two of three points beyond 2 SD: points {list of flagged pts} (values {vals}) are {above|below} the {+2|-2} SD line ({line value}); window {a}–{b}.

**Rule 6.** §5.4 with k = 1, w = 5, count ≥ 4, both sides independently.
> Rule 6 — Four of five points beyond 1 SD: points {list of flagged pts} (values {vals}) are {above|below} the {+1|-1} SD line ({line value}); window {a}–{b}.

**Rule 7.** Maximal runs of `within_1`. Length ≥ 15 → observation, direction `within`.
> Rule 7 — Fifteen or more points within 1 SD of the mean: {len} consecutive points, {a}–{b}, all between the -1 SD line ({L(-1)}) and the +1 SD line ({L(+1)}). Values: {list}.

**Rule 8.** Maximal runs of `outside_1`. Length ≥ 8 → observation, direction `either`, with counts of points above and below.
> Rule 8 — Eight or more points beyond 1 SD on either side: {len} consecutive points, {a}–{b}, none within 1 SD ({n_above} above, {n_below} below). Values: {list}.

### 5.6 Application to both charts **[CONFIRMED — Appendix B, D3]**

All eight rules run on the I series and, separately, on the MR series with the MR chart's own centre (MR̄), sigma and lines (§4.3). Thresholds are identical. On the MR chart the −2 SD and −3 SD lines are always below zero, so the *below* variants of Rules 1 and 5 can never fire there; the −1 SD line (0.2443 × MR̄) is above zero, so Rule 6 *below* and the below side of Rule 8 can. The engine needs no special handling for any of this.

### 5.7 Points in more than one pattern **[DEFAULT #7]**

A point is drawn once (red triangle) regardless of how many rules caught it, and appears in the list under every rule that caught it. Every observation states its direction.

### 5.8 Ordering of observations **[DEFAULT]**

Under each chart, and in the CSV: by rule number ascending, then by first point ascending. In the CSV, columns are in file order and the I chart precedes the MR chart within a column.

### 5.9 Worked examples (also the basis of the unit tests, §12.3)

The rule functions take the lines as an input, so tests can supply `mean = 0, SD = 1` and write values directly in SD units. In these examples `L(k) = k`. Each row lists the **complete** set of observations the engine must produce — including rules that also fire because, with the lines supplied, large values sit several SDs from the mean. v1.1 corrected E4, E5 and E14, which in v1.0 listed only the rule being illustrated.

| # | Series (values, mean 0, SD 1) | Expected observations |
|---|---|---|
| E1 | `0, 0, 3.5` | Rule 1: point 3 above +3 SD. Nothing else (Rule 5 window 1–3 has only one flagged point) |
| E2 | `0.5 × 12` (twelve 0.5s) | Rule 2: one entry, points 1–12, above. **Not** four entries |
| E3 | `0.5 × 5, 0, 0.5 × 5` | Nothing — the point on the mean splits the run into two runs of 5 |
| E4 | `1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1` (13 points) | Thirteen observations. Rule 1 above at each of points 4, 5, 6, 7, 8, 9, 10 (seven separate entries); Rule 2 above, points 1–13; Rule 3 rising 1–7 and Rule 3 falling 7–13 (point 7 in both); Rule 5 above, points 3–11, window 2–12; Rule 6 above, points 2–12, window 1–13; Rule 8, points 2–12 (11 above, 0 below) |
| E5 | `1, 2, 3, 3, 4, 5, 6, 7` | No Rule 3 entry: the tie at positions 3–4 splits the sequence into a 3-point run (1–3) and a 5-point run (4–8). No Rule 2 either (8 points < 9), and no Rule 8 (point 1 is exactly on the +1 SD line, leaving a 7-point run). Six observations: Rule 1 above at points 5, 6, 7, 8; Rule 5 above, points 3–8, window 2–8; Rule 6 above, points 2–8, window 1–8 |
| E6 | `0.5, -0.5` repeated 7 times (14 points) | Rule 4: points 1–14. Rule 7 does **not** fire (14 < 15) |
| E7 | E6 plus one more `0.5` (15 points) | Rule 4: points 1–15 **and** Rule 7: points 1–15. Multi-rule example |
| E8 | `1.5, -1.5` repeated 4 times (8 points) | Rule 8: points 1–8, 4 above, 4 below. Rule 4 does not fire (8 < 14) |
| E9 | `1, -1` repeated 7 times | Rule 4: points 1–14. Rule 8 does **not** fire: every value is exactly on a ±1 SD line, so no point is `outside_1` |
| E10 | `2.5, 0, 2.5` | Rule 5: points 1, 3 above +2 SD, window 1–3 |
| E11 | `2.5, 0, 2.5, 2.5, 0, 0` | Rule 5: one entry, points 1, 3, 4 above, window 1–5 (windows 1–3, 2–4, 3–5 qualify and overlap; 4–6 does not). Point 5 is inside the span but not listed |
| E12 | `1.5, 1.5, 0, 1.5, 1.5` | Rule 6: points 1, 2, 4, 5 above +1 SD, window 1–5 |
| E13 | `0.5, -0.5` repeated 8 times (16 points) | Rule 7: points 1–16. Rule 4 also fires (16 ≥ 14) |
| E14 | `0.5 × 7, 1.0, 0.5 × 7` (15 points) | Rule 7 does **not** fire: the point exactly on +1 SD breaks the run into two 7-point runs. Rule 2 does fire: all 15 points are above the mean, points 1–15 |

---

## 6. Output — page, charts, tables, downloads

### 6.1 Results page layout **[DEFAULT #9]**

Top of page: the upload form (always present so the next file can be uploaded), then, when results exist, a results header showing the source filename, the analysis timestamp, and two download links (report HTML, observations CSV).

Then one **section per column**, in file column order:

```
Heading: column name
[Warning box, if N < 20]           — or —   [Rejection box, if the column was rejected (V10)]
Individuals chart image             [download PNG]
Summary table (I)
Observations (I)
Moving Range chart image            [download PNG]
Summary table (MR)
Observations (MR)
```

Charts wider than the viewport sit inside a horizontally scrolling container.

### 6.2 Chart rendering **[CONFIRMED styling; DEFAULT sizing]**

Applies to both charts unless stated.

| Element | Specification |
|---|---|
| Data points (not in any pattern) | Black filled circle, prominent ("bold"): matplotlib marker `o`, size 6 |
| Data points in one or more patterns | Red filled triangle: marker `^`, size 8, drawn **instead of** the circle |
| Connecting line | Thin solid black line through all points in order (drawn beneath the markers) |
| Point numbers | Every point carries its number as a small text label just above the marker **[CONFIRMED: all points numbered]** |
| Mean line | Black, dotted |
| +1 SD and −1 SD lines | Red, dotted |
| +2 SD and −2 SD lines | Red, dotted |
| +3 SD and −3 SD lines | Red, solid |
| Line labels | At the right-hand end of each drawn line: `Mean` (the centre line on both charts), `+1 SD`, `+2 SD`, `+3 SD`, `-1 SD`, `-2 SD`, `-3 SD`, with an ordinary hyphen **[DEFAULT]** |
| Lines below zero (MR chart only) | Not drawn (§4.3) |
| Title | `{column name} — Individuals (I) chart` / `{column name} — Moving Range (MR) chart` |
| Axes | x: "Point number"; y: "Value" (I) / "Moving range" (MR) |
| x-axis range | 0.5 to N + 0.5 on **both** charts, so they align vertically. The MR chart has no point at x = 1 |
| x-axis ticks | Every point when N ≤ 50, otherwise every 5th (1, 5, 10, 15 …) **[DEFAULT — post-interview]** |
| y-axis range | Automatic, with margin, always including every drawn line and every point. MR chart lower bound 0 **[DEFAULT — post-interview]** |
| Figure size | Width in inches = `max(10, 0.2 × N)`; height 4.5 inches; 100 dpi. At N = 100 this is 2000 × 450 pixels **[DEFAULT]** |
| Legend | Small legend: circle = data point, triangle = Nelson pattern point **[DEV — optional]** |
| Format | PNG, rendered with matplotlib's Agg (non-GUI) backend |

### 6.3 Summary table **[CONFIRMED: n, mean, SD and all seven lines; v1.1 adds MR̄ and the sigma formula]**

| Row label | I chart | MR chart |
|---|---|---|
| Points | N | N − 1 |
| Mean | mean_I | MR̄ (the MR chart's centre) |
| Average moving range (MR-bar) | MR̄ | MR̄ |
| Sigma | σ_I, labelled `Sigma (MR-bar / 1.128)` | σ_MR, labelled `Sigma (0.7557 x MR-bar)` |
| +3 SD | L(+3) | L(+3) |
| +2 SD | L(+2) | L(+2) |
| +1 SD | L(+1) | L(+1) |
| -1 SD | L(−1) | L(−1), suffixed "(below 0, not drawn)" when negative |
| -2 SD | L(−2) | same (always negative on the MR chart) |
| -3 SD | L(−3) | same (always negative on the MR chart) |
| Patterns detected | count of observations | count of observations |

All values to 3 decimal places. On the MR chart the Mean and MR-bar rows show the same number by definition; both are kept so the two tables read the same way. The sigma labels are built from the named constants (§4.4), not typed as text.

### 6.4 Observations block **[CONFIRMED: rule, chart, direction, points, values, and the line crossed or window used]**

- Heading `Nelson patterns detected (I chart)` / `(MR chart)`
- One entry per observation, in §5.8 order, using the §5.5 templates verbatim
- When there are none: the single line **`No Nelson patterns detected.`** **[DEFAULT #8]**

### 6.5 Warnings **[CONFIRMED]**

When N < 20, each column shows, above its I chart:
> Only N points. Control limits based on fewer than 20 points are unreliable; treat every pattern below as indicative.

The warning is repeated in the downloadable report. It does not appear in the observations CSV.

### 6.6 Downloads **[CONFIRMED: all three]**

| Download | Content | Filename |
|---|---|---|
| Report | The complete results section (all columns) as a single standalone HTML file: inline CSS, charts embedded as base64 PNG, no external assets, no upload form, no download links. Title carries the source filename and timestamp | `{stem}_IMR_report.html` |
| Chart PNG | The exact image shown on the page | `{stem}_{column}_I.png` / `{stem}_{column}_MR.png` |
| Observations | All observations for all columns, both charts, schema in §6.7. UTF-8, comma-delimited, header row | `{stem}_observations.csv` |

`{stem}` = the uploaded filename without extension; `{column}` = the column name. Both are sanitised by replacing every character outside `A–Z a–z 0–9 _ -` with `_` **[DEFAULT — post-interview]**.

Report and CSV are generated at analysis time and held in memory alongside the page results, so a download never recomputes anything **[DEFAULT]**.

### 6.7 Observations CSV schema **[DEFAULT #13]**

| Column | Content | Example |
|---|---|---|
| `field` | Column name as in the file | `IMR_Field_Sales` |
| `chart` | `I` or `MR` | `I` |
| `rule_no` | 1–8 | `5` |
| `rule_name` | Name from §5.2 | `Two of three points beyond 2 SD (same side)` |
| `direction` | `above`, `below`, `rising`, `falling`, `alternating`, `within`, `either` | `above` |
| `points` | Contiguous run as `a-b`; otherwise comma-separated point numbers; single point as-is | `14-25` · `7,9` · `17` |
| `values` | Values of the listed points, semicolon-separated, 3 dp, in point order | `41.100;40.800` |
| `line_or_window` | Rule 1: `+3 SD=39.800`. Rule 2: `mean=…`. Rules 3, 4: empty. Rules 5, 6: `+2 SD=39.000; window 7-9`. Rules 7, 8: `-1 SD=…; +1 SD=…` | `+2 SD=39.000; window 7-9` |
| `description` | The full sentence shown on the page | — |

Fields are quoted where needed per RFC 4180 (Python's `csv` module default). The bundled answer key (§11) uses this same schema.

---

## 7. Validation and error handling

### 7.1 Validation rules, in the order they are checked

Severity: **F** = whole upload rejected, nothing analysed; **C** = that column rejected, others analysed; **W** = warning, processing continues.

| Code | Condition | Sev | Message (what happened · where · what to do) |
|---|---|---|---|
| V01 | No file in the request | F | No file was selected. Choose a `.csv` file and click Analyze. |
| V02 | Extension is not `.csv` | F | `{name}` is not a `.csv` file. Only comma-separated `.csv` files are accepted. |
| V03 | Upload exceeds 10 MB | F | `{name}` is larger than 10 MB. This tool is built for files of a few hundred rows. |
| V04 | Bytes are not valid UTF-8 (after removing a BOM) | F | `{name}` could not be read as UTF-8 text. Re-save it from Excel as "CSV UTF-8" and try again. |
| V05 | Header row missing, or no header starts with `IMR_Field` | F | No column starting with `IMR_Field` was found. Columns present: `{list}`. Rename the columns to chart so they start with `IMR_Field`. |
| V06 | Two or more IMR_Field headers are identical | F | Column name `{name}` appears more than once. Make every `IMR_Field` column name unique. |
| V07 | A data row has a different cell count from the header | F | Row `{r}` has `{k}` cells but the header has `{h}`. Fix the row (a stray comma or a missing value is the usual cause). *Lists every offending row, up to 20, then "… and {m} more"* **[v1.1]** |
| V08 | A cell in an IMR_Field column is blank or not a finite number (§3.3) | F | Column `{name}`, row `{r}` (point `{p}`) contains `"{text}"`, which is not a number. Every cell in an `IMR_Field` column must be a plain number. *Lists every offending cell, up to 20, then "… and {m} more".* |
| V09 | Fewer than 3 data rows | F | Only `{n}` data rows found; at least 3 are needed. Add more rows — 20 or more gives reliable limits. *(The 3 is built from the minimum-rows constant, not typed, so the minimum is a one-constant change.)* |
| V10 | `MR̄ = 0` (every value identical) | C | All `{n}` values in `{name}` are identical (`{value}`), so there is no variation to chart and no limits can be drawn for this column. |
| V11 | *Retired in v1.1* | — | Cannot occur under the moving-range method (a zero MR̄ means every value is identical, which is V10). The code is not reused |
| W01 | N < 20 | W | Text in §6.5 |

`{r}` is the spreadsheet row number (header = row 1, first data row = row 2), `{p}` the point number — both are given so the owner can find the cell in Excel and on the chart **[DEFAULT — post-interview]**.

All **F**-level checks that can be evaluated are run and **every** failure is listed together, so the owner fixes the file once, not one problem per upload. (V05–V08 can all be reported in one pass; V01–V04 each stop the pass, as nothing further can be checked.) **[DEFAULT]**

### 7.2 Message standard **[DEFAULT]**

Every user-facing message has three parts: what happened, where (column / row / point), and what to do about it. No stack traces, no Python exception names.

### 7.3 Presentation

- File-level rejection: the upload page re-renders with a red error box above the form listing all failures; HTTP status 400 **[DEV]**
- Column-level rejection: the column's section shows a red box in place of its charts, tables and observations; the column still appears in the report HTML with the same box; it contributes no rows to the observations CSV
- Download requested before any successful analysis: HTTP 404 with the message "Nothing has been analysed yet. Upload a file first."

### 7.4 Unexpected errors **[DEFAULT]**

Any uncaught exception during analysis returns a plain error page ("Something went wrong while analysing `{name}`. The details have been printed in the console window.") with HTTP 500, and the traceback is printed to the console the server was started from. Flask debug mode is **off**.

---

## 8. Non-functional requirements

| Area | Requirement |
|---|---|
| Binding | `127.0.0.1` only; never `0.0.0.0` |
| Network | No outbound calls of any kind; no CDN assets; the page must work with the machine offline |
| Persistence | None. No files written by the server, no database, no cookies beyond what Flask needs |
| Concurrency | Single user; one analysis at a time; the in-memory "last result" is simply overwritten |
| Browser | Any current Chromium-based browser (Edge/Chrome). No JavaScript required for core function |
| Platform | Windows 10/11, Python 3.11 |
| Performance | §2.3 budgets |
| Determinism | Same file → identical observations, tables and images every time (no randomness anywhere) |

---

# PART II — IMPLEMENTATION GUIDANCE

## 9. Architecture

### 9.1 Stack **[DEFAULT — mirrors the Pareto tool]**

| Layer | Choice | Notes |
|---|---|---|
| Runtime | Python 3.11 | Windows |
| Web | Flask | Server-rendered HTML; templates held as strings inside the file |
| Charts | matplotlib, `Agg` backend | Set the backend before importing `pyplot` |
| CSV, stats | Standard library: `csv`, `statistics`, `io`, `base64`, `re`, `dataclasses`, `webbrowser`, `threading` | No pandas. numpy is present only as matplotlib's dependency and is not imported directly |
| Tests | pytest + Flask's test client | |
| Dependencies file | `requirements.txt`: `flask`, `matplotlib`, `pytest`, pinned to the versions used in the build **[DEV]** |

### 9.2 Single-file constraint **[CONFIRMED]**

The application is one file, `imr.py`. Tests, sample data and documentation are separate files. Inside `imr.py`, keep these sections in this order, each behind a banner comment, so a build step can be scoped to one section:

```
1. Constants            — rule thresholds, tolerance, port range, figure sizing
2. Data classes         — §9.4
3. Parsing/validation   — bytes → ParsedFile or ValidationErrors (§7)
4. Statistics           — mean, moving ranges, MR̄, sigma, lines (§4)
5. Rule engine          — predicates, eight rule functions, detect_all (§5)
6. Rendering            — series → PNG bytes (§6.2)
7. Report/CSV builders  — AnalysisResult → HTML string, CSV string (§6.6, §6.7);
                           then, under a sub-banner "7.3 Analysis pipeline", the
                           function that joins sections 3–7 (Flask-free) [DEV — v1.1]
8. Flask app and routes — §9.3
9. Entry point          — start server, open browser (§9.5)
```

Sections 3–7 must have **no dependency on Flask** so they are directly unit-testable.

### 9.3 Routes **[DEFAULT]**

| Method, path | Behaviour |
|---|---|
| `GET /` | Upload page; if a result is in memory, also renders the results below the form |
| `POST /analyze` | Runs §7 validation, §4 statistics, §5 rules, §6 rendering; stores the `AnalysisResult` in a module-level variable (replacing any previous one); renders `/` |
| `GET /download/report` | `{stem}_IMR_report.html`, `text/html`, `Content-Disposition: attachment` |
| `GET /download/observations` | `{stem}_observations.csv`, `text/csv` |
| `GET /download/png/<int:column_index>/<chart>` | `chart` is `I` or `MR`; returns the stored PNG bytes, `image/png` |

### 9.4 Data model (Python dataclasses) **[DEV — names indicative]**

```python
@dataclass
class Observation:
    field: str; chart: str            # "I" | "MR"
    rule_no: int; rule_name: str; direction: str
    points: list[int]; values: list[float]
    span: tuple[int, int]             # first, last point of the run or merged window
    line_or_window: str; description: str

@dataclass
class ChartStats:
    n: int
    mean: float                       # centre line: mean_I, or MR̄ on the MR chart
    mr_bar: float                     # average moving range of the column (same on both charts)
    sigma: float                      # σ_I = mr_bar / D2_CONSTANT, or σ_MR = MR_SIGMA_FACTOR × mr_bar
    lines: dict[int, float]           # k → L(k), k in -3..3

@dataclass
class ChartResult:
    kind: str                         # "I" | "MR"
    point_numbers: list[int]; values: list[float]
    stats: ChartStats
    observations: list[Observation]
    pattern_points: set[int]          # union of Observation.points
    png: bytes

@dataclass
class ColumnResult:
    name: str; index: int; n: int
    warning: str | None               # W01 text
    rejected_reason: str | None       # V10 text; if set, the two charts are None
    individuals: ChartResult | None
    moving_range: ChartResult | None

@dataclass
class AnalysisResult:
    source_filename: str; stem: str; analysed_at: datetime
    columns: list[ColumnResult]
    report_html: str; observations_csv: str
```

### 9.5 Startup **[DEFAULT]**

`python imr.py`:
1. Try to bind `127.0.0.1:5000`; if busy, try 5001 … 5010; if all busy, print a message and exit
2. Start Flask (debug off, single-threaded is fine)
3. From a background thread, after ~1 second, open `http://127.0.0.1:{port}/` in the default browser via `webbrowser.open`
4. Print the URL to the console so it can be re-opened manually

### 9.6 Project structure

```
imr-chart-tool/
  imr.py                       — the application (single file)
  requirements.txt
  README.md                    — how to run, how to prepare a CSV, how to read the output
  CLAUDE.md                    — build guardrails (§13.3)
  SPEC.md                      — this document
  BLUEPRINT.md                 — numbered build prompts (to be produced next, Pareto pattern)
  todo.md                      — step checklist
  docs/
    answer_key_check.md        — the owner's Excel check sheet for §11.4
  sample/
    sample_imr.csv             — §11
    sample_answer_key.csv      — §11
  tests/
    conftest.py
    test_guardrails.py         — enforces §13.3 mechanically [v1.1]
    test_parsing.py
    test_stats.py
    test_rules.py
    test_render.py
    test_builders.py           — CSV and HTML builders [v1.1]
    test_pipeline.py           — the analysis pipeline, V10, W01 [v1.1]
    test_routes.py
    test_sample.py
```

---

## 10. Rendering notes **[DEV]**

- Create the figure with `plt.subplots(figsize=(width, 4.5), dpi=100)`; always `plt.close(fig)` after saving to avoid memory growth across uploads
- Draw order (z-order): lines (1) → connecting line (2) → circles (3) → triangles (4) → number labels (5)
- Number labels: `ax.annotate(str(p), (x, y), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=7)`
- Line labels: text at `x = N + 0.5` with `ha="left"`, `va="center"`, `fontsize=7`, clipped off; extend the right margin (`subplots_adjust`) so labels are visible
- Save with `fig.savefig(buf, format="png", bbox_inches="tight")` into a `BytesIO`; keep the bytes for both embedding (`base64`) and download
- Because both charts use the same x-range and figure width, they align when stacked

---

## 11. Sample dataset and answer key **[CONFIRMED]**

### 11.1 Files

- `sample/sample_imr.csv` — columns `IMR_Field_Rule1` … `IMR_Field_Rule8`, `IMR_Field_Clean`, and at least one non-IMR column (e.g. `Notes`) to prove ignored columns are ignored. 40 data rows **[DEFAULT]**
- `sample/sample_answer_key.csv` — every observation the tool must produce for the sample, in the §6.7 schema, in §5.8 order

### 11.2 Requirements

- Each `IMR_Field_RuleK` column must trigger Rule K on the **I chart** at least once
- `IMR_Field_Clean` must trigger **nothing** on either chart
- Incidental triggers (a Rule-1 spike will often also satisfy Rule 5; a strong pattern on the I chart usually produces something on the MR chart) are acceptable **provided they are in the answer key**
- The answer key is the complete, exact output — the end-to-end test (§12.8) compares the tool's CSV to it row for row

### 11.3 How to construct it **[DEV]**

Sigma comes from MR̄, which a level shift or a slow trend barely moves — but every sharp jump adds a large moving range. Build each column as a stable baseline of small noise plus an injected pattern, run the engine, and adjust the pattern's magnitude or length until the target rule fires. Two consequences of the moving-range method to design for: rapid up-down alternation creates large moving ranges and widens sigma, so Rule 8 is easier to trigger with *blocks* (several points well above, then several well below) than with alternation; and the moving ranges of plain noise are skewed, so their MR chart readily shows long runs below MR̄ — check the Clean column's MR chart in particular. Use fixed, hand-typed values — no random generation — so the file is reproducible.

### 11.4 Verification is the owner's job

An answer key produced by the engine and merely copied back only protects against *future regressions*; it cannot tell a wrong implementation from a right one. Before the key is committed, the owner (or the developer, by hand or in Excel) must independently confirm, for at least two columns, the mean, the moving ranges, MR̄, sigma, the seven lines, and the target rule's points. See Appendix C.1.

---

## 12. Testing plan **[DEFAULT — entire plan]**

Every test is pytest. Sections 3–7 of `imr.py` are tested without Flask; §12.7 uses Flask's test client.

### 12.1 Statistics (`test_stats.py`)

- Moving ranges: values equal `|x_i − x_{i−1}|`, count is N − 1, point numbers are 2 … N
- MR̄ equals the hand-computed mean of the moving ranges on several hand-picked series, including negative values and decimals
- I chart: centre is the plain mean; sigma equals MR̄ ÷ 1.128; the seven lines equal `mean + k × sigma`
- MR chart: centre is MR̄; sigma equals 0.7557 × MR̄; the +3 SD line is within 0.0002 × MR̄ of 3.267 × MR̄; the −2 and −3 SD lines are below zero and −1 SD is above zero
- Sigma is **not** the plain sample SD: on a series with a large level shift, σ_I is clearly smaller than `statistics.stdev` of the same values
- All-identical values give MR̄ = 0 and both sigmas exactly 0

### 12.2 Zone predicates (`test_rules.py`)

With `mean = 0, SD = 1`: a value of exactly `1.0` is neither `within_1` nor `outside_1`; `1.0 + 1e-12` is treated as on the line (tolerance); `1.0 + 1e-6` is `outside_1`; `0.0` is on neither side of the mean; a diff between equal values is `0`.

### 12.3 Rules (`test_rules.py`) — supply the lines directly (`mean = 0, SD = 1`)

For every rule:
- **Threshold positive**: exactly the threshold (9 for Rule 2, 6 for Rule 3, 14 for Rule 4, 2 of 3, 4 of 5, 15, 8) → one observation with the expected points, direction, span and description text
- **Threshold-minus-one negative**: one fewer → no observation
- **Over-length run** (Rules 2, 3, 4, 7, 8): threshold + 3 points → still exactly one observation covering all points
- **Both directions** (Rules 1, 2, 3, 5, 6): above and below / rising and falling produce correctly labelled observations
- **Tie / on-line breaks** (Rules 2, 3, 4, 7, 8): a tie or on-line point in the middle splits the run; assert no observation when both halves are under threshold
- **Window merging** (Rules 5, 6): overlapping qualifying windows merge into one span; only flagged points are listed; adjacent non-overlapping windows stay separate; `3 of 3` and `5 of 5` qualify
- **Description text** matches the §5.5 template exactly for one positive case per rule
- All fourteen worked examples E1–E14 from §5.9 are encoded as tests, asserting the complete set of observations (including the "also fires" cases)

### 12.4 Detect-all and multi-rule points

- `detect_all` returns observations in §5.8 order
- A point caught by two rules appears in both observations and once in `pattern_points`
- Running the engine on an MR series with point numbers 2 … N reports MR point numbers, not positions

### 12.5 Parsing and validation (`test_parsing.py`)

One test per code V02–V10 and W01 (V10 and W01 are raised by the analysis pipeline and may be tested in `test_pipeline.py`), each asserting the severity and that the message contains the column name / row number / point number as applicable. Additional cases: BOM present; `nan` and `1,234` rejected; ` 12.5 ` (padded) accepted; `-3.2e2` accepted; multiple bad cells all reported; more than 20 bad cells truncated with the "… and m more" suffix; non-IMR columns with garbage content are ignored; case-sensitive prefix (`imr_field_x` ignored).

### 12.6 Rendering (`test_render.py`)

- A PNG is produced for both charts (starts with the PNG signature, non-trivial size)
- Figure width follows the §6.2 formula — test the width helper directly, and that PNG pixel width grows with N. The exact pixel width is not asserted, because `bbox_inches="tight"` trims whitespace **[v1.1]**
- No exception when every point is a pattern point, or when no point is
- MR chart with all negative-k lines below zero renders without drawing them (assert via the summary table rather than the image)

### 12.7 Routes (`test_routes.py`)

- `GET /` → 200, contains the form
- `POST /analyze` with the sample → 200, page contains every `IMR_Field` heading, no rejection boxes, the report and observations links once, and an I and an MR PNG link for every non-rejected column
- `POST /analyze` with a bad file → 400, error box contains the expected message
- Each download route → correct status, content type, `Content-Disposition` filename per §6.6; PNG route for a rejected column → 404
- Downloads before any analysis → 404 with the §7.3 message
- A second upload replaces the first (heading of the first file's columns no longer present)

### 12.8 End-to-end (`test_sample.py`)

Run the full pipeline on `sample/sample_imr.csv`; the generated observations CSV must equal `sample/sample_answer_key.csv` exactly (compare as parsed rows, not bytes, to be line-ending tolerant). This is the acceptance test for the build.

### 12.9 Manual acceptance checklist (for the owner — no code reading required)

1. `python imr.py` opens the browser on the upload page
2. Upload `sample_imr.csv`: nine sections appear; `Notes` column is not charted
3. Every point on every chart carries a number; pattern points are red triangles, others black circles
4. Seven lines on the I chart in the specified colours/styles, labelled at the right
5. MR chart sits directly under the I chart with the same width, first point at 2
6. Under each chart: summary table, then observations (or "No Nelson patterns detected.")
7. `IMR_Field_Clean` shows no patterns on either chart
8. `IMR_Field_Rule5` observation lists only the out-of-zone points and names the window
9. For one column, recompute in Excel the mean, the moving ranges (`=ABS(B3-B2)` filled down), MR̄ (`=AVERAGE` of the moving ranges) and sigma (`=MR̄/1.128`) — they match the summary table to 3 dp
10. Upload a file with 15 rows: warning appears; charts still render
11. Upload a file with a blank cell: file rejected; message names the column, row and point
12. Download the report; open it with the machine's Wi-Fi off; charts and text are intact
13. Download a PNG; it is the same image as on the page
14. Download the observations CSV; open in Excel; columns match §6.7

---

## 13. Delivery

### 13.1 Single phase

Done when: all tests in §12.1–12.8 pass, the answer key has been independently verified (§11.4), and the §12.9 checklist passes.

### 13.2 Next artefact

`BLUEPRINT.md` — 22 standalone build prompts in the Pareto pattern (one prompt per `/step`, test-first, `git commit` after each green step) — plus `todo.md` and `CLAUDE.md`. Produced 26 September 2026 and aligned with this v1.1.

### 13.3 `CLAUDE.md` guardrails (non-negotiable across every build session)

1. The application is exactly one file, `imr.py`. Tests and data live outside it
2. Sigma comes only from the average moving range: `σ_I = MR̄ / D2_CONSTANT` and `σ_MR = MR_SIGMA_FACTOR × MR̄`, with `D2_CONSTANT = 1.128` and `MR_SIGMA_FACTOR = 0.7557`. Each constant is defined once and referenced by name; the rounded shortcuts 2.66 and 3.267 never appear; the plain sample SD is never used for lines (§4.4)
3. All eight Nelson rules run on both the I chart and the MR chart, standard thresholds, held as named constants
4. Comparisons are strict; a point exactly on a line (tolerance §5.1) belongs to neither side and breaks runs
5. MR points are numbered 2 … N, aligned with the I chart
6. Run rules produce one observation per maximal run; window rules list only out-of-zone points
7. No pandas, no direct numpy, no network access, no files written by the server
8. Sections 3–7 of `imr.py` never import Flask

---

# APPENDICES

## Appendix A — Defaults requiring review

Every item was assumed by the author, not confirmed. Items 1–14 were shown to the owner at the end of the interview (Q21) and not vetoed; items marked *(post-interview)* have not yet been seen.

**Input**
1. CSV: comma delimiter, UTF-8 (BOM tolerated), header row required
2. `IMR_Field` prefix match is exact and case-sensitive; other columns ignored; no match rejects the file
3. Numeric parsing rules (§3.3), including rejection of `nan`/`inf` and thousands separators *(post-interview detail)*
4. Ragged rows reject the file *(post-interview)*
5. Duplicate `IMR_Field` headers reject the file *(post-interview)*
6. 10 MB upload cap *(post-interview)*
7. **Minimum 3 data rows, not 2** *(post-interview; changes the Q11 answer)*. v1.1: the original reason (plain-SD MR chart needs two moving ranges) no longer applies; kept at 3 because a one-point MR chart can show nothing. Restoring 2 is a one-constant change

**Calculations and rules**
8. `MR̄ = 0` (all values identical) rejects the column, other columns proceed *(reworded in v1.1)*
9. ~~`SD_MR = 0` rejects the column~~ — retired in v1.1 (cannot occur separately from item 8)
10. Lower MR lines below zero are computed but not drawn
11. A point exactly on a line is neither beyond nor within; tolerance `1e-9 × max(1, |line|)` *(tolerance value post-interview)*
12. Merged window span may extend past the last flagged point (§5.4)
13. A point in several rules: one triangle, listed under each rule; every entry states direction
14. Observation ordering: rule number, then first point *(post-interview refinement of item 13's original wording)*

**Output**
15. Layout per column: I chart → table → observations → MR chart → table → observations; line labels at right edge; thin black connecting line
16. "No Nelson patterns detected." shown explicitly; warning shown above the I chart
17. 3 decimal places everywhere
18. Chart width `max(10, 0.2 × N)` inches; x ticks every point up to 50 then every 5th; MR y-axis floor at 0 *(tick and floor rules post-interview)*
19. Download filenames and sanitisation (§6.6); report excludes upload form and download links
20. Report and CSV built at analysis time, held in memory
21. Observations CSV schema (§6.7)

**Architecture**
22. Flask + matplotlib + standard library; no pandas
23. Route design (§9.3); in-memory single last result
24. Port 5000 with fallback to 5001–5010; browser auto-open
25. Error presentation and HTTP statuses (§7.3, §7.4); all file-level failures reported together
26. Sample dataset shape: 40 rows, one column per rule plus a clean column plus an ignored column
27. Entire testing plan (§12)
28. Deliverable format: this Markdown file, to become `SPEC.md` in the repository

**Added in v1.1**
29. Tabulated constants 1.128 and 0.7557, each held once as a named constant; limits may differ from the rounded 2.66 / 3.267 shortcuts in the last displayed decimal
30. Summary table shows MR̄ and a sigma row whose label states the formula
31. Hyphen-minus everywhere for negatives and line names (replaces v1.0's optional typographic minus on the page)
32. V07 lists at most 20 rows; blank lines after the last data row are ignored; a blank line between rows is V07

## Appendix B — Decisions against standard practice

Recorded so the trade-offs are visible to the implementer, not to relitigate.

### In force

| ID | Decision | Standard practice | Chosen | Consequence |
|---|---|---|---|---|
| D3 | Nelson rules on the MR chart | Rule 1 only (Minitab default; Rules 1–4 at most) | All eight rules, identical thresholds | Adjacent moving ranges share a data point and are therefore correlated, so the run and zone rules produce more false alarms on the MR chart than on the I chart |

**Rationale for D3** (owner, 26 Sep 2026, accepting the author's recommendation): the cost of running all eight rules on the MR chart is extra false alarms, not missed signals. The owner prefers to see every possible signal on both charts and judge it himself. MR-chart patterns from Rules 2–8 are read as "worth a look", not "act on it"; Rule 1 on the MR chart and every rule on the I chart are the ones to act on.

### Reversed in v1.1

| ID | v1.0 decision | Reversed to | Why |
|---|---|---|---|
| D1 | Plain sample SD (Excel `STDEV.S`) for the I chart | `σ_I = MR̄ / 1.128` (§4.2) | Special causes inflate the plain SD, widening every zone and making Rules 1, 5, 6, 7 and 8 **less** sensitive to exactly the signals the tool exists to find. The moving-range estimate is barely affected by a shift or trend, and matches Minitab, JMP and SPC texts, so results can be compared with any other IMR chart |
| D2 | Plain sample SD of the MR values for the MR chart | `σ_MR = 0.7557 × MR̄`, centred on MR̄ (§4.3) | Same sensitivity problem as D1; the standard factor reproduces the textbook 3.267 × MR̄ upper limit |

Owner decision, 26 September 2026, on the author's recommendation.

## Appendix C — Recommended work outside this build

**C.1 Verify the answer key by hand before it becomes the acceptance test.** §11.4. Recompute at least one column fully in Excel (mean, moving ranges, MR̄, sigma, seven lines, and the points that should trigger the target rule) and compare with the tool. Thirty minutes here is the only thing that makes "all tests pass" mean anything.

**C.2 D1–D3 rationale — done in v1.1.** D1 and D2 were reversed and D3's rationale is recorded in Appendix B. Nothing further needed.

**C.3 Candidate for a later version, not this build: a sigma-method switch.** If the owner ever needs to reproduce a colleague's spreadsheet that uses `STDEV.S` limits, the clean addition is a per-run choice between the moving-range sigma (default) and the plain SD, shown in the summary table. The structure in §9.2 (statistics isolated from rendering and rules) keeps this a small change.

**C.4 Keep the run-to-run discipline from the Pareto build.** One prompt per Claude Code session, `/clear` between steps, commit after each green step, and paste the AI's summary — not the code — back for a plain-language check.
