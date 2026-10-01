---
name: stage
description: "Implement an issue in a worktree through a Herdr-managed agent, adversarially review it, and stage it running for inspection before merge."
disable-model-invocation: true
---

Implement the issue the user names, then stage it for their inspection. The
merge is gated: nothing lands on main and the issue is not done until the user
has looked and said so.

Herdr command sequences live in `herdr-recipes.md` in this skill's directory;
the steps below refer to them by recipe name.

1. First, invoke the `/herdr` skill unless it has been previously invoked in
   this session. It teaches you the `herdr` CLI and requires that this agent is
   running inside a Herdr-managed pane. If the skill is unavailable or the
   environment check fails, abort and tell the user: this skill needs Herdr
   and its skill installed, and must be run from inside Herdr.

2. **Implement.** Set the issue's Status to `in-progress` first, according to
   the project's documented issue tracker. Then spawn the implementer on
   `opus` using the **spawn** recipe.

   The branch follows the project's convention, defaulting to the issue id
   (`foo/123`). The agent name is short and recognizable, as the recipes file
   describes; every later agent command addresses the worker by that name.
   The base is the repository's default branch, `master` or `main`, unless
   the user passed `--onto <branch>`. Keep the base, workspace id, root pane
   id, and worktree path from the create response; the **recover
   identifiers** recipe finds the ids again if they are lost.

   The agent's prompt should be the following:

   ```
   Implement the work described by `<issue id>`

   Use /tdd where possible, at pre-agreed seams.

   Run typechecking regularly, single test files regularly, and the full test suite once at the end.

   Once done, review the code in two ways:
   - use /code-review, with the additional instruction to launch each sub-agent as a herdr agent in its own pane, using
     the **reviewer pane** recipe in `herdr-recipes.md` (not a native subagent).
   - read `review-lenses.md` in this skill's directory, and the repo's own (if it exists) in `.claude/review-lenses.md`.
     Launch a reviewer for each lens, again, as a herdr agent in its own pane.

   Use your best judgment about which findings to fix. Run the full test suite after any substantive fixes.

   Commit your work to the current branch.
   ```

   After launching the agent, wait for it to finish using the
   **wait and handle blocked** recipe.

3. **Stage.** Set the issue's Status to `in-review` and append a comment:
   branch, commits, design calls, review outcome. If there is a documented
   method to do so, start the dev server in the worker's workspace using the
   **run a command in the worker's workspace** recipe and hand the user the
   URL. Then stop and report — what was built, what the review found, and any
   design call that deserves their eye.

4. **The verdict is theirs.** On approval, follow the **merge and clean up**
   recipe. It rebases onto the branch's base — the default branch, or the
   `--onto` branch — fast-forwards that base in the source checkout, removes the
   worktree and its workspace, and deletes the branch; note that it leaves the
   source checkout on the base branch. Then set the issue's Status to done and
   tick its boxes. On change requests: back to step 4.
