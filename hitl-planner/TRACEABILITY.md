# Traceability and tests — contract coverage matrix

Source: 34-page spec v1.0. **Coverage statuses remain open until code and tests actually exist.** This is a coverage plan, not evidence of passing tests.

## Inputs & outputs

| Spec item | Scope | Implementation task | Minimum assertion | Done |
|---|---|---|---|---|
| I1 period type | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I2 period label | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I3 system | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I4 population N | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I5 confidence | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I6 margin mode | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I7 margin input | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I8 expected issue rate | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I9 SMEs | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I10 hours/SME | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I11 minutes/conversation | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I12 DR share | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I13 DR floor | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I14 certify toggle | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |
| I15 threshold | §3.2 | 11,13,23 | Valid value and both boundary failures; prefill/default behavior | [ ] |

## Formula, answer-key and warning coverage

| ID | Rule / expected | Tasks | Done |
|---|---|---|---|
| F1 | E=E_abs or r×p | 03 | [ ] |
| F2 | Cochran n0 | 03 | [ ] |
| F3 | finite population correction | 03 | [ ] |
| F4 | assurance n_assure | 04 | [ ] |
| F5 | headline with binding | 05 | [ ] |
| F6 | double-review capped at n | 05 | [ ] |
| F7 | reviews, hours, capacity, fits | 05 | [ ] |
| F8 | detection power | 04 | [ ] |
| F9 | reverse margin at n | 04 | [ ] |
| F10 | inverse certify bound at n | 04 | [ ] |
| K1 | K1 N1m C95 E5 p50 ->385 | 03,31 | [ ] |
| K2 | K2 N5000 C95 E5 p50 ->357 | 03,31 | [ ] |
| K3 | K3 N1m C99 E3 p50 ->1840 | 03,31 | [ ] |
| K4 | K4 C95 T1% ->299 | 04,31 | [ ] |
| K5 | K5 n200 T1% ->0.8660 | 04,31 | [ ] |
| K6 | K6 N20k C95 p4 r25% ->1374 | 03,31 | [ ] |
| K7 | K7 N5000 n357 p50 C95 ->0.0500 | 04,31 | [ ] |
| K8 | K8 n120 C95 ->0.0247 | 04,31 | [ ] |
| K9 | K9 capacity N50k/3x8h/12min/15%/50 ->n70 | 06,31 | [ ] |
| K10 | K10 DR40=40,DR400=60 | 05,31 | [ ] |
| K11 | K11 C95 T0.1% -> n_assure2995 > N2000 | 04,31 | [ ] |
| W1 | W1 E>.10 | 08,35 | [ ] |
| W2 | W2 p=.5 & no observed rate history | 08,35 | [ ] |
| W3 | W3 absolute E>=p | 08,35 | [ ] |
| W4 | W4 DR<F capped by n | 08,35 | [ ] |
| W5 | W5 N<200 | 08,35 | [ ] |
| W6 | W6 n>.8N | 08,35 | [ ] |
| W7 | W7 certify && n_assure>N (red) | 08,35 | [ ] |
| W8 | W8 reviewed<n_planned | 24,35 | [ ] |
| W9 | W9 obs>2p or obs<.5p | 24,35 | [ ] |
| W10 | W10 agreement<.80 | 24,35 | [ ] |

S1–S7 — seven and exactly seven sentences tested for all applicability variants [ ]; §6, task 09.

Trade-off: n_max and n_max+1 boundary [ ], relative reverse E [ ], n_max=0 [ ]; task 06.
Sensitivity: 3 × 3 mode mapping [ ], bind indicator [ ], custom-value no highlight [ ]; task 07.

## API coverage (spec §9, **15 endpoints**)

| Route | Task | Success | Validation/error |
|---|---|---|---|
| `GET /` | 01 | [ ] 200 HTML | [ ] offline/no CDN |
| `GET /api/health` | 01 | [ ] tool/version/workspace_ok | [ ] workspace failure |
| `POST /api/calc` | 12 | [ ] outputs/warnings/statements/arithmetic | [ ] 400 field map |
| `POST /api/plans` | 18 | [ ] new version | [ ] 400; integrity/workspace gate |
| `GET /api/plans` | 21 | [ ] History list | [ ] corrupt folder |
| `GET /api/plans/<plan_id>` | 21 | [ ] plan + actuals | [ ] 404 |
| `GET /api/prefill?system=` | 23 | [ ] prefill + p_source | [ ] unknown system {} |
| `GET /api/systems` | 23 | [ ] saved names | [ ] corrupt excluded |
| `POST /api/actuals/calc` | 25 | [ ] outputs/warnings | [ ] 400/404 |
| `POST /api/plans/<plan_id>/actuals` | 26 | [ ] new actuals version | [ ] 400/404; gate |
| `GET /api/log/rebuild` | 28 | [ ] path/rows | [ ] write failure |
| `POST /api/open-report` | 20 | [ ] ok true | [ ] missing/open failure |
| `POST /api/open-folder` | 20 | [ ] ok true | [ ] missing/open failure |
| `GET /api/method` | 30 | [ ] constants/formulas/integrity | [ ] integrity failure |
| `POST /api/quit` | 02 | [ ] ok true/shutdown | [ ] only local |

## Persistence, screens and failure coverage

| Area | Task | Acceptance | Done |
|---|---|---|---|
| Immutable plans vN | 17–19 | save v1/v2 and earlier bytes unchanged | [ ] |
| Immutable actuals vN | 24–26 | save v1/v2 and earlier bytes unchanged | [ ] |
| Self-contained A4 report | 19,26 | seven statements, Actuals, no external asset | [ ] |
| CSV fixed columns, Excel BOM | 28 | 43 columns, Unicode/multiline notes, regenerated | [ ] |
| Safe sanitization + collisions | 17,33 | reserved names and `(2)` | [ ] |
| Config/launcher | 01–02,32–33 | first run, port conflict, same instance, Quit | [ ] |
| Plan tab | 13–16,20 | full input/output/slider/grid/save | [ ] |
| History tab | 21–23,29 | filter/load/corrupt handling | [ ] |
| Actuals tab | 24–27 | bounds, agreement, versioning | [ ] |
| Method tab | 30–31 | formulas, live arithmetic, integrity status | [ ] |
| E1–E10 | 32 | each typed error path, 400/404/500 response | [ ] |
| Owner manual 9 checks | 36 | see ACCEPTANCE.md | [ ] |

**Traceability completion:** 0 rows checked at kit creation.
