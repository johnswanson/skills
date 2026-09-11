---
name: stage
description: "Implement an issue in a worktree through subagents, adversarially review it, and stage it running for inspection before merge."
disable-model-invocation: true
---

Implement the issue the user names, then stage it for their inspection. The
merge is gated: nothing lands on main and the issue is not done until the user
has looked and said so.

When passed a single issue, the flow looks like this:

1. **Worktree.** Create a worktree on a fresh ticket branch off main. Run the
   project's documented worktree setup, if it has one — its `CLAUDE.md` or
   `CLAUDE.local.md` says where. Only then copy in what makes it runnable but
   isn't versioned (env files; install deps if absent; CLAUDE.local.md itself).

2. **Implement.** Set the issue's Status to `in-progress` first, according to
   the project's documented issue tracker. Then a subagent on Opus, working
   only in the worktree, does the implementation. Done when every acceptance
   criterion is addressed and the suites are green.

3. **Review** with /code-review in a separate agent on Opus, briefed from
   `brief-reviewer.md` in this skill's directory — adversarial: hunt real
   defects, spec violations, and weak or vacuous tests; press hardest on any
   design call the implementer made beyond the spec. Report only — findings
   ranked, each confirmed or plausible; fix nothing.

4. **Fix** each finding worth acting on by resuming the original implementer.
   Decide fix-vs-no-action yourself and say why. Done when every finding is
   fixed or explicitly declined and the suites are green again.

5. **Stage.** Set the issue's Status to `in-review` and append a comment:
   branch, commits, design calls, review outcome. If there is a documented
   method to do so, start the dev server in the worktree and hand the user the
   URL. Then stop and report — what was built, what the review found, and any
   design call that deserves their eye.

6. **The verdict is theirs.** On approval: merge to main — or, with an
   integration branch, merge to the integration branch — remove the worktree
   and branch, set the issue's Status to done and tick its boxes. On change
   requests: back to step 4.

When passed multiple issues in a single invocation, act as if you had been
given multiple sequential `/stage` invocations, with one exception: merge them
each (linearly) onto a fresh branch in a separate worktree after step 4, then
stage them and head to the user for a verdict on all of the issues at once. In
other words, fan out steps 1-4, and then consolidate into one worktree for
steps 5 and 6.

If on the other hand the user invokes `/stage` multiple times, run steps 1-6 on
each independently, in parallel, resulting in N different worktrees and N
different branches. Note that in some cases issues may be blocked by each
other; in this case, you may need to wait until issue N is Staged before
starting issue N+1, branching off of issue N's branch.
