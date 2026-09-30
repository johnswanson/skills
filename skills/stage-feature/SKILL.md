---
name: stage-feature
description: "Implement a feature in a worktree through Herdr-managed agents, adversarially review each, and stage the final product running for inspection before merge."
disable-model-invocation: true
---

Implement the feature the user names, then stage the result for their
inspection. The merge is gated: nothing lands on main and the issue is not done
until the user has looked and said so.

Herdr command sequences live in `herdr-recipes.md` in the `stage` skill's
directory (a sibling of this one); the steps below refer to them by recipe
name.

1. First, make sure `/herdr` has been previously invoked in this session. It
   teaches you the `herdr` CLI and requires that this agent is running inside
   a Herdr-managed pane. If it has not been invoked, or its environment check
   fails, report back to the user and ask them to invoke it from inside Herdr.

2. Begin the implementation loop. Create an integration branch, mirroring the
   default branch (`master` or `main`), as a Herdr worktree with no agent
   started: only the `herdr worktree create` line of the **spawn** recipe,
   with the feature name as the branch and the default branch as the base.
   Keep its base, workspace id, root pane id, and worktree path.

   Now find the first issue in the feature that is unblocked and in
   `ready-for-agent` status according to the project's documented issue
   tracker. Mark it as `in-progress`.

   Then spawn an implementer on `opus` using the full **spawn** recipe with
   `--base <feature>`.

   The branch follows the project's convention, defaulting to the issue id
   (`foo/123`). The agent name is short and recognizable, as the recipes file
   describes; every later agent command addresses that worker by its name.
   Keep each worker's workspace id, root pane id, and worktree path from its
   create response; the **recover identifiers** recipe finds them again if
   lost.

   The agent's prompt carries the issue ref and body verbatim, the acceptance
   criteria as a numbered list, and these instructions: run the suites, commit
   on the branch, and finish by writing a final report to a temporary file —
   what was built, any design call beyond the spec, and an evidence table of
   commands run with their results. It should then state the location of that
   final report. After launching the agent, wait for it to finish using the
   **wait and handle blocked** recipe. Done when every acceptance criterion is
   addressed and the suites are green.

   You can start multiple issues in parallel, as long as they are unblocked.
   Each gets its own worktree, workspace, and agent name. Herdr waits on one
   agent at a time; wait on parallel workers one after another, since all of
   them must finish anyway.

3. **Review.** Invoke the `/code-review` skill (`mattpocock-skills:code-review`)
   with these inputs:

   - the fixed point: the feature branch;
   - the changes: branch `<branch>` checked out in the worktree at `<path>`,
     so every git command runs with `-C <path>`;
   - the spec: the issue ref and body verbatim with the acceptance criteria
     as a numbered list, written to a temporary file and passed as the spec
     path;
   - and this one instruction: launch each sub-agent as a Herdr agent in its
     own pane using the **reviewer pane** recipe in `herdr-recipes.md`, not
     as a native subagent.

   Then run every lens in `review-lenses.md` in the `stage` skill's directory the
   same way, each as its own reviewer pane, and present its findings under
   the lens's own heading after the Standards and Spec reports. Reviewers
   report only; nothing is fixed in this step.

4. **Fix** each finding worth acting on as follow-up work in the original
   worker session using the **follow-up** recipe, then wait for it. Decide
   fix-vs-no-action yourself and say why. Have the worker refresh its report
   when it is done. Done when every finding is fixed or explicitly declined and
   the suites are green again.

5. **Merge** to the integration branch using the **merge and clean up**
   recipe, with one change: the fast-forward happens in the integration
   branch's worktree, not the source checkout. Rebase the issue branch onto
   the feature branch in the issue worktree, then in the integration worktree
   run `git merge --ff-only <branch>`. Remove the issue worktree and delete
   its branch as the recipe says.

6. Set the issue's Status to `in-review` and append a comment: integration
   branch, commits, design calls.

7. Return to step 2 and find the next available issue; repeat until there are
   no remaining `ready-for-agent` issues left in the feature. Note that "available" here
   means either "unblocked" or "blocked only by issues that are already merged into
   the integration branch."

8. **Stage.** If there is a documented method to do so, start the dev server
   in the integration branch's workspace using the **run a command in the
   worker's workspace** recipe and hand the user the URL.

   Then stop and report - what was built, any design calls that deserve the user's eye.

9. The verdict belongs to the user. If the user approves, merge the integration
   branch into the default branch using the **merge and clean up** recipe as
   written: rebase in the integration worktree, fast-forward in the source
   checkout, remove the integration worktree and its workspace, delete the
   branch. Mark all issues as `done`.
