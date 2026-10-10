# HITL Sample Size Planner — development checklist

Source of truth: [specification v1.0](docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf). Scope: local Windows Python 3.11/Flask tool, offline, one app file and one test file. **Use one prompt file per coding session; test first; commit only when green.**

## 0. Before coding

- [ ] Unzip this kit, commit it to a GitHub repository connected to Codex; keep the source specification at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf`.
- [ ] Confirm Windows Python 3.11 (`py -3.11 --version`) and Git and ChatGPT Codex have access to the connected repository.
- [ ] Create/activate a virtual environment; install `Flask` and `pytest` only.
- [ ] Read `AGENTS.md` Codex repository guardrails and read specification §§3–12.
- [ ] Locate existing Pareto Chart and IMR Control Chart tool launch scripts, if accessible; verify proposed port `5062` does not conflict, or choose an unused fixed port and record that decision in `DECISIONS.md` and spec Appendix B project notes. **Not yet verified.**
- [ ] Commit initial planning/spec files to the default branch and confirm Codex sees `AGENTS.md`, `prompts/`, and the PDF; start task 01 from that revision.
- [ ] Decide cloud Codex vs local Codex; if cloud, configure a Python 3.11 environment and install the specified dependencies. Mark Windows-only checks as deferred, not passed.
- [ ] Confirm only one Codex task/PR is active at a time and do not start the next until the previous is reviewed and merged.
- [ ] Confirm no actual AI conversation data will be uploaded, entered or processed.

## 1. Implementation sessions

For every task below, follow the same six gates (Codex cloud: review/merge before marking done):

1. [ ] Open `prompts/<task>_*.md`; submit the full fenced **text** prompt as one Codex task.
2. [ ] Confirm intended change boundary and expected failing test(s); do not expand scope.
3. [ ] Write red test(s), then minimum green implementation and integration.
4. [ ] Run `python -m pytest -q` (and `python hitl_planner.py --selftest` once implemented); inspect failures.
5. [ ] Confirm no new dependencies, no outbound calls, no overwrites of immutable JSON; review `git diff`.
6. [ ] For Codex cloud, review the green diff/PR and merge it; for local Codex, commit only when green. Tick the session row only after review/merge, and record the commit hash or PR.

Each session row should be ticked **only after** all six gates and the row-specific checks pass.

### Foundation

- [x] **01 — Repository bootstrap, config, and health.** `python -m pytest -q` passes; a manual local launch shows the page; `config.json` is ignored by git; no other runtime modules or network dependencies. Spec §2.1–2.4, §8.1, §8.6, §9, §10 E7. Prompt: `prompts/01_repository_bootstrap_config_and_health.md` — Local commit: `3d437f6`
    - [x] Flask `/` and `/api/health` return correct local-only responses.
    - [x] Config first-run creation and broken-config exit 2 tested.
    - [x] Module import is side-effect free; localhost launch verified.
- [x] **02 — Single-instance launcher and clean quit.** Launcher supports free/same-tool/foreign-port states; quit actually stops server; all endpoints stay localhost only. Spec §2.3, §9, §10 E6. Prompt: `prompts/02_single_instance_launcher_and_clean_quit.md` — Merged commit/PR: `________`
    - [x] Foreign and same-tool occupied ports handled distinctly.
    - [x] Quit and Ctrl-C tested in real local subprocess.
    - [x] Browser open mocked and server binds only to 127.0.0.1.

### Statistics

- [x] **03 — Cochran and finite-population core.** All four key cases and edge tests green, with precise constants and unchanged fixtures. Spec §4.1–4.3 F1–F3, §4.8, §11.1 K1–K3/K6, §11.2. Prompt: `prompts/03_cochran_and_finite_population_core.md` — Merged commit/PR: `________`
    - [x] K1=385, K2=357, K3=1840, K6=1374.
    - [x] Rounded Z constants, safe ceil and finite correction verified.
    - [x] N=1/census and relative margin verified.
- [x] **04 — Assurance, detection, and reverse maths.** Five answer-key cases pass; no undefined division or math exceptions in the required edges. Spec §4.3 F4/F8/F9/F10, §4.8, §11.1 K4/K5/K7/K8/K11. Prompt: `prompts/04_assurance_detection_and_reverse_maths.md` — Merged commit/PR: `________`
    - [x] K4=299, K5=.8660, K7=.0500, K8=.0247, K11=2995.
    - [x] Reverse n>=N and inverse n=0 edge cases covered.
    - [x] Shared numerical helpers return raw auditable intermediates.
- [x] **05 — Headline, review counts, and capacity.** Integrated pure calculation yields one authoritative source for reviews/capacity; no UI or persistence yet. Spec §4.3 F5–F7, §4.8, §11.1 K10–K11, §11.2. Prompt: `prompts/05_headline_review_counts_and_capacity.md` — Merged commit/PR: `________`
    - [x] F5 binding/tie/assurance infeasibility behavior tested.
    - [x] F6 DR cap K10 and F7 exact capacity verdict tested.
    - [x] Headline reuses helper values; no duplicate math.
- [x] **06 — Capacity-max trade-off engine.** K9 and boundary tests green; trade-off is driven by the same hours logic as headline. Spec §4.4, §4.8, §11.1 K9. Prompt: `prompts/06_capacity_max_trade_off_engine.md` — Merged commit/PR: `________`
    - [x] K9 n_max70, DR50, hours24, reverse ±11.7%, bound4.2%.
    - [x] Maximality verified at n_max+1 and empty-capacity case.
    - [x] Trade-off invokes SAME F6/F7 code as headline.
- [x] **07 — Nine-cell sensitivity service.** Sensitivity results are deterministic and use the same core calculator as primary results. Spec §4.5, §11.2. Prompt: `prompts/07_nine_cell_sensitivity_service.md` — Merged commit/PR: `________`
    - [x] Exactly nine mode-appropriate sensitivity cells.
    - [x] Every cell uses headline/certify algorithm and correct binding marker.
    - [x] Custom margin has no highlighted cell.

### Interpretation

- [x] **08 — Plan warning rules W1–W7.** Warnings are emitted from the core service, not re-created in front-end JS. Spec §5, §4.8, §11.2. Prompt: `prompts/08_plan_warning_rules_w1_w7.md` — Merged commit/PR: `________`
    - [x] W1–W7 strict trigger/non-trigger boundary pairs.
    - [x] W2 keyed to observed history, W7 red and saveable.
    - [x] Structured warning code/severity/message tested.
- [x] **09 — Seven reportable statements.** Statement service is reusable in the Plan tab and persisted reporting; it contains all disclaimers. Spec §6, §4.7, §11.2. Prompt: `prompts/09_seven_reportable_statements.md` — Merged commit/PR: `________`
    - [x] Seven statements always; relative/absolute S1.
    - [x] S2 feasible/infeasible/off and S3 power wording verified.
    - [x] Disclaimers S4–S7 included with substituted values.
- [x] **10 — Formatting and reproducible arithmetic.** Trace and formatting are invoked by the existing calculation pipeline and consumed by future Method/report views. Spec §4.7, §7.4, §8.2, §11.2. Prompt: `prompts/10_formatting_and_reproducible_arithmetic.md` — Merged commit/PR: `________`
    - [x] Rounding: hours 1dp, percentages under 1% 2dp.
    - [x] Arithmetic trace includes raw/rounded F1–F8 steps.
    - [x] Display rounding cannot affect FITS decision.

### Integration

- [x] **11 — Input validation and system-period identity.** All entry points can reuse validation, and tests prove bad inputs never reach statistics. Spec §3.1–3.3, §4.7, §10 E1, §11.2. Prompt: `prompts/11_input_validation_and_system_period_identity.md` — Merged commit/PR: `________`
    - [x] I1–I15 type/boundary/required validations tested.
    - [x] ISO month/week, defaults and blank factual inputs enforced.
    - [x] Per-field error messages and no silent clamping.
- [x] **12 — Validated Plan API as a single source.** First fully integrated calculation API works independently of UI and saving. Spec §9 POST /api/calc, §5, §6, §10. Prompt: `prompts/12_validated_plan_api_as_a_single_source.md` — Merged commit/PR: `________`
    - [x] POST /api/calc success and multiple-error 400 cases.
    - [x] 50,000 acceptance scenario: n382 DR58 hours88.
    - [x] No disk writes or JS statistical calculations.

### Plan UI

- [x] **13 — Plan screen forms and debounce.** Plan form drives validated live server calculations; it never computes sample sizes in the browser. Spec §7, §7.1, §3.2–3.3. Prompt: `prompts/13_plan_screen_forms_and_debounce.md` — Merged commit/PR: `________`
    - [x] All 15 controls present and correctly labeled.
    - [x] 150ms debounce and stale response cancellation tested.
    - [x] Bad/blank fields disable Save and gray results.
- [x] **14 — Plan headline, warnings, statements.** The complete headline and interpretation flow works for live inputs. Spec §7.1, §5–6, §4.7. Prompt: `prompts/14_plan_headline_warnings_statements.md` — Merged commit/PR: `________`
    - [x] Headline badges, binding explanations and warning banners.
    - [x] Render exact S1–S7 server strings in grouped area.
    - [x] Invalidation after valid calculation disables Save.
- [x] **15 — Live capacity what-if and Adopt.** What-if behavior is integrated with authoritative Python calculator; no independent JS statistics. Spec §4.4, §7.1, §11.6 items 2–4. Prompt: `prompts/15_live_capacity_what_if_and_adopt.md` — Merged commit/PR: `________`
    - [x] Slider stays separate from saved form until Adopt.
    - [x] Assurance floor holds while certify enabled.
    - [x] Certify-off 43/43/17.2h and panel hiding checked.
- [x] **16 — Sensitivity and assurance UI.** Plan tab now supports every numerical exploratory decision specified. Spec §4.5, §7.1. Prompt: `prompts/16_sensitivity_and_assurance_ui.md` — Merged commit/PR: `________`
    - [x] Nine sensitivity cells, green/red, A binding marker.
    - [x] Custom value correctly leaves no cell selected.
    - [x] Assurance W7 red; power shown when certify off.
- [x] **20 — Plan save workflow and open actions.** User can complete a Plan-tab workflow including durable save and local report launch. Spec §7.1, §9 open-report/open-folder, §10 E9. Prompt: `prompts/20_plan_save_workflow_and_open_actions.md` — Merged commit/PR: `________`
    - [x] Saved toast reports accurate plan/version.
    - [x] Open report/folder success, missing and failure states.
    - [x] Safe report path containment and Save re-use.

### Persistence

- [x] **17 — Atomic file writes and safe names.** Primitives are called by a real lightweight save/reload integration in tests, not left as unattached utilities. Spec §3.1, §8.1, §8.7, §10 E3/E5, §11.3. Prompt: `prompts/17_atomic_file_writes_and_safe_names.md` — Merged commit/PR: `________`
    - [x] Windows sanitizing incl reserved names and collisions.
    - [x] Atomic write failures clean temp and retain prior bytes.
    - [x] Workspace containment rejects path traversal.
- [x] **18 — Immutable plan saves and versions.** Versioned JSON is the immutable single source of truth and functional POST route is tested. Spec §3.1, §8.2, §8.7, §9, §11.3. Prompt: `prompts/18_immutable_plan_saves_and_versions.md` — Merged commit/PR: `________`
    - [x] Server-side inputs validation and calculations on save.
    - [x] v1/v2 creation with v1 byte-for-byte unchanged.
    - [x] Full required plan JSON incl method/warnings/statements.
- [x] **19 — Stand-alone printable HTML report.** Plan save response has working `report_path`; regenerated HTML is independent and printable offline. Spec §8.4, §6–7, §11.3. Prompt: `prompts/19_stand_alone_printable_html_report.md` — Merged commit/PR: `________`
    - [x] Report self-contained and A4 printable offline.
    - [x] Contains inputs, seven statements and arithmetic.
    - [x] Escaping of special characters and regeneration verified.
- [ ] **28 — Generated plans_log.csv and rebuild API.** CSV is reliable derived read model for spreadsheet inspection and history. Spec §8.5, §9 GET /api/log/rebuild, §11.3. Prompt: `prompts/28_generated_plans_log_csv_and_rebuild_api.md` — Merged commit/PR: `________`
    - [ ] 43-column CSV exact header order and UTF8 BOM.
    - [ ] CSV notes with commas/newlines round-trip.
    - [ ] Rebuild derives from latest JSON, repeat is idempotent.

### History

- [x] **21 — Read/list stored plans.** History and Actuals dropdown can rely on one tested read model. Spec §3.1, §7.2–7.3, §9 GET /api/plans and /api/plans/<id>. Prompt: `prompts/21_read_list_stored_plans.md` — Merged commit/PR: `________`
    - [x] GET plans list and plan detail latest vN.
    - [x] 404 unknown, corrupt folder marked unreadable.
    - [x] Read model sourced from saved JSON, not folder guess.
- [x] **22 — History filter, Load, report/folder UI.** Previously saved plans can be found, reopened, and reused through the live Plan form. Spec §7.3, §9. Prompt: `prompts/22_history_filter_load_report_folder_ui.md` — Merged commit/PR: `________`
    - [x] History newest-first rows and case-insensitive filtering.
    - [x] Load restores period and all inputs including N.
    - [x] Corrupt rows have no action buttons; no delete.
- [ ] **23 — Auto-complete and history prefill.** New period can start from previous observations while never inventing current population. Spec §3.1–3.3, §4.6 next-cycle p, §9 systems/prefill, §11.3. Prompt: `prompts/23_auto_complete_and_history_prefill.md` — Merged commit/PR: `________`
    - [ ] Case-insensitive saved systems datalist/prefill.
    - [ ] Observed-rate source and zero-rate 0.1% floor.
    - [ ] N blank, period reset, manual field edits preserved.
- [ ] **29 — History consistency and corrupt-file handling.** History, log, and prefill consistently reflect readable source records without silent data loss. Spec §7.3, §8.5, §10 E4, §11.3. Prompt: `prompts/29_history_consistency_and_corrupt_file_handling.md` — Merged commit/PR: `________`
    - [ ] Unreadable folders visible but never altered.
    - [ ] History/CSV/Prefill agree on readable records.
    - [ ] Corrupt/latest actuals excluded and recovery possible.

### Actuals

- [ ] **24 — Actuals calculations and W8–W10.** All actuals metrics reuse F9/F10 and are correctly interpretable in extreme outcomes. Spec §4.6–4.8, §5 W8–W10, §11.2. Prompt: `prompts/24_actuals_calculations_and_w8_w10.md` — Merged commit/PR: `________`
    - [ ] Interior/zero/all issues mapped to margin/bounds.
    - [ ] Certify met/not met/off/issues-found cases.
    - [ ] W8–W10 strict boundary pairs and validation.
- [ ] **25 — Stateless Actuals calculation endpoint.** Actuals can be previewed and validated before committing a record. Spec §9 POST /api/actuals/calc, §10 E1. Prompt: `prompts/25_stateless_actuals_calculation_endpoint.md` — Merged commit/PR: `________`
    - [ ] Actuals calc uses saved plan not client-forged values.
    - [ ] 382/11/.86 yields observed~2.9%/margin~1.7%.
    - [ ] Stateless 400 and 404 behavior tested.
- [ ] **26 — Versioned actuals plus report regeneration.** Actuals recording is durable and immediately visible in latest report and read API. Spec §3.1, §8.3–8.4, §9, §11.3. Prompt: `prompts/26_versioned_actuals_plus_report_regeneration.md` — Merged commit/PR: `________`
    - [ ] Versioned actuals v1/v2 and preserved bytes.
    - [ ] Report regenerates from latest persisted JSON.
    - [ ] Actuals plan_version reference remains correct.
- [ ] **27 — Actuals complete browser tab.** End user can finish a Plan→Actuals cycle from the browser alone. Spec §7.2, §4.6, §9. Prompt: `prompts/27_actuals_complete_browser_tab.md` — Merged commit/PR: `________`
    - [ ] Actuals form, plan summary and live bound display.
    - [ ] Record again generates new version safely.
    - [ ] Agreement 86% vs <80% warning and invalid-count gate.

### Method

- [ ] **30 — Method API and live educational tab.** Auditor can reproduce the output and read assumptions directly from UI. Spec §7.4, §9 GET /api/method, §4.1–4.3. Prompt: `prompts/30_method_api_and_live_educational_tab.md` — Merged commit/PR: `________`
    - [ ] Method F1–F10/Z table, assumptions and references.
    - [ ] Live arithmetic equals Plan headline results.
    - [ ] No false 11/11 passed before actual selftest.

### Safety

- [ ] **31 — Immutable answer key and startup gate.** Statistical integrity becomes an enforceable runtime gate, not a cosmetic label. Spec §2.3 --selftest, §7.5, §11.1, §11.5, §10 E8. Prompt: `prompts/31_immutable_answer_key_and_startup_gate.md` — Merged commit/PR: `________`
    - [ ] K1–K11 selftest prints 11 PASS + exit0.
    - [ ] Injected broken constant fails and names cases.
    - [ ] Startup failure blocks save at API and UI levels.
- [ ] **32 — Failures, workspace health, and JSON error resilience.** All required failure modes have deterministic recoverable responses. Spec §8.6–8.7, §10 E1–E10, §9. Prompt: `prompts/32_failures_workspace_health_and_json_error_resilience.md` — Merged commit/PR: `________`
    - [ ] E1–E10 failures have correct response paths.
    - [ ] Workspace failure health/banner and recovery.
    - [ ] 500 hides stack traces; temp files cleaned.
- [ ] **33 — Multi-tab consistency, race safety and launcher regression.** The specified single-user, multi-tab usage cannot silently destroy saved work. Spec §2.3, §3.1, §4.8, §8.7, §10 E5/E6. Prompt: `prompts/33_multi_tab_consistency_race_safety_and_launcher_regression.md` — Merged commit/PR: `________`
    - [ ] Concurrent versions never overwrite old files.
    - [ ] Port conflict/reuse and Quit regression passes.
    - [ ] Two tabs calculate independently without stale globals.

### Quality

- [ ] **34 — Offline desktop fit, polish, and accessibility.** User-facing experience is stable, offline, understandable and faithful to spec. Spec §2.1, §7.1–7.4, §10. Prompt: `prompts/34_offline_desktop_fit_polish_and_accessibility.md` — Merged commit/PR: `________`
    - [ ] Desktop light cards, four tabs, Quit and focus states.
    - [ ] No external CSS/JS/URL/CDN and keyboard smoke.
    - [ ] Report print, labels/tooltips, error states clear.
- [ ] **35 — Full automated integration and contract audit.** Every stated test category has explicit passing evidence, with no skipped mandatory contract tests. Spec §11.1–11.5, §4–10. Prompt: `prompts/35_full_automated_integration_and_contract_audit.md` — Merged commit/PR: `________`
    - [ ] Entire Plan→Actuals→History→CSV→Method chain tested.
    - [ ] All I/F/K/W/S and 15 endpoints covered.
    - [ ] pytest/selftest green with isolated test workspaces.

### Release

- [ ] **36 — Manual acceptance, documentation, and release.** Ship only after all automatic and manual checks are green, port is verified, and the owner approves release. Spec §11.6, §12–13, Appendix B. Prompt: `prompts/36_manual_acceptance_documentation_and_release.md` — Merged commit/PR: `________`
    - [ ] Windows README commands work from clean environment.
    - [ ] All nine owner acceptance cases recorded as passed.
    - [ ] Port verified, owner sign-off received, then release tag.

## 2. Final contract gates

- [ ] All **11** answer-key cases K1–K11 pass exactly, with Z constants 1.645, 1.960, 2.576.
- [ ] F1–F10 are independently tested (including reverse mode and n_max=0), no browser calculation duplicates.
- [ ] W1–W10 each have in/out boundary tests; W7 remains saveable but does not make a false certify claim.
- [ ] Exactly seven S1–S7 generated for absolute, relative and all certification states.
- [ ] I1–I15 validated with out-of-range errors; N and team facts are not guessed.
- [ ] All 15 endpoints from §9 tested for success/error (enumerate in `TRACEABILITY.md`).
- [ ] plan_vN.json and actuals_vN.json immutable; report.html and plans_log.csv regenerated atomically.
- [ ] Corrupt JSON leaves a non-destructive unreadable History row and is excluded from log/prefill.
- [ ] Offline behavior verified and bound to 127.0.0.1 only; local file opening handles failures.
- [ ] Startup 11/11 integrity check gates Save/Record in backend and UI.
- [ ] Desktop Plan, Actuals, History, Method and Quit all exercised.
- [ ] Acceptance checklist in `ACCEPTANCE.md` completed with notes/evidence.
- [ ] Port collision check marked **verified**, with any adjustment documented.
- [ ] README commands and Windows launch steps checked on target machine.
- [ ] End-to-end `python -m pytest -q` succeeds.
- [ ] `python hitl_planner.py --selftest` gives 11 PASS and exit code 0.
- [ ] Check no v2 features or conversation-content ingestion were introduced.
- [ ] Owner approves release; tag `v1.0.0` only afterward.

## 3. Risks / observations log

| Date | Task | Finding or blocker | Owner decision / disposition |
|---|---|---|---|
| 2026-10-08 | 00 | Port 5062 requires comparison with existing Pareto/IMR tool scripts, which were not attached. | Confirm on Windows before launch. |
| 2026-10-08 | 00 | External code-generation agent may not have PDF-reading support. | Supply its readable PDF or extracted text without altering the source contract. |

**Progress:** 22 / 36 implementation tasks completed in this supplied planning kit. The checklist is not evidence of implemented or tested code.

## Codex task review gate (repeat before checking off any row)

- [ ] Codex shows which files changed and which exact tests ran.
- [ ] Full pytest suite passed **in the current environment** (or blocking failure reported).
- [ ] No K1–K11 expected values or contract formulas changed.
- [ ] No user data, secrets, or runtime network dependencies added.
- [ ] If working in cloud Codex, PR/change set reviewed and merged onto the branch used by the next task.
- [ ] Unrun Windows-specific checks listed as deferred for `ACCEPTANCE.md`.

## Execution evidence — 2026-10-10

- Complete kit recovered from Downloads; all nine supplied Markdown files matched SHA256 before changes.
- Local Windows execution selected; user explicitly authorizes automatic sequential progression after green checks.
- Python 3.11.17; isolated virtual environment; Flask and pytest installed with their transitive dependencies.
- GitHub authentication verified as tjhrness; only SDG and logmark exposed. Planner repository access requested; no remote/push/PR yet.
- Pareto script uses 8765; downloaded IMR script uses 5000–5010; 5062 successfully bound on this PC. IMR archive comparison is not proof of a different installed version.
- Task 01 RED: missing module collection error. GREEN: python -m pytest -q, 10 passed; git diff --check clean.
- Task 01 Windows browser: localhost 5062 displayed title and honest placeholder in Codex browser; no external assets.
- Startup integrity and selftest not yet implemented; no selftest claim.

- Task 02 RED: 5 missing-launcher failures, 10 existing tests passed. GREEN: 15 passed; browser Quit stopped real Windows launcher with exit 0; Ctrl-C separately exercised in a PTY. Health probes use only literal 127.0.0.1; browser open mocked in tests.

- Task 02 commit: 2338064. Task 03 RED: five missing-core failures. GREEN: full suite 20 passed; K1=385, K2=357, K3=1840, K6=1374 unchanged. F1–F3/raw values, exact Z, ceil_safe, N=1/census and absolute/relative equivalence checked; diff clean.

- Task 03 commit: 9703dcc. Task 04 RED: 2 missing-helper failures. GREEN: full suite 22 passed; K4, K5, K7, K8, K11 unchanged; n=0, N=1, census and monotonicity covered.

- Task 04 commit: ad8dd4e. Task 05 RED: 6 missing-function failures. GREEN: 28 passed; K10 double-review cap and W7 infeasible headline behavior; ties/cochran/assurance/off, equality tolerance and census. Default scenario 382/58/440/88.0h/24.0h matches acceptance.

- Task 05 commit: 66199db. Task 06 RED: 7 missing trade-off failures. GREEN: full suite 35 passed; K9 n_max70/DR50/reviews120/hours24, next71 fails; 0 capacity, tiny capacity, census, relative margin and population cap tested.

- Task 06 commit: 3e6f824. Task 07 RED: 3 missing-grid failures. GREEN: 38 passed; nine mode-correct cells, main-calculator equivalence, A markers, custom values/no highlight and exact selection.

- Task 07 commit: 5e9d372. Task 08 RED: 6 missing-warning failures. GREEN: 44 passed; all W1–W7 boundary pairs; W2 uses observed-history presence, W7 red, W5+W6 together, no duplicate codes; exact message templates.

- Task 08 commit: f6f1dbd. Task 09 RED: 4 missing-statement failures. GREEN: 48 passed; exactly seven ordered templates, absolute/relative S1, three S2 states, power, random-selection disclaimer, English month/week, small rates and thousands.

- Task 09 commit: 06e4b5c. Task 10 RED: missing formatter failure. GREEN: 49 passed; complete ordered Z/F1–F8 arithmetic retains repr precision; human percentages/hours/counts separated; tight rounding cannot change verdict.

- Task 10 commit: 23439f7. Task 11 RED: 77 missing-validation failures. GREEN: 126 passed; I1–I15 required/range/type/finite cases, exact endpoints, ISO week validity, normalized system matching, defaults without factual guesses and invalid data blocked before math.

- Task 11 commit: 336d4b6. Task 12 RED: missing route404. GREEN: 127 passed; API success and400/malformed JSON, twenty calls leave workspace unchanged, seven statements/nine cells/arithmetic/warnings, default acceptance numbers.

- Task 12 commit: 331f3b1. Task 13 RED: missing form-controls test. GREEN: 128 passed; Windows browser entered required facts, API validation cleared all errors, blank N immediately invalidated and outlined, keyboard Tab and Quit exercised. Saving remains disabled until durable save implementation.

- Task 13 commit: a9acdf5. Task 14 RED: missing output container. GREEN: 129 passed; browser headline382/88h/DOES NOT FIT, exactly7 rendered statements; clearing N invalidates and Save disabled; server binding explanation verified.

- Task 14 commit: df87f47. Task 15 RED: missing slider/control failure. GREEN: 130 passed. Windows browser: slider15% preserved form5%; certify-on299/50/69.8h; certify-off43/43/17.2h; Adopt wrote15%, FITS and panel hidden; relative slider5–50 step1.

- Task 15 commit: 4c65b50. Task 16 RED: missing cards/grid failure. GREEN: 131 passed; Windows browser9 cells/90-95-99 headings, one default highlight/no custom highlight, A cells, W7 red/infeasible2995>N2000 and detection remains visible with certify off.

- Task 16 commit: b42c1d9. Task 17 RED: three missing persistence helper failures. GREEN: 134 passed; Unicode save/reload, sanitized date-first names, collision suffix, immutable bytes, containment and replace-failure cleanup.

- Task 17 commit: 29b31a2. Task 18 RED: missing save route (404). GREEN: 136 passed; v1 bytes unchanged after v2, concurrent distinct versions, recalculated tampered output, W7 save, offset timestamps, all eleven integrity cases and minimal generated report. GitHub clone/access succeeded; public full-kit push rejected by automatic review, publication preference pending.

- Task 18 commit: aede465. Task 19 RED: missing print stylesheet. GREEN: 137 passed; report generated from saved JSON, all ordered sections and seven escaped statements, inline A4 CSS, no scripts/outbound URLs, latest-version regeneration. Owner Windows print-to-PDF smoke check remains pending for final acceptance.

- Task 19 commit: 68dd949. Task 20 RED: missing Save workflow. GREEN: 138 passed; missing/traversal/open-failure routes covered. Windows browser Save v1/v2, accurate toast and enabled re-save, actual os.startfile report/folder success, Quit shutdown verified.

- Task 20 commit: 5d8aaed. Task 21 RED: missing GET list. GREEN: 139 passed; numeric v10 over v9, untouched immutable bytes, case-preserved identity, corrupt row and unknown404, latest detail. User explicitly approved full-kit public GitHub publication.

- Task 21 commit: 9325629. Task 22 RED: missing History controls. GREEN: 140 passed; month/week calendar ordering, Windows browser mixed-case filter leaves one row/three actions, corrupt row actionless, Load restores N50000 and saved August period with source badge.
