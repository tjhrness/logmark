# Answer key check (SPEC.md §11.4)

Before `sample/sample_answer_key.csv` becomes the acceptance test, check three charts by hand in Excel. Open `sample/sample_imr.csv`: row 1 holds the headers and rows 2–41 hold points 1–40, so **point p is on row p + 1**.

**The tool deliberately does NOT use Excel's STDEV.S.** Every line comes from the average moving range, the standard IMR method. If you type STDEV.S, your numbers will not match, and that is expected.

Compare to 3 decimal places. Use an empty column (L below) for the moving ranges.

---

## 1. IMR_Field_Rule5, Individuals chart (data in column E)

| What | Excel formula | Expected |
|---|---|---|
| Mean | `=AVERAGE(E2:E41)` | 50.258 |
| Moving ranges | `L3 =ABS(E3-E2)`, filled down to `L41` (row 3 = MR point 2) | 39 numbers |
| Average moving range | `=AVERAGE(L3:L41)` | 1.167 |
| Sigma | `=average moving range/1.128` | 1.034 |
| +3 SD | `=mean + 3*sigma` | 53.360 |
| +2 SD | `=mean + 2*sigma` | 52.326 |
| +1 SD | `=mean + 1*sigma` | 51.292 |
| Mean line | `=mean` | 50.258 |
| -1 SD | `=mean - 1*sigma` | 49.223 |
| -2 SD | `=mean - 2*sigma` | 48.189 |
| -3 SD | `=mean - 3*sigma` | 47.155 |

**Rule 5 (two of three points beyond 2 SD, same side).** Two points should trigger it:

| Point | Row | Value | Line crossed |
|---|---|---|---|
| 20 | 21 | 53.000 | above +2 SD (52.326) |
| 21 | 22 | 52.900 | above +2 SD (52.326) |

The tool reports this as one entry, points 20 and 21, with window 19–22. That is because two three-point windows each hold both points (19–21 and 20–22); they overlap, so they merge into one span, 19–22. Window 21–23 holds only point 21, so it does not count. Neither point is above +3 SD, so Rule 1 does not fire on this chart. No point is below -2 SD.

---

## 2. IMR_Field_Rule7, Individuals chart (data in column G)

Clear column L first, or use column M.

| What | Excel formula | Expected |
|---|---|---|
| Mean | `=AVERAGE(G2:G41)` | 50.095 |
| Moving ranges | `L3 =ABS(G3-G2)`, filled down to `L41` | 39 numbers |
| Average moving range | `=AVERAGE(L3:L41)` | 0.741 |
| Sigma | `=average moving range/1.128` | 0.657 |
| +3 SD | `=mean + 3*sigma` | 52.066 |
| +2 SD | `=mean + 2*sigma` | 51.409 |
| +1 SD | `=mean + 1*sigma` | 50.752 |
| Mean line | `=mean` | 50.095 |
| -1 SD | `=mean - 1*sigma` | 49.438 |
| -2 SD | `=mean - 2*sigma` | 48.781 |
| -3 SD | `=mean - 3*sigma` | 48.124 |

**Rule 7 (fifteen or more points in a row within 1 SD of the mean).** Points **12 to 28** (rows 13–29, 17 points in a row) are all strictly between the -1 SD line (49.438) and the +1 SD line (50.752):

| Points | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Value | 50.1 | 49.9 | 50.3 | 50.0 | 49.8 | 50.2 | 50.4 | 49.9 | 50.1 | 50.3 | 49.8 | 50.0 | 50.2 | 49.9 | 50.3 | 50.1 | 49.8 |

Point 11 (48.9) is below -1 SD and point 29 (51.0) is above +1 SD, so the run stops at both ends.

---

## 3. IMR_Field_Rule1, Moving Range chart (data in column A)

| What | Excel formula | Expected |
|---|---|---|
| Moving ranges | `L3 =ABS(A3-A2)`, filled down to `L41` | 39 numbers |
| Average moving range (the MR chart's centre) | `=AVERAGE(L3:L41)` | 1.321 |
| Sigma | `=0.7557*average moving range` | 0.998 |
| +3 SD | `=average + 3*sigma` | 4.314 |
| +2 SD | `=average + 2*sigma` | 3.316 |
| +1 SD | `=average + 1*sigma` | 2.318 |
| Centre line | `=average` | 1.321 |
| -1 SD | `=average - 1*sigma` | 0.323 |
| -2 SD | `=average - 2*sigma` | -0.675 (below 0, not drawn) |
| -3 SD | `=average - 3*sigma` | -1.673 (below 0, not drawn) |

The +3 SD line is about 3.267 × the average moving range, the textbook upper limit. The -2 and -3 SD lines are below zero; -1 SD is above zero.

Two moving ranges are above the +3 SD line (Rule 1): **MR point 20** (row 21, `=ABS(A21-A20)` = 7.400) and **MR point 21** (row 22, `=ABS(A22-A21)` = 4.900). Both come from the spike of 56.0 at point 20.

---

If every number matches to 3 decimals, commit the answer key (the command is in the Step 21 summary). If anything differs, do not commit; bring the difference back.
