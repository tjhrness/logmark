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
