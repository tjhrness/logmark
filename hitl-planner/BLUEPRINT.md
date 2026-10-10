# Implementation blueprint — HITL Sample Size Planner v1.0

## Objective and acceptance boundary

One AI system and one calendar month/ISO week at a time: plan statistically defensible SME review sample; predict review hours including independent re-review; compare with capacity; explore achievable precision and threshold certification; record reviewed issues and agreement after review; preserve immutable records and produce an offline printable report and cycle log. No conversation content is ingested. Source contract is **the PDF in `docs/`**, particularly §4 formulas, §11.1 answer key, §12 guardrails.

**Not an implementation:** This kit is a build plan and coding prompts. No executable planner or completed tests are represented here.

## 1. Architecture and data flow

```text
Windows Python 3.11 + Flask 127.0.0.1 only
  GET / -> embedded light HTML/CSS/plain JS 4-tab desktop app
  JS (150ms debounce) -> POST /api/calc or /api/actuals/calc
                              |
                    Python validation / pure calculator
                       F1-F10 / warnings / S1-S7
                              |
                    save endpoint -> immutable JSON
                                           |
                         +-----------------+-----------------+
                         |                                   |
                   report.html                          plans_log.csv
                   derived A4 page                       derived Excel log
                         |                                   |
                     History / Prefill / Actuals read saved JSON
```

- Source files: `hitl_planner.py` only runtime script; `test_hitl_planner.py` single pytest suite; `AGENTS.md`; README; config.json created on first run (ignored by Git).
- Dependencies: Flask runtime and pytest for development, everything else standard library. No CDNs, telemetry, remote fonts, npm, DB, or third-party statistics libraries.
- Workspace: `%USERPROFILE%\Documents\HITL Planner\`, configured, with folder per `<period label> - <sanitised system>`. Saved `plan_vN.json`, `actuals_vN.json` immutable; derived `report.html` per folder and `plans_log.csv` at workspace root.
- Calculations work independently of the web request; Flask endpoints validate, call pure services, and return JSON. All stats, formatting and warning conditions are computed in Python.
- Configure and launch: the port **5062 is provisional**, and must be verified against existing Pareto and IMR scripts before first release; restart behavior follows single-instance health probe; Quit cleanly stops server.

## 2. Statistical and methodological contract

- Exact Z values: 90%=1.645, 95%=1.960, 99%=2.576; `ceil_safe(x)=ceil(round(x,9))`; `fits(hours,capacity)` uses <= with tolerance 1e-9.
- F1 effective margin E = E_abs or relative r×p; F2 n0=Z²p(1-p)/E²; F3 n_cochran=ceil_safe(n0/(1+(n0-1)/N)); F4 n_assure=ceil_safe(ln(1-C)/ln(1-T)).
- F5 n=max(n_cochran,n_assure) when certify enabled AND assurance feasible (`n_assure<=N`); otherwise n=n_cochran. Assurance binds only when feasible and strictly larger. W7 warns if infeasible; saving still allowed.
- F6 DR=min(n,max(F,ceil_safe(s*n))); F7 reviews=n+DR; hours=reviews*M/60; capacity=S*H.
- F8 detection=1-(1-T)^n; F9 reverse margin Z√[p(1-p)/n ×(N-n)/(N-1)], zero at census; F10 inverse T_at=1-(1-C)^(1/n), n=0 n/a.
- n_max from monotonic search with **same** F6/F7 hours function; 3x3 grid recomputes same headline rule per cell; what-if slider does not mutate plan until "Adopt".
- W1–W7 for Plan and W8–W10 for Actuals, with exact strict boundaries; always S1–S7 ordered seven sentences.
- Actuals: reviewed, issues, agreement and notes; observed rate=issues/reviewed; interior achieved margin uses observed p; 0/all issues generate confidence *bounds* not margins. Observed p prefill floor 0.1%.

## 3. Domain and API contracts

### I1–I15 and type system

| Field | Constraint | Default |
|---|---|---|
| I1 period type | `month`/`week` | month; last plan for known system |
| I2 period | valid `YYYY-MM` or ISO `YYYY-Www` | current; never carried forward |
| I3 system | text 1–60 characters | blank |
| I4 population N | integer ≥1 | blank; never carried forward |
| I5 confidence | 0.90, 0.95, 0.99 | 0.95 |
| I6 margin mode | `absolute`/`relative` | absolute |
| I7 margin | absolute 0.005–0.25; relative 0.05–0.50 | absolute 0.05 |
| I8 expected issue rate p | 0.001–0.999 | 0.5; actuals or planned from saved system |
| I9 SMEs | integer ≥1 | blank (known system prior plan) |
| I10 hours/SME | decimal >0 | blank (known system prior plan) |
| I11 minutes/review | decimal >0 | blank (known system prior plan) |
| I12 DR share | 0–1 | 0.15 |
| I13 DR floor | integer ≥0 | 50 |
| I14 certify | bool | on |
| I15 threshold | 0.0001–0.50 | 0.01 |

Percent UI shows percent units, JSON/API stores decimal; refuse (never clamp) out-of-range, missing, nonnumeric.

### HTTP surface (15 routes total)

1. GET `/` single page, GET `/api/health` identifying running instance/workspace state.
2. POST `/api/calc` and POST `/api/actuals/calc` (pure calculations).
3. POST `/api/plans` and POST `/api/plans/<plan_id>/actuals` (immutable versioned saves).
4. GET `/api/plans` and GET `/api/plans/<plan_id>` (history/reload).
5. GET `/api/prefill?system=` and GET `/api/systems` (history prefill).
6. GET `/api/log/rebuild`, POST `/api/open-report`, POST `/api/open-folder`, GET `/api/method`, POST `/api/quit`.

**There are 15 distinct method/path endpoints** in specification §9.

### Persistence and retention

- On every save recalculate server side, create new `plan_vN.json` or `actuals_vN.json` with ISO local-offset timestamp and full tool, plan, inputs, output, warnings, method arithmetic and integrity provenance.
- Version = max existing version +1 at saving time. Atomic temp-write/replace for derived files and safe exclusive creation for immutable numbered files; prevent concurrent overwrite.
- Folder sanitizing and collision suffixes are exact §3.1 requirements; never infer system identity from sanitized folder.
- CSV rebuilt from JSON, UTF-8 BOM, 43 columns in fixed order; corrupt folders skipped with visible History error, never deleted.
- `report.html` self-contained, no scripts/external URLs, A4 print mode. Browser Print to PDF only.

## 4. Decomposition method (three granularity passes)

**Pass A — six product slices:** foundation → statistical core → explanation/validation → Plan UI → persistence/history/actuals → governance/release. Too coarse: large UI or persistence changes would hide math regressions.

**Pass B — independently testable services:** config+launcher; F1–F3; F4/F8–F10; F5–F7; capacity-max; sensitivity; warnings; statements; formatting; validation; calculation API; Plan presentation; plan saves/reports/history/prefill; actuals engine/routes/UI; CSV; Method/integrity; failures/release. Still too large around screens and user data.

**Pass C — final 36 commit-sized tasks:** separate input UI vs outputs vs slider vs sensitivity, separate atomic writes vs version save vs report, split actuals engine from preview from save from UI, and split integrity gate from recovery/concurrency and polish. All tasks include red tests + one integrated production path, and no stage assumes a new statistical algorithm. See `PROMPTS.md` and `todo.md`. Each Codex cloud task should produce a reviewable change set; the owner merges it before starting the next task.

## 5. Final 36 tasks / dependency order

01. **Repository bootstrap, config, and health** [Foundation]. Test proof: Red: root and health responses, config-created-on-first-run, config-preserved, corrupted/missing-key config exits 2, tmp workspace isolation, HTTP without outside resources. Spec §2.1–2.4, §8.1, §8.6, §9, §10 E7.
02. **Single-instance launcher and clean quit** [Foundation]. Test proof: Test correct occupied-port classification using monkeypatched health/probes and a temporary socket, correct host binding, clean shutdown in a real subprocess/local test, browser-opening mocked, and Ctrl-C path. Spec §2.3, §9, §10 E6.
03. **Cochran and finite-population core** [Statistics]. Test proof: Write failing tests first: K1 (N 1000000 C. Spec §4.1–4.3 F1–F3, §4.8, §11.1 K1–K3/K6, §11.2.
04. **Assurance, detection, and reverse maths** [Statistics]. Test proof: Red-first K4:. Spec §4.3 F4/F8/F9/F10, §4.8, §11.1 K4/K5/K7/K8/K11.
05. **Headline, review counts, and capacity** [Statistics]. Test proof: Red: binding cases assurance/cochran/tie/certify-off/W7 condition; K10 DR(40)=40 DR(400)=60 at s=. Spec §4.3 F5–F7, §4.8, §11.1 K10–K11, §11.2.
06. **Capacity-max trade-off engine** [Statistics]. Test proof: Red-first K9: N50000 S3 H8 M12 s. Spec §4.4, §4.8, §11.1 K9.
07. **Nine-cell sensitivity service** [Statistics]. Test proof: Red: always exactly nine cells in correct mode, 90/95/99 confidence, cell value matches independent main calculation at matching inputs, certify-off has no A, certify-on may bind, custom values highlight none, equality highlight works, correct ordered cells. Spec §4.5, §11.2.
08. **Plan warning rules W1–W7** [Interpretation]. Test proof: Write boundary tests inside/outside for all seven, including W1=. Spec §5, §4.8, §11.2.
09. **Seven reportable statements** [Interpretation]. Test proof: Red: always seven, one S1 per margin mode, three S2 variants, S3 threshold and power inserted correctly, S6 explicit random selection and N, correctly formatted month and ISO week, 0. Spec §6, §4.7, §11.2.
10. **Formatting and reproducible arithmetic** [Interpretation]. Test proof: Red: 0. Spec §4.7, §7.4, §8.2, §11.2.
11. **Input validation and system-period identity** [Integration]. Test proof: Red: both ends and just outside every numeric limit, invalid non-finite numbers, booleans masquerading as integers, invalid ISO week including week 53 where invalid, malformed month, blank fields and system length, missing dict keys, unknown fields safely handled, valid exact endpoints. Spec §3.1–3.3, §4.7, §10 E1, §11.2.
12. **Validated Plan API as a single source** [Integration]. Test proof: Red: Flask test client success with acceptance scenario N50000,p. Spec §9 POST /api/calc, §5, §6, §10.
13. **Plan screen forms and debounce** [Plan UI]. Test proof: Red/green via Flask page smoke tests for all I1–I15, no external script/style tags; static inspection of JS for debounce and no math formulas; manual keyboard entry verifies fields, toggles and disabled state; API tests unchanged. Spec §7, §7.1, §3.2–3.3.
14. **Plan headline, warnings, statements** [Plan UI]. Test proof: Test HTML container IDs and response mapping, Flask API acceptance numbers, W7 red and W1 advisory yellow, mutually exclusive binding copy, exactly seven statements in DOM when valid. Spec §7.1, §5–6, §4.7.
15. **Live capacity what-if and Adopt** [Plan UI]. Test proof: Tests of unchanged form value while moving slider, adopted value on click, relative/absolute endpoints, inability to go below n_assure with certify on, K9 read-out and §11. Spec §4.4, §7.1, §11.6 items 2–4.
16. **Sensitivity and assurance UI** [Plan UI]. Test proof: Test nine visible cells and 90/95/99 headings, relative mode labels, custom-margin no highlight, a binding cell shows A, W7 assurance is red, detection power shown even when certify off; API tests compare one cell to direct calculation. Spec §4.5, §7.1.
17. **Atomic file writes and safe names** [Persistence]. Test proof: Red: sanitized `A/B: "C" -> AB C`, `CON -> CON_`, empty invalid, control chars, collision `(2)`, `. Spec §3.1, §8.1, §8.7, §10 E3/E5, §11.3.
18. **Immutable plan saves and versions** [Persistence]. Test proof: Red: two saves create v1 and v2; v1 hash/bytes remain identical; reload object matches `/api/calc` outputs; W7 allowed to save; timestamps offset-aware; two browser requests cannot silently overwrite each other; bad inputs 400; save does not depend on browser-calculated output. Spec §3.1, §8.2, §8.7, §9, §11.3.
19. **Stand-alone printable HTML report** [Persistence]. Test proof: Test report exists after save; contains plan ID and all seven exact strings, no `<script`, no `http://` or `https://`, usable `<style>` print rules, input containing `<>&` safely escaped, saving v2 reflects newest version. Spec §8.4, §6–7, §11.3.
20. **Plan save workflow and open actions** [Plan UI]. Test proof: Test Save disabled on errors and enabled on valid data; second Save increments version; endpoint 404 for missing plan_id, rejects `. Spec §7.1, §9 open-report/open-folder, §10 E9.
21. **Read/list stored plans** [History]. Test proof: Red: three plans with multiple versions, highest numeric version selected (`v10` > `v9`), no accidental modification, corrupt JSON produces unreadable row, unknown returns 404, endpoint output contracts and data sourced from JSON. Spec §3.1, §7.2–7.3, §9 GET /api/plans and /api/plans/<id>.
22. **History filter, Load, report/folder UI** [History]. Test proof: Browser tests or lightweight JS tests without new npm dependencies: filter case-insensitive, Load reconstructs 15 inputs/p_source, period preserved rather than replaced, version shown, unreadable row actionless. Spec §7.3, §9.
23. **Auto-complete and history prefill** [History]. Test proof: Red: unknown system `{}`, whitespace/case-insensitive matching, multiple months with timestamp ordering distinct from period, N always blank, zero observed rate floors to. Spec §3.1–3.3, §4.6 next-cycle p, §9 systems/prefill, §11.3.
24. **Actuals calculations and W8–W10** [Actuals]. Test proof: Red: zero/one/all issue cases, n=1 and census, relative margin, W8/W9/W10 strict edge pairs (agreement. Spec §4.6–4.8, §5 W8–W10, §11.2.
25. **Stateless Actuals calculation endpoint** [Actuals]. Test proof: Flask client tests for full scenario: plan N50000 n382 p. Spec §9 POST /api/actuals/calc, §10 E1.
26. **Versioned actuals plus report regeneration** [Actuals]. Test proof: Red: v1 and v2 actuals, v1 bytes unchanged, correct plan_version persisted, latest report contains Actuals plus notes properly escaped, zero-issues bounds, 400/404, simulated write failure leaves JSON immutable and surfaces recoverable report error. Spec §3.1, §8.3–8.4, §9, §11.3.
27. **Actuals complete browser tab** [Actuals]. Test proof: Browser acceptance: record reviewed382 issues11 agreement86% -> ~2. Spec §7.2, §4.6, §9.
28. **Generated plans_log.csv and rebuild API** [Persistence]. Test proof: Red: three plans, one with actuals -> three rows, correct header names/order, UTF8 BOM, commas and multiline notes round-trip, W2;W6, deterministic sorting, no blank extra rows, re-running rebuild idempotent, corrupt folder skipped, retry after simulated failure, route returns `{path,rows}`. Spec §8.5, §9 GET /api/log/rebuild, §11.3.
29. **History consistency and corrupt-file handling** [History]. Test proof: Regression tests: corrupt plan, corrupt latest actuals, mixed valid/invalid folders, byte-for-byte preservation, three-row log excluding broken record, case-insensitive system matching, history and CSV agree on displayed numerical fields and warning codes. Spec §7.3, §8.5, §10 E4, §11.3.
30. **Method API and live educational tab** [Method]. Test proof: Test all ten formula identifiers and exact constants are in JSON and tab; math trace matches n382 scenario; relative margin trace, method version, references, no external links or dependencies. Spec §7.4, §9 GET /api/method, §4.1–4.3.
31. **Immutable answer key and startup gate** [Safety]. Test proof: Test selftest process prints 11 PASS lines and exit0; monkeypatch bad Z or function -> failing case list and exit1; startup method failure banner, direct save/actuals POST rejected, old records left intact; intact calculation passes 11/11. Spec §2.3 --selftest, §7.5, §11.1, §11.5, §10 E8.
32. **Failures, workspace health, and JSON error resilience** [Safety]. Test proof: Force 400/404/500, bad JSON content, malformed config, read-only workspace, disk failure on report vs JSON, stale workspace recovery and health flag, `. Spec §8.6–8.7, §10 E1–E10, §9.
33. **Multi-tab consistency, race safety and launcher regression** [Safety]. Test proof: Test concurrent saves via test client/threads isolated temp workspace create v1/v2 with no lost data; same-name collision gets suffix; two independent calc calls have no global state pollution; subprocess launcher free/reuse/conflict and clean quit; original versions checksum unchanged. Spec §2.3, §3.1, §4.8, §8.7, §10 E5/E6.
34. **Offline desktop fit, polish, and accessibility** [Quality]. Test proof: Static test scans root HTML/report for CDN and external HTTP assets; browser verify keyboard tabbing, focus, tooltips, no horizontal overflow at typical desktop widths, all badges legible, invalid fields and global banner visible, print-to-PDF preview legible. Spec §2.1, §7.1–7.4, §10.
35. **Full automated integration and contract audit** [Quality]. Test proof: Run `python -m pytest -q`, `python hitl_planner. Spec §11.1–11.5, §4–10.
36. **Manual acceptance, documentation, and release** [Release]. Test proof: Manual checklist: K1–K4, 50k/88h case, 1m/385 case, certify slider and Adopt, save+report+print, reviewed382/issues11/agreement86, new month p prefill, Method11/11, quit/restart. Spec §11.6, §12–13, Appendix B.

## 6. Test strategy and quality gates

**Early:** K1–K11 key cases are introduced with their math functions, not as a last-day smoke test; integration uses the same helpers. Boundary tests for every W1–W10, ceil_safe, sample >=N, n_max0, ties, and exact capacity equality.

**Middle:** test every validation limit, 400 field-map, correct API response shape, page offline, no duplicate JS math, safe path naming and atomic cleanup, immutable version checks by raw byte equality. Flask `test_client`, pytest `tmp_path` and monkeypatch prevent real user-data writes.

**Late:** save/reload equivalence, timestamp and version correctness, corrupt-folder exclusion, CSV BOM/quoting, full tab cycle, method trace reproducibility, startup integrity failure blocking even direct forged POSTs, and port/quit subprocess smoke.

Run after every task: `python -m pytest -q`; after answer key exists: `python hitl_planner.py --selftest`; then `git diff --check` and a single commit. Never update a failing answer-key fixture.

## 7. Risk decisions / conservative implementation choices

- Port 5062 clashes cannot be ruled out from supplied files. Verify against existing Pareto/IMR code on target Windows before committing port selection; see `DECISIONS.md`.
- Manual UI tests and print-to-PDF acceptance require the actual Windows machine. They are deliberately **unchecked**, even if all docs are generated.
- The spec explicitly excludes an observed issue-rate confidence interval, despite reverse margin calculations for 0<obs<1; do not add Wilson or other CI "improvements".
- The spec uses exact zero-issue threshold formula even when finite population is large/small. Preserve contract and W7 wording rather than inventing finite-population certification adjustments.
- The spec's 11 cases are the acceptance key; observed examples in §8.2 are illustrative and display rounded numbers, not a replacement for §11.1.
- A plan JSON record can be saved even when warnings (including red W7) fire. The integrity failure and workspace failure are what block saving; do not confuse red W7 with an integrity failure.
- Concurrent version numbering needs process-level synchronization plus exclusive allocation to preserve immutability. Do not pretend an atomic `os.replace` alone prevents overwriting `plan_vN.json` during collision.
- Treat unsafe folder IDs and `system` text as untrusted and escape HTML. This is defensive implementation, not an extra user-facing feature.

## 8. Definition of done

All 36 tasks checked and green; every item in `TRACEABILITY.md` covered; owner's nine browser checks verified; Windows port confirmed; READMEs correct; commit hashes documented; tag v1.0.0. No development code has been created by this planning kit.

## Codex adaptation (workflow only; not a product-spec change)

The original PDF's §12 uses `CLAUDE.md` and specifies `/step N`. In this Codex kit, those guardrails live in `AGENTS.md`, and `prompts/NN_*.md` is submitted as one Codex task. Each step should be applied to the latest reviewed Git revision. Cloud changes should be reviewed as a PR and merged before the next task. Linux cloud execution is not evidence of Windows acceptance; run `ACCEPTANCE.md` on the target PC. `docs/SPEC_TEXT.txt` is a derived search aid, never a replacement for the PDF.
