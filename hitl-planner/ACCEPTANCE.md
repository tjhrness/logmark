# Windows owner acceptance — HITL Sample Size Planner v1.0

**Status: NOT RUN.** These manual checks are sourced from specification §11.6 (pages 28–29) and cannot be marked complete until performed against a running Windows application. Log browser, input values, actual observed values and screenshots as applicable.

## Prerequisites

- [ ] Confirm port choice against existing Pareto and IMR tools, then configure an unused fixed port.
- [ ] Open the app via `python hitl_planner.py` on Windows (Python 3.11).
- [ ] Verify four tabs and Quit; browser has no internet dependency.

## Spec §11.6 manual checks

- [ ] **A1 / key cases:** Enter K1–K4 on Plan; obtain 385, 357, 1,840, 299 on assurance.
- [ ] **A2 / default scenario:** N=50,000; confidence=95%; absolute ±5%; p=50%; SMEs=3, hours/SME=8, minutes/review=12, double-review share=15%, floor=50, certify ON threshold=1%. Verify n=382, DR=58, total 440 reviews=88.0 SME hours, capacity=24.0 h DOES NOT FIT, precision-binding, detection ~97.8%, W2; n_max=70, reverse margin ±11.7%, inverse certify 4.2%.
- [ ] **A3 / large N:** Change N to 1,000,000; n=385, DR=58, 88.6 h.
- [ ] **A4 / what-if:** certify ON, slider at absolute ±15%, headline no lower than assurance 299 and does not fit (349 reviews=69.8 h). Turn certify OFF: n=43, DR=43, 86 reviews, 17.2 h FITS. Adopt margin: green badge, panel gone, W1 and W4.
- [ ] **A5 / plan save/report:** Save, inspect folder and `plan_v1.json` inputs. Open `report.html`; print to PDF through browser; no missing elements/scripts/remote assets.
- [ ] **A6 / actuals:** For the scenario with planned n382 (use A2 plan), record reviewed382, issues11, agreement86%; observed ≈2.9%, margin ≈1.7%, W9. Confirm `actuals_v1.json`, report Actuals block and `plans_log.csv` Excel row.
- [ ] **A7 / next cycle:** Start next-month plan for same system. Banner shows prefill, expected p≈2.9% p_source `last_observed`, N blank.
- [ ] **A8 / Method:** 11/11 answer key passed; live arithmetic independently matches headline.
- [ ] **A9 / Quit/return:** Quit stops server; new launch reopens same configured local port.

## Defensive checks (supplement to owner list, not product features)

- [ ] No issue rates are silently clamped at limits; invalid fields block Save/Record.
- [ ] W7 shows impossible certification accurately yet preserves ability to save a **plan**, unless unrelated global integrity or workspace failure.
- [ ] Generate two versions of plan and actuals; compare older byte hashes unchanged.
- [ ] Confirm report is printable and log BOM opens in Excel with Unicode/multiline notes.
- [ ] Method integrity failure (intentional test only, not production editing) prevents save from UI and HTTP.
- [ ] No AI conversation content is entered or captured.

## Sign-off

Owner: ______________________   Date: __________  Version/tag: __________

Observed issues, evidence, and remediation: _______________________________________

## Codex cloud versus target-Windows evidence

A passing cloud (typically Linux) pytest suite is useful but **not** evidence of desktop behavior. Run all manual acceptance checks on the target Windows machine; keep any cloud-only result marked provisional until that happens. Do not approve release until owner signs off.
