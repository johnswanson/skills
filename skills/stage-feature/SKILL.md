---
name: stage-feature
description: "Implement every issue in a feature through Herdr-managed agents, one worktree and review cycle per issue, merge them onto an integration branch, and stage that branch running for inspection before merge."
disable-model-invocation: true
---

Implement the feature the user names, one issue at a time, then stage the
integration branch for their inspection. The merge is gated: nothing lands on
the base and no issue is done until the user has looked and said so.

Herdr command sequences live in `herdr-recipes.md` in the `stage` skill's
directory, a sibling of this one; the steps below refer to them by recipe
name. `<base>` is as that file defines it: the default branch, or the
`--onto` branch.

1. First, invoke the `/herdr` skill unless it has been previously invoked in
   this session. It teaches you the `herdr` CLI and requires that this agent is
   running inside a Herdr-managed pane. If the skill is unavailable or the
   environment check fails, abort and tell the user: this skill needs Herdr
   and its skill installed, and must be run from inside Herdr.

2. **Integration branch.** Create a worktree with no agent: only the
   `herdr worktree create` line of the **spawn** recipe, with the feature's
   name as the branch and `<base>` as its base. Keep its workspace id, root
   pane id, and worktree path; every issue merges onto this branch, and it
   is what the user inspects.

3. **Implement an issue.** Find the next available issue in the feature
   according to the project's documented issue tracker: Status
   `ready-for-agent`, and blocked by nothing except issues already merged
   onto the integration branch. Set its Status to `in-progress`, then spawn
   an implementer on `opus` using the full **spawn** recipe with the
   integration branch as its base.

   The branch follows the project's convention, defaulting to the issue id
   (`foo/123`). The agent name is short and recognizable, as the recipes file
   describes; every later agent command addresses that worker by its name.
   Keep each worker's workspace id, root pane id, and worktree path from its
   create response; the **recover identifiers** recipe finds them again if
   lost.

   The agent's prompt is `worker-prompt.md` in the `stage` skill's
   directory, with `<issue id>`, `<stage dir>` (that directory, absolute),
   and `<repo>` (the source checkout, absolute) filled in. Write it to a file
   in your scratchpad; the worker runs its own review cycle from it. Then
   wait for it with the **wait and handle blocked** recipe.

   Several available issues may run at once, each with its own worktree,
   workspace, and agent name. Herdr waits on one agent at a time; wait on
   parallel workers one after another, since all of them must finish anyway.

4. **Merge onto the integration branch** with the **merge and clean up**
   recipe, the integration branch as `<base>`: the rebase runs in the issue
   worktree and the fast-forward in the integration worktree. If the rebase
   conflicts, abort it and hand the conflict to that issue's worker with the
   **follow-up** recipe: rebase, resolve, run the full suite, commit; then
   merge again. Set the issue's Status to `in-review` and append a comment:
   integration branch, commits, design calls, review outcome.

5. Return to step 3 until the feature has no available issue left. An issue
   that stays blocked by something outside the feature is reported in step
   6, not worked.

6. **Stage.** If there is a documented method to do so, start the dev server
   in the integration branch's workspace using the **run a command in the
   worker's workspace** recipe and hand the user the URL. Then stop and
   report — what was built, issue by issue, what the reviews found, any
   design call that deserves their eye, and any issue left unworked and why.

7. **The verdict is theirs.** On approval, follow the **merge and clean up**
   recipe as written, with the integration branch as `<branch>`: rebase in
   the integration worktree, fast-forward `<base>` in the source checkout,
   remove the worktree and its workspace, delete the branch; note that it
   leaves the source checkout on `<base>`. Then set every merged issue's
   Status to done and tick its boxes. On change requests: start an agent in
   the integration worktree's root pane, the `agent start` and `agent prompt`
   lines of the **spawn** recipe, hand it the request verbatim with the
   instruction to commit on the current branch, wait, then back to step 6.
