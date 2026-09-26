---
description: Run one build step from BLUEPRINT.md (usage: /step N)
argument-hint: <step number 1-22>
---

Run build step $ARGUMENTS of the IMR Control Chart Tool, and only that step.

1. Open BLUEPRINT.md in the repository root. Find the heading that starts with `### Step $ARGUMENTS — ` (the number followed by a space and an em dash, so Step 1 does not match Step 10–19).
2. Take the single ```text fenced block that directly follows that heading. That block is your complete instruction for this session. Do not read ahead into later steps' prompts, and do not do any work belonging to another step.
3. If there is no such heading, or no ```text block under it, stop and say so. Do not guess a prompt.
4. Follow CLAUDE.md throughout. Never modify SPEC.md, BLUEPRINT.md, todo.md or CLAUDE.md.
5. Commit exactly as the step prompt says (Step 21 is not committed by you). If the repository has a remote named `origin`, push each commit you make to the current branch with `git push -u origin HEAD`, since a cloud container does not keep unpushed work.
6. Finish with the plain-English summary the step prompt asks for.
