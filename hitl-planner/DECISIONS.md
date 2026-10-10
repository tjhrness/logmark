# Decisions and open checks

This is a planning ledger, not authorization to change statistical formulas or fixed answer-key values. Record owner choices here; for any change affecting a formula, constant or answer-key value, specification §1/§4 requires a method-version bump and a new approved spec.

| ID | Status | Decision | Reason / owner action |
|---|---|---|---|
| D-01 | **OPEN** | Default port **5062 provisional** | Spec §2.3 says check existing Pareto/IMR script ports; those scripts are not in the attached material. Verify on user's Windows machine. If conflict, pick unused fixed port and document it in Appendix B project notes/config. |
| D-02 | Confirmed by spec | One source `hitl_planner.py`, single pytest file | No modules/packages; additional Markdown guidance and test dependency metadata are not runtime modules. |
| D-03 | Confirmed by spec | Immutable numbered JSON; derived HTML+CSV | Protect user records, enable regeneration. |
| D-04 | Confirmed by spec | No generated PDF; browser Print to PDF | PDF output explicitly parked for v2. |
| D-05 | Confirmed by spec | No conversation content in tool | Counts/rates and notes only, local offline. |
| D-06 | OPEN implementation clarification | Concurrent versions | Version selected at save-time, no overwrite; use safe exclusive allocation/synchronization while maintaining temp+atomic contract. |
| D-07 | OPEN acceptance environment | Windows browser and Excel manual acceptance | Requires owner's target desktop; source spec §11.6. |
| D-08 | Confirmed workflow adaptation | Codex cloud/CLI instead of original Claude build tool | Repository instructions in `AGENTS.md`; one standalone Codex task per prompt; code/statistical contracts unchanged. |
| D-09 | OPEN Codex setup | GitHub connected repository and task environment | Owner must connect authorized GitHub repo; cloud Linux checks cannot substitute for Windows manual acceptance. |

## Change record

| Date | Decision ID | Change | Approved by |
|---|---|---|---|
| — | — | — | — |

## Implementation observation: all-issue prefill boundary
Specification §4.6 sets next-cycle p=max(obs,0.001), which yields 1 when every review finds an issue. I8 limits p to 0.999. Both contracts are preserved: prefill retains the specified observed value and Plan validation requires manual correction before saving. No silent upper clamp or statistical method change was introduced. Owner clarification can resolve this boundary in a future specification revision.
