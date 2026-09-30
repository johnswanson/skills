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

   The agent's prompt carries the issue ref and body verbatim, the acceptance
   criteria as a numbered list, and these instructions: run the suites, commit
   on the branch, and finish by writing a final report to a temporary file —
   what was built, any design call beyond the spec, and an evidence table of
   commands run with their results. It should then state the location of that
   final report. After launching the agent, wait for it to finish using the
   **wait and handle blocked** recipe. Done when every acceptance criterion is
   addressed and the suites are green.

3. **Review** with /code-review in a separate subagent on Opus, briefed from
   `brief-reviewer.md` in this skill's directory — adversarial: hunt real
   defects, spec violations, and weak or vacuous tests; press hardest on any
   design call the implementer made beyond the spec. Report only — findings
   ranked, each confirmed or plausible; fix nothing. The brief's inputs come
   from the worker: the worktree path from the create response, the base
   from step 2, and the implementer report from the temporary file the
   implementer created.

4. **Fix** each finding worth acting on as follow-up work in the original
   worker session using the **follow-up** recipe, then wait for it. Decide
   fix-vs-no-action yourself and say why. Have the worker refresh its report
   when it is done. Done when every finding is fixed or explicitly declined and
   the suites are green again.

5. **Stage.** Set the issue's Status to `in-review` and append a comment:
   branch, commits, design calls, review outcome. If there is a documented
   method to do so, start the dev server in the worker's workspace using the
   **run a command in the worker's workspace** recipe and hand the user the
   URL. Then stop and report — what was built, what the review found, and any
   design call that deserves their eye.

6. **The verdict is theirs.** On approval, follow the **merge and clean up**
   recipe. It rebases onto the branch's base — the default branch, or the
   `--onto` branch — fast-forwards that base in the source checkout, removes the
   worktree and its workspace, and deletes the branch; note that it leaves the
   source checkout on the base branch. Then set the issue's Status to done and
   tick its boxes. On change requests: back to step 4.
