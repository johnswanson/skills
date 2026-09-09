# Waves — several issues at once

Applies when the skill is given more than one issue, or an `--onto <branch>` argument. SKILL.md's steps
still run, once per issue; what follows replaces the parts that assume a single issue and main.

## Inputs

- A set of issues.
- `--onto <branch>` — use that existing integration branch. Without it, create one off main named for the
  feature, not for any one issue (`session-management-spec`).

## 1. Graph, then waves

Before touching a worktree:

1. Read each issue's blockers from the project's tracker (with the `tickets` CLI, the `Blocked by:` line of
   `tickets issue show <NN> -p <project>`).
2. A blocker outside the set that is not done blocks the whole run. Stop, name it, and ask. Do not
   quietly drop the issue that depends on it.
3. A wave is every not-yet-merged issue in the set whose blockers have all merged. Recompute after each
   wave; the first wave is the issues with no blockers inside the set.
4. Print the plan — integration branch, each wave and its issues — before starting.

Run a wave's issues in parallel. No issue in wave *n+1* starts until every issue in wave *n* has merged.

## 2. Per issue: steps 1–4, with three changes

- **Step 1.** The worktree branches off the integration branch at its current tip, never off main, so each
  wave builds on the last. Name the worktree `<feature-short>-<NN>-<slug>` (`sm-28-sessions-list`); the
  worktree hook names the branch after the worktree and reuses an existing one of the same name.
- **Steps 2 and 3.** Fill `{integration-branch}` in `brief-implementer.md` (its "Parallel-branch etiquette"
  section then applies: delimited blocks, open maps, no reformatting of shared files) and add to both
  briefs the sibling issues in the same wave — number, one-line summary, and the files each is expected to
  touch — so the agent knows which shared files will see additive edits it cannot see.
- **Step 5 does not apply per issue.** Staging happens once, for the integration branch (§5).

## 3. Merge, immediately after step 4 is green

The orchestrator merges; no subagent touches the integration branch.

```
git merge --no-ff <branch> -m "Merge <branch>: <summary> (<issue ref>)"
```

e.g. `Merge sm-28-sessions-list: GET /api/sessions list endpoint (metabase/28)`.

Conflicts are the orchestrator's to resolve. They are textual and expected in the files two siblings both
touched; resolve them by hand and re-run the issue's own test namespaces against the merge result. Never
resolve a conflict by re-running an implementer — it has no view of the sibling's intent and will rewrite
working code.

Before the next wave starts, run the merged tests of *every* issue merged so far on the integration
branch. A sibling's semantic conflict shows up here, not in the merge.

## 4. Cleanup, on the merge — not at the end

For the issue just merged, in order:

1. Tear down its dev environment.
2. Remove the worktree.
3. Delete the issue branch — the `--no-ff` merge commit preserves its history.
4. Set the issue's status to `in-review` in the tracker.
5. Append the step 5 comment: branch, commits, design calls, review outcome, and any optional scope taken.

Do this now rather than at the end of the run: a live dev env holds ports and containers that the next
wave's issues need, and a worktree of the same name recreated later inherits the orphaned backend and
bundler processes of the one that was deleted.

## 5. Stage once (step 5)

After the last wave, on the integration worktree: start the dev env and hand over the URL. The report
covers the whole run — every issue with its review outcome, and the design calls that deserve the user's
eye, attributed to their issue.

## 6. Verdict (step 6)

- Approval: merge the integration branch to main, then set every issue done and tick its boxes.
- Change requests name an issue. Only that issue goes back to step 4, in a fresh worktree branched off the
  integration branch, followed by the same merge (§3) and cleanup (§4). The other issues stay staged.

