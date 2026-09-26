---
description: Run one build step from BLUEPRINT.md (usage: /step N)
argument-hint: <step number 1-22>
---

Run build step $ARGUMENTS of the IMR Control Chart Tool, and only that step.

1. Open BLUEPRINT.md in the repository root. Find the heading that starts with `### Step $ARGUMENTS — ` (the number followed by a space and an em dash, so Step 1 does not match Step 10–19).
2. Take the single ```text fenced block that directly follows that heading. That block is your complete instruction for this session. Do not read ahead into later steps' prompts, and do not do any work belonging to another step.
3. If there is no such heading, or no ```text block under it, stop and say so. Do not guess a prompt.
4. Follow CLAUDE.md throughout. Never modify SPEC.md, BLUEPRINT.md, todo.md or CLAUDE.md, except the todo.md ticks point 6 allows.
5. Commit exactly as the step prompt says (Step 21 is not committed by you). If the repository has a remote named `origin`, push each commit you make to the current branch with `git push -u origin HEAD`, since a cloud container does not keep unpushed work.
6. Owner-approved exception to the "never modify todo.md" rule, limited to this: once the full test suite is green, open todo.md, find the `**Step $ARGUMENTS — ` entry and tick only its `Built` line (for Step 21, `Built; files staged, **not committed**`) and its `Tests green` line, changing `- [ ]` to `- [x]`. Change nothing else in todo.md: the Verify and Watch-for items are the owner's to tick. Except on Step 21, commit this as a separate commit after the step's own commit (message: `todo: tick Step $ARGUMENTS built and tests green`) and push it as in point 5. On Step 21, leave the change unstaged and uncommitted along with the rest.
7. Show the owner the updated todo.md: send it with the SendUserFile tool (display "render") if that tool is available, otherwise print that step's todo.md entry in your reply.
8. Finish with the plain-English summary the step prompt asks for.
