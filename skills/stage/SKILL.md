---
name: stage
description: "Implement an issue in a worktree through subagents, adversarially review it, and stage it running for inspection before merge."
disable-model-invocation: true
---

Implement the issue the user names, then stage it for their inspection. The merge is gated: nothing lands on main and the issue is not done until the user has looked and said so.

1. **Worktree.** Create a worktree on a fresh ticket branch off main. Copy in what makes it runnable but isn't versioned (env files; install deps if absent).

2. **Implement.** Set the issue's Status to `in-progress` first, according to the project's documented issue tracker. Then a subagent on Opus, working only in the worktree. Brief it with the issue, the relevant PRD/ADRs/context docs, and key file pointers. Its instructions: use /tdd where possible, at pre-agreed seams; run typechecking and single test files regularly, the full suite once at the end; commit to the branch. Done when every acceptance criterion is addressed and the suites are green.

3. **Review** with /code-review in a separate agent on Fable, briefed to be adversarial: hunt real defects, spec violations, and weak or vacuous tests; press hardest on any design call the implementer made beyond the spec. Report only — findings ranked, each confirmed or plausible; fix nothing.

4. **Fix** each finding worth acting on with an Opus subagent, or by resuming the original implementer. Decide fix-vs-no-action yourself and say why. Done when every finding is fixed or explicitly declined and the suites are green again.

5. **Stage.** Set the issue's Status to `in-review` and append a comment: branch, commits, design calls, review outcome. If there is a documented method to do so, start the dev server in the worktree and hand the user the URL. Then stop and report — what was built, what the review found, and any design call that deserves their eye.

6. **The verdict is theirs.** On approval: merge to main, remove the worktree and branch, set the issue's Status to done and tick its boxes. On change requests: back to step 4.
