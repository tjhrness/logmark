# Traceability and tests — contract coverage matrix

Source: 34-page spec v1.0. **Automated coverage verified on Windows, 10 October 2026: 158 pytest cases pass and K1–K11 selftest passes.** Owner Print-to-PDF, Excel and release sign-off remain open in ACCEPTANCE.md.

## Inputs & outputs

| Spec item | Scope | Implementation task | Minimum assertion | Done |
|---|---|---|---|---|
| I1 period type | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I2 period label | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I3 system | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I4 population N | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I5 confidence | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I6 margin mode | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I7 margin input | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I8 expected issue rate | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I9 SMEs | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I10 hours/SME | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I11 minutes/conversation | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I12 DR share | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I13 DR floor | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I14 certify toggle | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |
| I15 threshold | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [x] |

## Formula, answer-key and warning coverage

| ID | Rule / expected | Tasks | Done |
|---|---|---|---|
| F1 | E=E_abs or r×p | 03 | [x] |
| F2 | Cochran n0 | 03 | [x] |
| F3 | finite population correction | 03 | [x] |
| F4 | assurance n_assure | 04 | [x] |
| F5 | headline with binding | 05 | [x] |
| F6 | double-review capped at n | 05 | [x] |
| F7 | reviews, hours, capacity, fits | 05 | [x] |
| F8 | detection power | 04 | [x] |
| F9 | reverse margin at n | 04 | [x] |
| F10 | inverse certify bound at n | 04 | [x] |
| K1 | K1 N1m C95 E5 p50 ->385 | 03,31 | [x] |
| K2 | K2 N5000 C95 E5 p50 ->357 | 03,31 | [x] |
| K3 | K3 N1m C99 E3 p50 ->1840 | 03,31 | [x] |
| K4 | K4 C95 T1% ->299 | 04,31 | [x] |
| K5 | K5 n200 T1% ->0.8660 | 04,31 | [x] |
| K6 | K6 N20k C95 p4 r25% ->1374 | 03,31 | [x] |
| K7 | K7 N5000 n357 p50 C95 ->0.0500 | 04,31 | [x] |
| K8 | K8 n120 C95 ->0.0247 | 04,31 | [x] |
| K9 | K9 capacity N50k/3x8h/12min/15%/50 ->n70 | 06,31 | [x] |
| K10 | K10 DR40=40,DR400=60 | 05,31 | [x] |
| K11 | K11 C95 T0.1% -> n_assure2995 > N2000 | 04,31 | [x] |
| W1 | W1 E>.10 | 08,35 | [x] |
| W2 | W2 p=.5 & no observed rate history | 08,35 | [x] |
| W3 | W3 absolute E>=p | 08,35 | [x] |
| W4 | W4 DR<F capped by n | 08,35 | [x] |
| W5 | W5 N<200 | 08,35 | [x] |
| W6 | W6 n>.8N | 08,35 | [x] |
| W7 | W7 certify && n_assure>N (red) | 08,35 | [x] |
| W8 | W8 reviewed<n_planned | 24,35 | [x] |
| W9 | W9 obs>2p or obs<.5p | 24,35 | [x] |
| W10 | W10 agreement<.80 | 24,35 | [x] |

S1–S7 — seven and exactly seven sentences tested for all applicability variants [x]; §6, task 09.

Trade-off: n_max and n_max+1 boundary [x], relative reverse E [x], n_max=0 [x]; task 06.
Sensitivity: 3 × 3 mode mapping [x], bind indicator [x], custom-value no highlight [x]; task 07.

## API coverage (spec §9, **15 endpoints**)

| Route | Task | Success | Validation/error |
|---|---|---|---|
| `GET /` | 01 | [x] 200 HTML | [x] offline/no CDN |
| `GET /api/health` | 01 | [x] tool/version/workspace_ok | [x] workspace failure |
| `POST /api/calc` | 12 | [x] outputs/warnings/statements/arithmetic | [x] 400 field map |
| `POST /api/plans` | 18 | [x] new version | [x] 400; integrity/workspace gate |
| `GET /api/plans` | 21 | [x] History list | [x] corrupt folder |
| `GET /api/plans/<plan_id>` | 21 | [x] plan + actuals | [x] 404 |
| `GET /api/prefill?system=` | 23 | [x] prefill + p_source | [x] unknown system {} |
| `GET /api/systems` | 23 | [x] saved names | [x] corrupt excluded |
| `POST /api/actuals/calc` | 25 | [x] outputs/warnings | [x] 400/404 |
| `POST /api/plans/<plan_id>/actuals` | 26 | [x] new actuals version | [x] 400/404; gate |
| `GET /api/log/rebuild` | 28 | [x] path/rows | [x] write failure |
| `POST /api/open-report` | 20 | [x] ok true | [x] missing/open failure |
| `POST /api/open-folder` | 20 | [x] ok true | [x] missing/open failure |
| `GET /api/method` | 30 | [x] constants/formulas/integrity | [x] integrity failure |
| `POST /api/quit` | 02 | [x] ok true/shutdown | [x] only local |

## Persistence, screens and failure coverage

| Area | Task | Acceptance | Done |
|---|---|---|---|
| Immutable plans vN | 17–19 | save v1/v2 and earlier bytes unchanged | [x] |
| Immutable actuals vN | 24–26 | save v1/v2 and earlier bytes unchanged | [x] |
| Self-contained A4 report | 19,26 | seven statements, Actuals, no external asset | [x] |
| CSV fixed columns, Excel BOM | 28 | 43 columns, Unicode/multiline notes, regenerated | [x] |
| Safe sanitization + collisions | 17,33 | reserved names and `(2)` | [x] |
| Config/launcher | 01–02,32–33 | first run, port conflict, same instance, Quit | [x] |
| Plan tab | 13–16,20 | full input/output/slider/grid/save | [x] |
| History tab | 21–23,29 | filter/load/corrupt handling | [x] |
| Actuals tab | 24–27 | bounds, agreement, versioning | [x] |
| Method tab | 30–31 | formulas, live arithmetic, integrity status | [x] |
| E1–E10 | 32 | each typed error path, 400/404/500 response | [x] |
| Owner manual 9 checks | 36 | see ACCEPTANCE.md; print/Excel/sign-off pending | [ ] |

**Traceability completion:** Automated rows checked against the tests below; owner acceptance remains separately tracked.

## Executed evidence and test mapping

Verified on the target Windows machine with Python 3.11.17, Flask 3.1.3 and pytest 9.1.1. Commands: `.venv\Scripts\python.exe -m pytest -q` (158 passed, no skips), `.venv\Scripts\python.exe hitl_planner.py --selftest` (PASS K1–K11, exit 0), and `python -m py_compile hitl_planner.py test_hitl_planner.py` (success). A fresh `.verification-venv` installed only Flask/pytest and their dependencies from cache; its selftest and full suite also passed. All automated workspaces/configs are isolated fixtures.

| Contract items | Passing tests in test_hitl_planner.py |
|---|---|
| I1–I15, finite/type/range/ISO dates, factual defaults | test_plan_validation_invalid_fields; test_nonfinite_and_bool_numbers_refused; test_validation_limits_dates_defaults_and_no_mutation |
| F1–F3, K1–K3/K6 | test_cochran_answer_key; test_precision_constants_rounding_and_census |
| F4/F8/F9/F10, K4/K5/K7/K8/K11 | test_assurance_reverse_answer_keys; test_assurance_reverse_edges_and_monotonicity; test_headline_binding |
| F5–F7, K9/K10, equality and no-review capacity | test_review_counts_contract_and_capacity; test_headline_binding; test_headline_tie_is_cochran; test_capacity_max_answer_key_and_shared_hours; test_capacity_max_boundaries |
| K1–K11 runtime enforcement and fault injection | test_selftest_process_and_injected_failure_gate; test_method_api_and_live_trace_contract |
| W1–W7, including observed-history W2 and saveable W7 | test_warning_output_boundaries; test_warning_history_population_mode_and_structure; test_system_prefill_timestamp_matching_and_observed_history; test_plan_save_route_versions_recalculate_and_schema |
| W8–W10, zero/one/all issues and relative/census outcomes | test_actuals_boundaries_relative_and_validation; test_actuals_extremes_and_shared_formulas |
| S1–S7 and exact applicable variants | test_seven_statements_variants; test_standalone_report_escaped_complete_latest |
| Sensitivity/what-if and presentation-only formatting | test_sensitivity_grid; test_whatif_contract_and_ui; test_display_formatting_and_arithmetic_trace; test_headline_ui_response_mapping |
| All fifteen §9 routes in one lifecycle | test_full_isolated_lifecycle_all_fifteen_endpoints |
| Endpoint error contracts and stored-plan authority | test_plan_api_success_errors_and_statelessness; test_actuals_api_stateless_and_saved_plan_authority; test_plan_read_model_numeric_latest_corruption_and_identity; test_save_ui_and_safe_open_actions |
| E1/E2 validation/extremes | Validation, capacity boundary and Actuals boundary tests above |
| E3 atomic failures, drive health, partial save and retry | test_atomic_failure_preserves_old_and_cleans_temporary; test_api_failure_resilience_workspace_recovery_and_json_errors; test_actuals_saves_versions_report_and_recoverable_failure; test_csv_log_exact_schema_roundtrip_rebuild_and_failure; test_log_failure_response_and_all_issue_prefill_boundary |
| E4 corrupt records preserved/excluded | test_corrupt_record_types_and_invalid_config_schema; test_history_csv_prefill_consistency_with_corrupt_actuals |
| E5 Windows names, containment and simultaneous collision | test_safe_names_and_workspace_containment; test_persistence_slice_unicode_collisions_and_immutability; test_concurrent_plan_actuals_collision_and_statelessness |
| E6 free/same/foreign port, localhost, Quit/Ctrl-C | test_port_probe_free_foreign_and_same_tool; test_launcher_occupied; test_launcher_binding_and_keyboard_interrupt; test_real_subprocess_launch_and_quit |
| E7 malformed/unreadable config preserved, exit 2 | test_bad_config_preserved_exit2; test_unreadable_config; test_config_preserved |
| E8 failed integrity blocks UI/backend recording | test_selftest_process_and_injected_failure_gate |
| E9 Windows file-open success/failure/missing resources | test_save_ui_and_safe_open_actions; real Windows browser open-report/open-folder smoke check, task 20 |
| E10 console traceback, safe JSON 500 | test_api_failure_resilience_workspace_recovery_and_json_errors |
| Immutable hashes/versions, concurrent requests | test_plan_save_route_versions_recalculate_and_schema; test_concurrent_plan_requests_preserve_distinct_versions; test_actuals_saves_versions_report_and_recoverable_failure; test_concurrent_plan_actuals_collision_and_statelessness |
| Report offline/escaped/latest version, CSV 43-column BOM/multiline/idempotence | test_standalone_report_escaped_complete_latest; test_csv_log_exact_schema_roundtrip_rebuild_and_failure; test_offline_assets_and_accessible_tab_contract |
| History/calendar sorting/prefill consistency | test_history_ui_and_calendar_period_sorting; test_history_csv_prefill_consistency_with_corrupt_actuals; test_system_prefill_timestamp_matching_and_observed_history |

Windows in-app browser checks also exercised Plan validation, headline, slider and Adopt, nine-cell grid, W7, Save v1/v2 and native file opening, History filter/Load, prefill preserving manual edits, Actuals v1/v2 and bounds, live Method arithmetic, keyboard focus/arrow navigation, and Quit. Desktop layout was visually inspected at 1280×900 with no page overflow. These browser observations do not substitute for native Print-to-PDF or Excel checks, which remain explicit owner checks. No statistical v2 features, conversation uploads, generated PDFs, external assets or runtime telemetry were added.
