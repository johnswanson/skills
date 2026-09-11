---
name: stage
description: "Implement an issue in a worktree through workmux agents, adversarially review it, and stage it running for inspection before merge."
disable-model-invocation: true
---

Implement the issue the user names, then stage it for their inspection. The
merge is gated: nothing lands on main and the issue is not done until the user
has looked and said so.

1. First, invoke the `/coordinator` skill unless it has been previously invoked
   in this session. This will teach you how to manage agents using `workmux`
   CLI commands. (If the coordinator skill is unavailable, it's not installed - abort
   and tell the user to install workmux and its skills.)

2. **Implement.** Set the issue's Status to `in-progress` first, according to
   the project's documented issue tracker. Then spawn the implementer using
   `opus`:

       workmux add <issue-id> -a opus -b -P <prompt-file>

   `issue-id` means the whole `project/number` slug, e.g. `foo/123`.

   Add `--base <branch>` when the user passed `--onto <branch>`. The handle is
   the issue id; every later command addresses the agent by it. The agent's
   prompt carries the issue ref and body verbatim, the acceptance criteria as a
   numbered list, and these instructions: run the suites, commit on the branch,
   and finish by writing a final report to a temporary file — what was built,
   any design call beyond the spec, and an evidence table of commands run with
   their results. It should then state the location of that final report. After
   launching the agent, wait for it to finish. Done when every acceptance
   criterion is addressed and the suites are green.

3. **Review** with /code-review in a separate subagent on Opus, briefed from
   `brief-reviewer.md` in this skill's directory — adversarial: hunt real
   defects, spec violations, and weak or vacuous tests; press hardest on any
   design call the implementer made beyond the spec. Report only — findings
   ranked, each confirmed or plausible; fix nothing. The brief's inputs come
   from the worker: the worktree path from `workmux path <handle>`, the base
   from `git config branch.<branch>.workmux-base`, and the implementer report
   from the temporary file the implementer created.

4. **Fix** each finding worth acting on as follow-up work in the original
   worker session — `workmux send <handle> -f <followup-file>`, then wait for
   it. Decide fix-vs-no-action yourself and say why. Have the worker refresh
   its report when it is done. Done when every finding is fixed or explicitly
   declined and the suites are green again.

5. **Stage.** Set the issue's Status to `in-review` and append a comment:
   branch, commits, design calls, review outcome. If there is a documented
   method to do so, start the dev server in the worker's window with
   `workmux run <handle> -b -- <command>` and hand the user the URL. Then stop
   and report — what was built, what the review found, and any design call
   that deserves their eye.

6. **The verdict is theirs.** On approval: `workmux merge <handle>`. It merges
   into the branch's recorded base — main, or the `--onto` branch — and
   removes the worktree, its window, and the branch; note that it leaves the
   main checkout on that target branch. Then set the issue's Status to done
   and tick its boxes. On change requests: back to step 4.
