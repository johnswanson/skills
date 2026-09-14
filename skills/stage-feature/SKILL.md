---
name: stage-feature
description: "Implement a feature in a worktree through workmux agents, adversarially review each, and stage the final product running for inspection before merge."
disable-model-invocation: true
---

Implement the feature the user names, then stage the result for their
inspection. The merge is gated: nothing lands on main and the issue is not done
until the user has looked and said so.

1. First, make sure both `/workmux` and `/coordinator` have been previously invoked
   in this session. If they have not, report back to the user and ask them to invoke both.

2. Begin the implementation loop. Create an integration branch, mirroring the
   main/master branch, and run a new workmux session for that integration branch
   with no prompt.

   Now find the first issue in the feature that is unblocked and in
   `ready-for-agent` status according to the project's documented issue
   tracker. Mark it as `in-progress`.

   Then spawn an implementer using `opus`:

       workmux add <issue-id> -a opus -b --base <feature> -P <prompt-file>

   `issue-id` means the whole `project/number` slug, e.g. the `issue-id` is `foo/123` not `123`.

   The handle is the `project/number` slug; every later command addresses the
   agent by it. The agent's prompt carries the issue ref and body verbatim, the
   acceptance criteria as a numbered list, and these instructions: run the
   suites, commit on the branch, and finish by writing a final report to a
   temporary file — what was built, any design call beyond the spec, and an
   evidence table of commands run with their results. It should then state the
   location of that final report. After launching the agent, wait for it to
   finish. Done when every acceptance criterion is addressed and the suites are
   green.

   Note that you can start multiple issues in parallel, as long as they are unblocked.

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

5. **Merge** to the integration branch using `workmux merge <handle>`.

6. Set the issue's Status to `in-review` and append a comment: integration
   branch, commits, design calls.

7. Return to step 2 and find the next unblocked issue; repeat until there are
   no remaining `ready-for-agent` issues left in the feature.

8. **Stage.** If there is a documented method to do so, start the dev server
   in the worktree running the integration branch and hand the user the URL.

   Then stop and report - what was built, any design calls that deserve the user's eye.

9. The verdict belongs to the user. If the user approves, merge the integration branch into the
   recorded base branch using `workmux merge`. Mark all issues as `done`.
