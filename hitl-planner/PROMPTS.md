# HITL Sample Size Planner — 36 self-contained code-generation prompts

**Source:** `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` — v1.0, 34 pages. All prompts below can be pasted separately; each repeats the operating constraints, quotes the relevant specification sections, defines TDD checks, and **never requires reading another prompt**. Execute in numerical order **against the current committed repository**. Each step should be one Codex task and one reviewed, green change set.

Do **not** copy all prompts into the Codex at once. If you work on a phone, copy the standalone matching prompt in `prompts/` rather than scrolling through this master file.

## Prompt index

| Task | Phase | Goal | Spec |
|---|---|---|---|
| 01 | Foundation | Repository bootstrap, config, and health | §2.1–2.4, §8.1, §8.6, §9, §10 E7 |
| 02 | Foundation | Single-instance launcher and clean quit | §2.3, §9, §10 E6 |
| 03 | Statistics | Cochran and finite-population core | §4.1–4.3 F1–F3, §4.8, §11.1 K1–K3/K6, §11.2 |
| 04 | Statistics | Assurance, detection, and reverse maths | §4.3 F4/F8/F9/F10, §4.8, §11.1 K4/K5/K7/K8/K11 |
| 05 | Statistics | Headline, review counts, and capacity | §4.3 F5–F7, §4.8, §11.1 K10–K11, §11.2 |
| 06 | Statistics | Capacity-max trade-off engine | §4.4, §4.8, §11.1 K9 |
| 07 | Statistics | Nine-cell sensitivity service | §4.5, §11.2 |
| 08 | Interpretation | Plan warning rules W1–W7 | §5, §4.8, §11.2 |
| 09 | Interpretation | Seven reportable statements | §6, §4.7, §11.2 |
| 10 | Interpretation | Formatting and reproducible arithmetic | §4.7, §7.4, §8.2, §11.2 |
| 11 | Integration | Input validation and system-period identity | §3.1–3.3, §4.7, §10 E1, §11.2 |
| 12 | Integration | Validated Plan API as a single source | §9 POST /api/calc, §5, §6, §10 |
| 13 | Plan UI | Plan screen forms and debounce | §7, §7.1, §3.2–3.3 |
| 14 | Plan UI | Plan headline, warnings, statements | §7.1, §5–6, §4.7 |
| 15 | Plan UI | Live capacity what-if and Adopt | §4.4, §7.1, §11.6 items 2–4 |
| 16 | Plan UI | Sensitivity and assurance UI | §4.5, §7.1 |
| 17 | Persistence | Atomic file writes and safe names | §3.1, §8.1, §8.7, §10 E3/E5, §11.3 |
| 18 | Persistence | Immutable plan saves and versions | §3.1, §8.2, §8.7, §9, §11.3 |
| 19 | Persistence | Stand-alone printable HTML report | §8.4, §6–7, §11.3 |
| 20 | Plan UI | Plan save workflow and open actions | §7.1, §9 open-report/open-folder, §10 E9 |
| 21 | History | Read/list stored plans | §3.1, §7.2–7.3, §9 GET /api/plans and /api/plans/<id> |
| 22 | History | History filter, Load, report/folder UI | §7.3, §9 |
| 23 | History | Auto-complete and history prefill | §3.1–3.3, §4.6 next-cycle p, §9 systems/prefill, §11.3 |
| 24 | Actuals | Actuals calculations and W8–W10 | §4.6–4.8, §5 W8–W10, §11.2 |
| 25 | Actuals | Stateless Actuals calculation endpoint | §9 POST /api/actuals/calc, §10 E1 |
| 26 | Actuals | Versioned actuals plus report regeneration | §3.1, §8.3–8.4, §9, §11.3 |
| 27 | Actuals | Actuals complete browser tab | §7.2, §4.6, §9 |
| 28 | Persistence | Generated plans_log.csv and rebuild API | §8.5, §9 GET /api/log/rebuild, §11.3 |
| 29 | History | History consistency and corrupt-file handling | §7.3, §8.5, §10 E4, §11.3 |
| 30 | Method | Method API and live educational tab | §7.4, §9 GET /api/method, §4.1–4.3 |
| 31 | Safety | Immutable answer key and startup gate | §2.3 --selftest, §7.5, §11.1, §11.5, §10 E8 |
| 32 | Safety | Failures, workspace health, and JSON error resilience | §8.6–8.7, §10 E1–E10, §9 |
| 33 | Safety | Multi-tab consistency, race safety and launcher regression | §2.3, §3.1, §4.8, §8.7, §10 E5/E6 |
| 34 | Quality | Offline desktop fit, polish, and accessibility | §2.1, §7.1–7.4, §10 |
| 35 | Quality | Full automated integration and contract audit | §11.1–11.5, §4–10 |
| 36 | Release | Manual acceptance, documentation, and release | §11.6, §12–13, Appendix B |


For cloud Codex, review and merge each green task before creating the next task. A PR alone is not completion. Codex will not automatically inherit files from this ChatGPT conversation; put this kit in the connected repository.

---

# Implementation task 01 — Repository bootstrap, config, and health

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Repository bootstrap, config, and health
Authoritative sections: §2.1–2.4, §8.1, §8.6, §9, §10 E7

Implementation scope:
Create the smallest genuinely runnable Python 3.11 desktop Flask application. Add `hitl_planner.py`, `test_hitl_planner.py`, `requirements.txt` (Flask only), `requirements-dev.txt` (pytest only), and a succinct startup README if not present. Serve a static locally defined HTML page at `/` with project title and a clear "not yet available" placeholder, and `GET /api/health` with `{tool,version,workspace_ok}`. Use Flask's test client. Load or atomically create `config.json` next to the script with schema_version 1, workspace default `Path.home()/Documents/HITL Planner`, port provisionally 5062. Create workspace on first run. If config is malformed, missing keys, or cannot be read, print one line and exit 2; never overwrite a bad config. Config and workspace paths must be Windows-safe, and environment-independent in tests. No fake statistics, fake answer-key passes, or fake final UI.

Tests to write FIRST:
Red: root and health responses, config-created-on-first-run, config-preserved, corrupted/missing-key config exits 2, tmp workspace isolation, HTTP without outside resources. Green: minimal app factory that accepts injectable config/workspace, source-of-truth constants, explicit main guard. Ensure importing module has no side effects; do not open browser during tests.

Acceptance condition:
`python -m pytest -q` passes; a manual local launch shows the page; `config.json` is ignored by git; no other runtime modules or network dependencies.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 02 — Single-instance launcher and clean quit

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Single-instance launcher and clean quit
Authoritative sections: §2.3, §9, §10 E6

Implementation scope:
Implement the Windows launch lifecycle in `hitl_planner.py`. On `python hitl_planner.py`, read config, check configured port on 127.0.0.1: if `/api/health` identifies this tool, open its URL in the default browser and exit 0. If any other service occupies the port, print a concise error naming the port and config.json; exit 2. If free, start a controllable local server only on 127.0.0.1, open browser, and respond to Ctrl-C. Implement POST `/api/quit` returning `{ok:true}` then cleanly stopping this process. Avoid relying on deprecated/missing Werkzeug request-environ shutdown hooks. Do not bind to 0.0.0.0. Include Quit button on the basic shell.

Tests to write FIRST:
Test correct occupied-port classification using monkeypatched health/probes and a temporary socket, correct host binding, clean shutdown in a real subprocess/local test, browser-opening mocked, and Ctrl-C path. Tests may use ephemeral ports; avoid interacting with real port 5062 in automated tests.

Acceptance condition:
Launcher supports free/same-tool/foreign-port states; quit actually stops server; all endpoints stay localhost only.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 03 — Cochran and finite-population core

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Cochran and finite-population core
Authoritative sections: §4.1–4.3 F1–F3, §4.8, §11.1 K1–K3/K6, §11.2

Implementation scope:
Implement exact Z constants `{0.90:1.645,0.95:1.960,0.99:2.576}`, `ceil_safe(x)=ceil(round(x,9))`, F1 effective margin (absolute E_abs or relative r*p), F2 base Cochran n0, and F3 finite population-corrected `n_cochran=ceil_safe(n0/(1+(n0-1)/N))`. Capture raw unrounded intermediates for audit. Centralize the statistical functions inside the one application file; never use SciPy or more precise Z values. Handle N=1 and n never exceeding N. Expose these functions only through an internal calculation entry point now, not an incomplete public API.

Tests to write FIRST:
Write failing tests first: K1 (N 1000000 C .95 E .05 p .5 -> 385), K2 (N 5000 ->357), K3 (N 1000000 C .99 E .03 ->1840), K6 (N 20000 C .95 p .04 relative .25 ->1374); `ceil_safe(356.0000000004)=356`, `ceil_safe(356.0000001)=357`; N=1 census; absolute/relative equivalence. Assert raw intermediary values within documented precision.

Acceptance condition:
All four key cases and edge tests green, with precise constants and unchanged fixtures.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 04 — Assurance, detection, and reverse maths

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Assurance, detection, and reverse maths
Authoritative sections: §4.3 F4/F8/F9/F10, §4.8, §11.1 K4/K5/K7/K8/K11

Implementation scope:
Implement F4 exact assurance `ceil_safe(log(1-C)/log(1-T))`; F8 detection `1-(1-T)**n`; F9 achieved reverse margin `Z*sqrt(p*(1-p)/n * (N-n)/(N-1))` returning 0 if n>=N or N=1; F10 inverse certification threshold `1-(1-C)**(1/n)` and an explicit n=0 n/a result. Preserve raw assurance values. Do not impose artificial population clipping on n_assure: infeasibility is handled later.

Tests to write FIRST:
Red-first K4: .95/.01 ->299; K5 n200 T.01 -> .8660 (display later); K7 N5000 n357 p.5 C.95 -> .0500 at 4 dp; K8 n120 C.95 -> .0247 at 4 dp; K11 C.95 T.001 ->2995 and larger than N2000. Add n>=N, N=1, n=0 tests, monotonicity tests for power and inverse bounds.

Acceptance condition:
Five answer-key cases pass; no undefined division or math exceptions in the required edges.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 05 — Headline, review counts, and capacity

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Headline, review counts, and capacity
Authoritative sections: §4.3 F5–F7, §4.8, §11.1 K10–K11, §11.2

Implementation scope:
Wire a coherent plan calculation from the existing mathematical helpers. F5: with certify on and n_assure<=N choose max(n_cochran,n_assure); otherwise n=n_cochran; binding assurance only when feasible and strictly larger than n_cochran, cochran on ties. F6 double reviews: `DR=min(n,max(F,ceil_safe(s*n)))`. F7 reviews=n+DR, hours=reviews*M/60, capacity=S*H; `fits(a,b)` means a<=b+1e-9 with unrounded numbers. Return named values suitable for API/report reuse; preserve n_assure even when infeasible. No HTTP calculations or duplicate arithmetic.

Tests to write FIRST:
Red: binding cases assurance/cochran/tie/certify-off/W7 condition; K10 DR(40)=40 DR(400)=60 at s=.15 F50; DR=0 with s=F=0; DR<=n; equality fits and just-above capacity fails; N1. Assert return data contains n, binding, reviews, hours, capacity, verdict.

Acceptance condition:
Integrated pure calculation yields one authoritative source for reviews/capacity; no UI or persistence yet.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 06 — Capacity-max trade-off engine

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Capacity-max trade-off engine
Authoritative sections: §4.4, §4.8, §11.1 K9

Implementation scope:
Implement monotone largest-fitting-sample search for `n_max` in `[0,min(N,floor(capacity*60/M+1e-9))]`, using exactly the F6/F7 shared hours and fits helpers. Binary search is preferred; verify maximality with n_max+1. Return double-review count, total reviews, precise hours, F9 margin at capacity, optional relative margin, F10 threshold. n_max=0 must return no margins and explicit "no reviews" state. Generate trade-off only when headline DOES NOT FIT, never fabricate feasible certification.

Tests to write FIRST:
Red-first K9: N50000 S3 H8 M12 s.15 floor50 p.5 C.95 => n_max70, DR50, reviews120, hours24, next 71 does not fit, margin ~.1171, threshold ~.0419. Include 0 capacity (test via search helper even though form hours>0), extreme floor, max population, exact equality, n_max never exceeds N.

Acceptance condition:
K9 and boundary tests green; trade-off is driven by the same hours logic as headline.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 07 — Nine-cell sensitivity service

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Nine-cell sensitivity service
Authoritative sections: §4.5, §11.2

Implementation scope:
Implement 3x3 sensitivity grid as pure Python-derived data: absolute margins .03/.05/.10 or relative .10/.25/.50 crossed with confidence .90/.95/.99. For each cell run the same F1–F7 headline and assurance logic with unchanged other plan inputs. Return n, DR, hours, fits, binding, an "A" indicator only when assurance strictly binds, and exact current-confidence-and-margin highlighting (none for custom margin). No duplicate sample-size implementation.

Tests to write FIRST:
Red: always exactly nine cells in correct mode, 90/95/99 confidence, cell value matches independent main calculation at matching inputs, certify-off has no A, certify-on may bind, custom values highlight none, equality highlight works, correct ordered cells.

Acceptance condition:
Sensitivity results are deterministic and use the same core calculator as primary results.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 08 — Plan warning rules W1–W7

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Plan warning rules W1–W7
Authoritative sections: §5, §4.8, §11.2

Implementation scope:
Implement structured warning objects `{code,severity,message}` for W1–W7. Exact triggers: W1 effective E>.10; W2 p==.50 AND no observed history for system (not keyed solely to p_source); W3 absolute mode and E>=p; W4 DR<F due to n cap; W5 N<200; W6 n>.8*N; W7 certify on and n_assure>N (red). All warnings are advisory for saving including W7; keep literal code, severity and human message from spec. Make observed-history existence an explicit dependency resolved server-side when persistence arrives; until then pure warning function receives boolean.

Tests to write FIRST:
Write boundary tests inside/outside for all seven, including W1=.1/.1001, W5=199/200, W6 exact .8N vs above, W3 equality, W4 n<F, W2 with rate history even p=.5, W7 feasible/infeasible, W5+W6 together. Assert no duplicate codes and W7 red.

Acceptance condition:
Warnings are emitted from the core service, not re-created in front-end JS.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 09 — Seven reportable statements

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Seven reportable statements
Authoritative sections: §6, §4.7, §11.2

Implementation scope:
Implement exactly seven ordered S1–S7 statements generated by Python from plan calculations, system, and period display. Mirror §6 wording and switches: S1 absolute/relative, S2 feasible certifying / infeasible W7 / certify off, S3 power, S4 period/system limit, S5 no subgroup precision, S6 true random selection, S7 issues not severity. Store a plain ordered seven-element list ready for API/JSON/report. Escape only at HTML rendering boundaries; plain saved JSON retains text.

Tests to write FIRST:
Red: always seven, one S1 per margin mode, three S2 variants, S3 threshold and power inserted correctly, S6 explicit random selection and N, correctly formatted month and ISO week, 0.25% rendered to 2 decimals, thousands grouping.

Acceptance condition:
Statement service is reusable in the Plan tab and persisted reporting; it contains all disclaimers.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 10 — Formatting and reproducible arithmetic

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Formatting and reproducible arithmetic
Authoritative sections: §4.7, §7.4, §8.2, §11.2

Implementation scope:
Implement common Python-side presentation/formatting helpers and a detailed live arithmetic trace: Z, effective E, n0, finite corrected raw/result, assurance raw/result, binding/headline, DR, reviews, hours, capacity, exact verdict and detection power. Carry machine-precision numeric fields separately from human display strings; only the latter round. Percentages normally 1 dp but rates and thresholds <1% use 2 dp. Hours/capacity 1 dp; counts separated by thousands. Ensure all numbers in a saved method trace can be reproduced.

Tests to write FIRST:
Red: 0.0025->"0.25%", .0288->"2.9%", n=12345->"12,345", hours=88->"88.0", calculation trace exact sequence and contains raw and rounded intermediate values; display rounding never changes verdict at tight boundary.

Acceptance condition:
Trace and formatting are invoked by the existing calculation pipeline and consumed by future Method/report views.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 11 — Input validation and system-period identity

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Input validation and system-period identity
Authoritative sections: §3.1–3.3, §4.7, §10 E1, §11.2

Implementation scope:
Build centralized validation for I1–I15 and actual date labels. Required: month/week with valid YYYY-MM or ISO YYYY-Www, system 1–60 chars, N>=1 int, confidence in .90/.95/.99, absolute/relative, margin abs .005–.25 or relative .05–.50, p .001–.999, SME count>=1, net hours>0, minutes>0, DR share [0,1], DR floor int>=0, certify bool, threshold .0001–.50. API inputs are decimals, UI inputs visually percentages; refuse out-of-range values with per-field errors, never clamp. Provide default initial form state with statistical defaults; N/S/H/M remain empty. Period defaults use local date; no carried-over N.

Tests to write FIRST:
Red: both ends and just outside every numeric limit, invalid non-finite numbers, booleans masquerading as integers, invalid ISO week including week 53 where invalid, malformed month, blank fields and system length, missing dict keys, unknown fields safely handled, valid exact endpoints. `validate_plan` returns typed normalized fields or `{field:reason}` without mutating inputs.

Acceptance condition:
All entry points can reuse validation, and tests prove bad inputs never reach statistics.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 12 — Validated Plan API as a single source

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Validated Plan API as a single source
Authoritative sections: §9 POST /api/calc, §5, §6, §10

Implementation scope:
Implement `POST /api/calc` using plan validation, integrated numerical pipeline, W1–W7, S1–S7, sensitivity, trade-off, and arithmetic. Success returns `{outputs,warnings,statements,arithmetic}` matching spec semantics; invalid data returns 400 with `errors` keyed per form field. Stateless calculation, no disk writes; compute W2 from available observed-rate history when that service exists, otherwise use deterministic none-observed behavior. No statistics performed by JavaScript. Add predictable JSON error shape for malformed JSON. Make all calculations callable directly from tests.

Tests to write FIRST:
Red: Flask test client success with acceptance scenario N50000,p.5,C.95,E.05,S3,H8,M12,s.15,F50,T.01 -> n382 DR58 88.0h DOES NOT FIT, n_max70; 400 invalid with multiple field errors; no file changes after 20 calc calls; seven statements/nine cells/warnings complete; ensure no rounding used in `fits`.

Acceptance condition:
First fully integrated calculation API works independently of UI and saving.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 13 — Plan screen forms and debounce

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Plan screen forms and debounce
Authoritative sections: §7, §7.1, §3.2–3.3

Implementation scope:
Replace placeholder page with simple desktop-only four-tab shell and fully labeled Plan form, grouped as Identity, Population and precision, SME capacity, Double review/certify. Plan controls match I1–I15; system datalist is local; confidence dropdown, month/week picker, margin segmented mode, preset or custom margin, live capacity labels, tooltips, p_source tag. Required unfilled inputs are visibly highlighted, disabled Save and grayed result placeholder. Use small inline JS to POST `/api/calc` after about 150ms idle and render server-provided field errors; manage out-of-order responses so stale responses cannot repaint. Keep other tabs minimal, clearly not functional yet; no unimplemented controls presented as working.

Tests to write FIRST:
Red/green via Flask page smoke tests for all I1–I15, no external script/style tags; static inspection of JS for debounce and no math formulas; manual keyboard entry verifies fields, toggles and disabled state; API tests unchanged. Do not add a UI test framework.

Acceptance condition:
Plan form drives validated live server calculations; it never computes sample sizes in the browser.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 14 — Plan headline, warnings, statements

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Plan headline, warnings, statements
Authoritative sections: §7.1, §5–6, §4.7

Implementation scope:
Wire the Plan outputs column to render API-returned warning banners, sample headline and FITS/DOES NOT FIT badge, n + DR review subtotal, hours/capacity, and binding explanation. Show S1–S7 in grouped Can say/Can't say sections. Render server-provided data and formatted strings; no duplicated JS formulas. Gray-out on invalid input and prevent stale/successful response from enabling an invalid Save. Keep content present through keyboard-only operation.

Tests to write FIRST:
Test HTML container IDs and response mapping, Flask API acceptance numbers, W7 red and W1 advisory yellow, mutually exclusive binding copy, exactly seven statements in DOM when valid. Manual simulate editing after valid state then clearing N.

Acceptance condition:
The complete headline and interpretation flow works for live inputs.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 15 — Live capacity what-if and Adopt

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Live capacity what-if and Adopt
Authoritative sections: §4.4, §7.1, §11.6 items 2–4

Implementation scope:
Implement trade-off panel visible ONLY if headline DOES NOT FIT: show n_max, DR/reviews/hours, attainable E and inverse T, explicit zero-capacity message. Add what-if margin slider absolute 2–15% step .5%, relative 5–50% step 1%; initialize to current margin when panel opens, and send candidate to Python `/api/calc` for live recalculation WITHOUT mutating the form. Show candidate n, DR, hours, fit verdict and assurance-binding limit. "Adopt this margin" writes chosen slider value into I7, triggering normal recalculation; panel vanishes if fit. Keep slider state separate from plan until Adopt. Do not replace certifying math with Cochran-only.

Tests to write FIRST:
Tests of unchanged form value while moving slider, adopted value on click, relative/absolute endpoints, inability to go below n_assure with certify on, K9 read-out and §11.6 example with certify off n43 DR43 ->17.2h; manual browser check panel hides upon fit.

Acceptance condition:
What-if behavior is integrated with authoritative Python calculator; no independent JS statistics.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 16 — Sensitivity and assurance UI

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Sensitivity and assurance UI
Authoritative sections: §4.5, §7.1

Implementation scope:
Render the server-computed 3x3 sensitivity grid with confidence headings, margin rows, n + SME hours per cell, green/red fit styling, "A" for assurance binding, and current-input highlight when exact cell exists. Add assurance card with n_assure and applicable feasible/infeasible wording, detection-power sentence regardless of certify toggle. Keep the card red for W7 and never suggest feasibility when n_assure>N. Grid switch absolute/relative and retained model result when other inputs change.

Tests to write FIRST:
Test nine visible cells and 90/95/99 headings, relative mode labels, custom-margin no highlight, a binding cell shows A, W7 assurance is red, detection power shown even when certify off; API tests compare one cell to direct calculation.

Acceptance condition:
Plan tab now supports every numerical exploratory decision specified.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 17 — Atomic file writes and safe names

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Atomic file writes and safe names
Authoritative sections: §3.1, §8.1, §8.7, §10 E3/E5, §11.3

Implementation scope:
Implement all persistence primitives before save routes: workspace path from config, safe plan folder names `<period> - <sanitised system>`, sanitize prohibited Windows `<>:"/\|?*`, ASCII control chars, whitespace, dot/space edges, length 60, reserved names CON/PRN/AUX/NUL/COM1–9/LPT1–9; collision suffix `(2)` etc if saved JSON identifies a different system. Prevent path traversal and confine every requested file to configured workspace. Implement atomic UTF-8 JSON/text/CSV write temp within same folder then `os.replace`, with cleanup on failure and never overwrite immutable version files. Handle a missing workspace and I/O exceptions with useful error.

Tests to write FIRST:
Red: sanitized `A/B: "C" -> AB C`, `CON -> CON_`, empty invalid, control chars, collision `(2)`, `..`/traversal blocked, atomic failure retains old content and removes tmp, Unicode JSON retains characters, folder naming date-first.

Acceptance condition:
Primitives are called by a real lightweight save/reload integration in tests, not left as unattached utilities.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 18 — Immutable plan saves and versions

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Immutable plan saves and versions
Authoritative sections: §3.1, §8.2, §8.7, §9, §11.3

Implementation scope:
Implement `POST /api/plans`: server-side revalidate and recalculate every plan field, derive period display/plan_id, set schema_version, tool version/method version, timestamp with local UTC offset, inputs plus p_source/prefilled_from, all outputs, warnings, seven statements, constants, formulas, arithmetic, integrity status. Save `plan_v<N>.json` with N=max(existing)+1 computed at save time. Never overwrite any existing `plan_vN`. Return `{plan_id,version,folder,report_path}` (report path populated as soon as report generation exists, or integrate a minimal immediately generated report in this step). Plan can save with W7. Ensure tampered client outputs are ignored. Saving same plan again increments version.

Tests to write FIRST:
Red: two saves create v1 and v2; v1 hash/bytes remain identical; reload object matches `/api/calc` outputs; W7 allowed to save; timestamps offset-aware; two browser requests cannot silently overwrite each other; bad inputs 400; save does not depend on browser-calculated output.

Acceptance condition:
Versioned JSON is the immutable single source of truth and functional POST route is tested.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 19 — Stand-alone printable HTML report

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Stand-alone printable HTML report
Authoritative sections: §8.4, §6–7, §11.3

Implementation scope:
Generate `report.html` on each successful plan save from latest saved JSON (not untrusted form state). Use only inline CSS, static HTML, no scripts/fonts/images from external URLs, with A4 print stylesheet and sensible page breaks. Sections ordered: header with plan/version/timestamps/tool/method; inputs; headline and verdict; trade-off if needed; 3x3 grid; assurance/detection; seven statements; warnings; step-by-step arithmetic; formulas/constants; references; Actuals section only when actuals later exist. Escape system and user notes so HTML is safe. Rebuild report atomically and preserve immutable JSON as source.

Tests to write FIRST:
Test report exists after save; contains plan ID and all seven exact strings, no `<script`, no `http://` or `https://`, usable `<style>` print rules, input containing `<>&` safely escaped, saving v2 reflects newest version. Human print-to-PDF smoke check on Windows.

Acceptance condition:
Plan save response has working `report_path`; regenerated HTML is independent and printable offline.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 20 — Plan save workflow and open actions

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Plan save workflow and open actions
Authoritative sections: §7.1, §9 open-report/open-folder, §10 E9

Implementation scope:
Wire Save button to `POST /api/plans` with currently validated Plan inputs. Show success toast with actual plan_id/version and working "Open report" / "Open folder" actions. Implement POST `/api/open-report` and `/api/open-folder` accepting plan_id and resolving only within workspace to existing saved resources. On Windows use `os.startfile`, mock safely in tests; opening failure yields yellow toast with absolute file path and `{ok:false,path}`, never crashes page. Keep Save enabled for additional edited version after a successful save; always recalculate before saving.

Tests to write FIRST:
Test Save disabled on errors and enabled on valid data; second Save increments version; endpoint 404 for missing plan_id, rejects `../` and separators; mocked successful os.startfile and failure response. Browser test click Save and both open actions.

Acceptance condition:
User can complete a Plan-tab workflow including durable save and local report launch.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 21 — Read/list stored plans

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Read/list stored plans
Authoritative sections: §3.1, §7.2–7.3, §9 GET /api/plans and /api/plans/<id>

Implementation scope:
Implement `GET /api/plans` list and `GET /api/plans/<plan_id>` latest plan and latest actuals if present. Scan workspace folders, recognize latest version numerically, map saved_at dates, sort newest-first for dropdown as appropriate, and include identity/n/hours/verdict/warning codes plus an unreadable field for corrupt folders. Do not trust folder names as the system truth. Do not delete or overwrite corrupt records. For unknown ID respond 404. Keep safe ID containment.

Tests to write FIRST:
Red: three plans with multiple versions, highest numeric version selected (`v10` > `v9`), no accidental modification, corrupt JSON produces unreadable row, unknown returns 404, endpoint output contracts and data sourced from JSON. Validate local case-preserving system identity.

Acceptance condition:
History and Actuals dropdown can rely on one tested read model.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 22 — History filter, Load, report/folder UI

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: History filter, Load, report/folder UI
Authoritative sections: §7.3, §9

Implementation scope:
Build fully functional History tab table (newest period first) sourced from `GET /api/plans`, including period, system, version, saved-at, sample, hours, verdict, warnings, actuals present, observed rate and achieved margin. Add case-insensitive substring filter. Per normal row implement Load (loads saved Plan inputs including N and saved period; switches to Plan), Report and Folder using secure open routes; show unreadable rows with explanation and no actions. Explicitly no delete. Make date sorting deterministic even with month/week periods.

Tests to write FIRST:
Browser tests or lightweight JS tests without new npm dependencies: filter case-insensitive, Load reconstructs 15 inputs/p_source, period preserved rather than replaced, version shown, unreadable row actionless. Flask tests ensure listing sorted and valid URL-safe IDs.

Acceptance condition:
Previously saved plans can be found, reopened, and reused through the live Plan form.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 23 — Auto-complete and history prefill

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Auto-complete and history prefill
Authoritative sections: §3.1–3.3, §4.6 next-cycle p, §9 systems/prefill, §11.3

Implementation scope:
Implement `GET /api/systems` and `GET /api/prefill?system=...`, matching trimmed case-insensitive saved `system` field, not sanitized folder names. Find latest plan by `saved_at` across all periods; latest actuals by `recorded_at`. Return I1/I5–I7/I9–I15 from latest plan; I8 from latest observed issue rate floored at 0.001, else latest planned p, with `p_source` last_observed or last_planned; never prefill N, reset period label to current local period. Preserve manually edited inputs during async prefill; include informative source banner with version and optional recorded-at, and systems list in datalist. Record p_source values default/manual/last_observed/last_planned and `prefilled_from` on save.

Tests to write FIRST:
Red: unknown system `{}`, whitespace/case-insensitive matching, multiple months with timestamp ordering distinct from period, N always blank, zero observed rate floors to .1%, no actuals uses last planned, 50% with observed history suppresses W2, manual edits not overwritten by late prefill, no corrupt record contamination.

Acceptance condition:
New period can start from previous observations while never inventing current population.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 24 — Actuals calculations and W8–W10

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Actuals calculations and W8–W10
Authoritative sections: §4.6–4.8, §5 W8–W10, §11.2

Implementation scope:
Implement pure actuals calculation keyed to a specific saved plan version. Validate reviewed integer 1…N, issues integer 0…reviewed, agreement 0–1 decimal, notes free text. Return observed rate issues/reviewed. For 0<obs<1 calculate reverse margin F9 with p=obs (plus relative margin when planned mode relative); for zero issues return no margin and `true rate below T_at(reviewed)` C-bound; for all issues return no margin and `true rate above 1-T_at(reviewed)`; certification statuses: off not planned; on with issues>0 not applicable; on with zero issues met if inverse threshold<=T else not met. W8 reviewed<n_planned, W9 obs>2*p_planned OR obs<.5*p_planned (strict inequalities), W10 agreement<.80. Return planned-vs-actual comparison for report.

Tests to write FIRST:
Red: zero/one/all issue cases, n=1 and census, relative margin, W8/W9/W10 strict edge pairs (agreement .8 vs .799, observed exactly x2/x.5), certification met/not met/not planned/issues found, invalid counts/error-map, no modification to referenced plan.

Acceptance condition:
All actuals metrics reuse F9/F10 and are correctly interpretable in extreme outcomes.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 25 — Stateless Actuals calculation endpoint

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Stateless Actuals calculation endpoint
Authoritative sections: §9 POST /api/actuals/calc, §10 E1

Implementation scope:
Implement `POST /api/actuals/calc` accepting `{plan_id, reviewed, issues, agreement, notes}` and optional explicit plan_version only if compatible with the plan selection UI; load referenced immutable plan server-side and invoke actuals service. Success JSON `{outputs,warnings}`; invalid field values return 400 with field errors; missing/corrupt plan return consistent 404/error. No save side effects. Source confidence/N/threshold/mode/n_planned from saved plan, never from client-supplied forged stats.

Tests to write FIRST:
Flask client tests for full scenario: plan N50000 n382 p.5; reviewed382, issues11, agreement .86 -> ~2.9% observed and ~1.7% achieved, W9, certification not applicable; zero-issue bound; invalid notes type; 404 and no file changes after calc.

Acceptance condition:
Actuals can be previewed and validated before committing a record.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 26 — Versioned actuals plus report regeneration

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Versioned actuals plus report regeneration
Authoritative sections: §3.1, §8.3–8.4, §9, §11.3

Implementation scope:
Implement POST `/api/plans/<plan_id>/actuals` to validate actuals, lock in reference to selected plan version, compute outputs/W8–W10, and atomically create immutable `actuals_v<N>.json` with offset-aware recorded_at and tool/schema/method version. Version increments on subsequent recordings; never edit existing actuals or plan files. Recreate report.html using latest plan and latest actuals; actuals block includes observed rate/achieved margin or bound, planned-vs-actuals, certify, agreement, notes and warnings. Update GET plan detail to return latest actuals for relevant version; maintain clear reference semantics if plan_version differs.

Tests to write FIRST:
Red: v1 and v2 actuals, v1 bytes unchanged, correct plan_version persisted, latest report contains Actuals plus notes properly escaped, zero-issues bounds, 400/404, simulated write failure leaves JSON immutable and surfaces recoverable report error. No duplicate statistics.

Acceptance condition:
Actuals recording is durable and immediately visible in latest report and read API.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 27 — Actuals complete browser tab

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Actuals complete browser tab
Authoritative sections: §7.2, §4.6, §9

Implementation scope:
Implement Plan dropdown newest first with saved-at/verdict/latest version; selected plan shows read-only planned sample, DR, margin, threshold, p and N. If actuals exist show last entry read-only plus "Record again" to create a version. Editable form reviewed/issues/agreement visually %, notes; live server calculation via POST `/api/actuals/calc` with validation error rendering, observed rate, achieved margin or bound, certify status, planned-vs-actual table and warnings. Save actuals to POST route and show versioned toast/open-report action. Never collect conversation content.

Tests to write FIRST:
Browser acceptance: record reviewed382 issues11 agreement86% -> ~2.9% obs/~1.7% margin/W9; Record again makes v2; invalid reviewed>N disables save; zero issues bound instead of NaN; show agreement warning below 80%, plan summary immutable while entering actuals.

Acceptance condition:
End user can finish a Plan→Actuals cycle from the browser alone.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 28 — Generated plans_log.csv and rebuild API

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Generated plans_log.csv and rebuild API
Authoritative sections: §8.5, §9 GET /api/log/rebuild, §11.3

Implementation scope:
Implement pure workspace scan to rebuild `plans_log.csv` from readable immutable JSON on every plan/actuals save and GET `/api/log/rebuild`. One row per folder using latest plan and latest actuals; exact 43-column order in spec §8.5, sorted period_label descending then system ascending; `utf-8-sig` Excel BOM; standard `csv` quoting; warnings codes separated by semicolon; actuals cells empty when none; unreadable folders skipped with console warning. Write CSV atomically, never append or let it supersede JSON. If log rebuild fails after an immutable record saved, report partial success clearly and support explicit rebuild—do not claim save was rolled back.

Tests to write FIRST:
Red: three plans, one with actuals -> three rows, correct header names/order, UTF8 BOM, commas and multiline notes round-trip, W2;W6, deterministic sorting, no blank extra rows, re-running rebuild idempotent, corrupt folder skipped, retry after simulated failure, route returns `{path,rows}`.

Acceptance condition:
CSV is reliable derived read model for spreadsheet inspection and history.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 29 — History consistency and corrupt-file handling

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: History consistency and corrupt-file handling
Authoritative sections: §7.3, §8.5, §10 E4, §11.3

Implementation scope:
Wire History tab's extra actuals columns and sort/filter semantics to the same read model as generated `plans_log.csv`. Ensure corrupt JSON folders render an "unreadable — error" placeholder (no actions), are omitted from prefill/system suggestions/log, and remain unchanged on disk. Keep stale report/log failure visually visible without failing unrelated read operations; make rebuild API repair derived CSV. Latest-version selection and newest-period sort must be deterministic.

Tests to write FIRST:
Regression tests: corrupt plan, corrupt latest actuals, mixed valid/invalid folders, byte-for-byte preservation, three-row log excluding broken record, case-insensitive system matching, history and CSV agree on displayed numerical fields and warning codes.

Acceptance condition:
History, log, and prefill consistently reflect readable source records without silent data loss.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 30 — Method API and live educational tab

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Method API and live educational tab
Authoritative sections: §7.4, §9 GET /api/method, §4.1–4.3

Implementation scope:
Implement GET `/api/method` with constants/formulas F1–F10, assumptions and integrity status (which may be marked pending until automated startup check is integrated), method version 1.0 and tool version 1.0.0. Render Method tab: 11-case status, exact rounded Z table, each F1–F10 with terms explained, assumptions from §7.4, per-plan live arithmetic already calculated server-side, Cochran/Hanley & Lippman-Hand references. Update tab from successful Plan calculation responses. Avoid displaying "11/11 passed" before check really ran.

Tests to write FIRST:
Test all ten formula identifiers and exact constants are in JSON and tab; math trace matches n382 scenario; relative margin trace, method version, references, no external links or dependencies. Manual Method tab while editing Plan shows matching n/DR/hours.

Acceptance condition:
Auditor can reproduce the output and read assumptions directly from UI.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 31 — Immutable answer key and startup gate

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Immutable answer key and startup gate
Authoritative sections: §2.3 --selftest, §7.5, §11.1, §11.5, §10 E8

Implementation scope:
Implement all 11 answer-key K1–K11 as self-contained shared assertions against pure application math; use EXACT constants/expected values from spec. `python hitl_planner.py --selftest` prints one PASS/FAIL per case and exits 0 only if all pass, before server launch. At every normal startup run same key and cache integrity status. On any failure print failing identifiers, show red all-tab banner, disable `POST /api/plans` and actuals recording server-side even for forged clients, disable Save and Record UI; leave calculation and Method available with untrusted warning. Expose status via GET `/api/method`. NEVER 'fix' case failures by editing expected numbers.

Tests to write FIRST:
Test selftest process prints 11 PASS lines and exit0; monkeypatch bad Z or function -> failing case list and exit1; startup method failure banner, direct save/actuals POST rejected, old records left intact; intact calculation passes 11/11. No fake flags.

Acceptance condition:
Statistical integrity becomes an enforceable runtime gate, not a cosmetic label.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 32 — Failures, workspace health, and JSON error resilience

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Failures, workspace health, and JSON error resilience
Authoritative sections: §8.6–8.7, §10 E1–E10, §9

Implementation scope:
Harden each endpoint and UI errors according to E1–E10. Unexpected exceptions log full traceback to console but return JSON 500 `{error:"Unexpected error",details:"<type>"}`, no stack trace in browser. Invalid data 400 with field errors; workspace not writable/drive full sets global red banner and GET health workspace_ok=false; Record/Save disabled until retry succeeds; atomic temp files cleaned and immutable records unaffected. Bad config exits 2 (never reset). Failed os.startfile gives yellow manual-path toast. Corrupt records excluded from derived data. Preserve usable UI after a failed API response; never suggest unsaved work was saved.

Tests to write FIRST:
Force 400/404/500, bad JSON content, malformed config, read-only workspace, disk failure on report vs JSON, stale workspace recovery and health flag, `.tmp` cleanup, warnings preserved, rendered error contains no traceback. Regression `python -m pytest -q` and --selftest green.

Acceptance condition:
All required failure modes have deterministic recoverable responses.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 33 — Multi-tab consistency, race safety and launcher regression

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Multi-tab consistency, race safety and launcher regression
Authoritative sections: §2.3, §3.1, §4.8, §8.7, §10 E5/E6

Implementation scope:
Exercise and close gaps in simultaneous browser tabs and repeated saves: calculate remains stateless, versions determined from disk on save, two saves cannot overwrite/collide even when requests land close together; provide internal synchronization suitable for one-process Flask. Check folder collision naming consistently uses saved JSON system. Re-verify same-tool single-instance and foreign port exit2, local-only binding, Quit and Ctrl-C, printing only expected health responses. Do not introduce external database, locking dependency, or user login.

Tests to write FIRST:
Test concurrent saves via test client/threads isolated temp workspace create v1/v2 with no lost data; same-name collision gets suffix; two independent calc calls have no global state pollution; subprocess launcher free/reuse/conflict and clean quit; original versions checksum unchanged.

Acceptance condition:
The specified single-user, multi-tab usage cannot silently destroy saved work.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 34 — Offline desktop fit, polish, and accessibility

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Offline desktop fit, polish, and accessibility
Authoritative sections: §2.1, §7.1–7.4, §10

Implementation scope:
Polish single embedded desktop HTML/CSS/JS app using light system-font cards consistent with existing Pareto/IMR screenshots or CSS ONLY if actually available in workspace. Do not fabricate reuse. Four tabs and Quit at right, responsive enough for Windows desktop but no mobile redesign. Ensure input labels/tooltips, visible focus, warnings not distinguished by color alone, readable tables/print mode, consistent percentage formatting, success/error toasts with understandable text, debounce cancellation/stale response guard, local assets only. Avoid any added statistical feature or new tabs.

Tests to write FIRST:
Static test scans root HTML/report for CDN and external HTTP assets; browser verify keyboard tabbing, focus, tooltips, no horizontal overflow at typical desktop widths, all badges legible, invalid fields and global banner visible, print-to-PDF preview legible.

Acceptance condition:
User-facing experience is stable, offline, understandable and faithful to spec.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 35 — Full automated integration and contract audit

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Full automated integration and contract audit
Authoritative sections: §11.1–11.5, §4–10

Implementation scope:
Build final integration/regression tests that follow a complete lifecycle: config -> plan calculation -> save v1/v2 -> report -> History -> prefill -> Actuals calc/save v1/v2 -> report -> generated CSV -> Method -> integrity -> quit. Construct source-to-test coverage matrix of every I1–I15, F1–F10, K1–K11, W1–W10, S1–S7, all §9 endpoints, E1–E10. Address any uncovered boundary; do not expand scope. Confirm `--selftest` startup and pytest are both green; no test modifies real workspace/config. Check v2-excluded features aren't accidentally present.

Tests to write FIRST:
Run `python -m pytest -q`, `python hitl_planner.py --selftest`, and portable smoke tests; capture commands and results in docs. Verify 11 key cases unchanged, equality boundaries, HTML offline, CSV BOM, immutable JSON hashes, path traversal prevention, atomic recovery.

Acceptance condition:
Every stated test category has explicit passing evidence, with no skipped mandatory contract tests.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```

---

# Implementation task 36 — Manual acceptance, documentation, and release

```text
You are Codex implementing the **HITL Sample Size Planner** (specification v1.0, method version 1.0, tool version 1.0.0), a personal offline Windows desktop tool for selecting a random sample of AI conversations and estimating SME review effort. Inspect `AGENTS.md` and the current repository, then consult the authoritative PDF at `docs/HITL_Sample_Size_Planner_Spec_v1.0.pdf` for the sections named below (use the searchable `docs/SPEC_TEXT.txt` as a convenience if PDF reading is unavailable; the PDF takes precedence). The specification's §4 formulas and §11.1 eleven-case answer key are immutable acceptance contracts: if code disagrees with a key, correct the code, not the key. This task is self-contained and applies to the current committed repository; do not depend on other prompts. The application targets Windows, but Codex cloud may execute on Linux: test portable logic in the available environment and explicitly defer any Windows-only manual check to the owner.

Non-negotiable architecture: Python 3.11, one runtime source `hitl_planner.py`, one pytest suite `test_hitl_planner.py`, Flask as the only runtime third-party package, otherwise standard library; all statistical calculations in Python; embedded offline HTML/CSS/plain JS only, no outbound requests/CDNs/telemetry/login; host 127.0.0.1 only. JSON plan/actuals versions are immutable, derived report/CSV regenerable, all writes atomic. Do not implement parked v2 features (stratification, uploads, PDF generator, Cohen kappa, issue-rate CI, trend view, cost, delete). Never accept conversation contents. Keep code testable by import without launching Flask.

Task: Manual acceptance, documentation, and release
Authoritative sections: §11.6, §12–13, Appendix B

Implementation scope:
Finish README.md for a non-technical Windows owner: Python3.11 environment, install Flask/pytest, start, stop, run selftest and pytest, configure port/workspace, find immutable files/CSV, browser Print to PDF, recover/backup, what tool cannot claim. Run all nine manual acceptance steps from spec §11.6 without modifying any fixed expected value. Verify proposed port5062 does not conflict with existing Pareto/IMR tools; if they are unavailable, stop and mark this an unresolved owner check, not "verified". Preserve spec version 1.0, method1.0, tool1.0.0 and no v2 features. Commit only after tests and owner acceptance, then tag `v1.0.0` only when acceptance is fully signed off.

Tests to write FIRST:
Manual checklist: K1–K4, 50k/88h case, 1m/385 case, certify slider and Adopt, save+report+print, reviewed382/issues11/agreement86, new month p prefill, Method11/11, quit/restart. README commands work in fresh Windows venv and include backup warnings.

Acceptance condition:
Ship only after all automatic and manual checks are green, port is verified, and the owner approves release.
Execution protocol:
1. Before implementation, summarize the exact functions/routes/screens to touch and list RED tests with expected numerical assertions.
2. Implement the smallest increment: write tests first, run them to see appropriate failure, then implement until green. Do not delete or water down tests.
3. Use the existing app's calculation/persistence helpers; avoid duplicate logic. Integrate all new code into a real call path or testable functional slice, with no dormant placeholder code.
4. Run `python -m pytest -q`; run `python hitl_planner.py --selftest` when implemented. If any established answer-key case fails, STOP and report rather than changing expectations.
5. Report changed files, exact tests run/results, unresolved risks, and acceptance evidence; explicitly distinguish checks NOT RUN on this environment (especially Windows-only tests). If established answer-key tests fail, stop and explain why.
6. For ChatGPT Codex cloud: leave one focused, reviewable branch/change set or pull request; do not merge it or mark `todo.md` complete. The owner reviews and merges after green checks, then starts the next task from the updated branch. For local Codex, make one focused commit only when green. Execute just this task; no next-task implementation.
```
