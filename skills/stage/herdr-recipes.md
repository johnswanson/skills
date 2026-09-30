# Herdr recipes for `stage` and `stage-feature`

Command sequences the skills refer to by name. Every command returns JSON;
read identifiers from the response, never guess them.

Two names appear throughout:

- `<branch>` — the git branch. Follow the project's branch convention; the
  issue id (`foo/123`) is the default when there is none.
- `<agent>` — the Herdr agent name. It must match `[a-z][a-z0-9_-]{0,31}` and
  be unique among live agents in this Herdr session. Make it short and
  recognizable in the sidebar: the issue number plus a word or two of topic,
  like `123-oauth-retry`. Add a project prefix only when the session hosts
  several projects and the workspace label does not already tell them apart.

`<base>` is the branch the work leaves from and merges back into. Unless the
user passed `--onto <branch>`, it is the repository's default branch:

    git symbolic-ref --short refs/remotes/origin/HEAD   # e.g. origin/master

Strip the `origin/` prefix. If that ref is unset, use whichever of `master` or
`main` exists. Herdr does not record the base anywhere; keep it in your notes.

## Recipe: spawn

Create the worktree and its workspace. Run from the source checkout.

    herdr worktree create --cwd "$PWD" --branch <branch> --base <base> --label <branch> --no-focus

Read from the response:

- `.result.workspace.workspace_id` — the workspace (`w2`), needed for removal
- `.result.root_pane.pane_id` — the shell pane to start the agent in (`w2:p1`)
- `.result.worktree.path` — the worktree directory

Start Claude on Opus in the root pane with auto permissions. This returns once
the agent is idle (about four seconds); the pane is at its prompt immediately
after creation.

    herdr agent start <agent> --kind claude --pane <root-pane-id> -- --model opus --permission-mode auto

Deliver the prompt from a file and block until the agent settles. There is no
prompt-from-file flag; command substitution works for multi-line files.

    herdr agent prompt <agent> "$(cat <prompt-file>)" --wait

Do not pass the prompt as a Claude positional argument: `agent start` would
then return not-ready while Claude is already working.

## Recipe: wait and handle blocked

`--wait` (on `prompt` or standalone `agent wait <agent>`) returns on the first
settled `idle`, `done`, or `blocked` state. Leave the timeout off for
implementation work; it is indefinite. On return, check
`.result.agent.agent_status`:

- `done` or `idle`: the turn is over. Read the report the agent named.
- `blocked`: Herdr recognized an approval or question UI. Auto permissions
  make this rare, so it is usually a real question. Inspect it:

      herdr agent read <agent> --source recent-unwrapped --lines 60

  If the prompt itself already answers it, reply with `herdr agent send-keys
  <agent> <key>` (for example `enter`, or `down` then `enter`) and wait
  again. Otherwise stop and put the question to the user.

A wait that returns `timeout` or `agent_prompt_stalled` does not prove the
prompt was lost. Read the pane before deciding whether to resend.

## Recipe: reviewer pane

Every reviewer — each sub-agent `/code-review` would normally spawn natively,
and each lens from `review-lenses.md` — runs as its own Herdr agent in a pane
inside the worker's worktree. It shares the checkout but none of the worker's
context. The worker must be idle and must stay idle until every reviewer has
finished: do not send follow-up work while they share the tree.

    herdr pane split <root-pane-id> --direction right --cwd <path> --no-focus
    herdr agent start <reviewer> --kind claude --pane <new-pane-id> -- --model opus --permission-mode auto
    herdr agent prompt <reviewer> "$(cat <prompt-file>)" --wait

`<reviewer>` follows the same naming rule as `<agent>`: the issue number plus
the reviewer's role, like `123-standards`, `123-spec`, or `123-<lens>`.
`<prompt-file>` holds the reviewer's brief exactly as `/code-review` or the
lens specifies it, plus this closing instruction:

> Report only: fix nothing, commit nothing, and revert any change you make
> to test a claim. When done, write the full report to a temporary file and
> reply with only that file's path.

Read the reply with `herdr agent read <reviewer> --source recent-unwrapped
--lines 40`, then read the file. Handle `blocked` as in the wait recipe.

Reviewers may run in parallel: split each new pane from the previous
reviewer's pane, alternating `right` and `down` so no pane gets unusably
small, start them all, then wait on them one after another.

Close each reviewer's pane once its report is in hand; a re-review after
fixes starts fresh ones:

    herdr pane close <new-pane-id>

## Recipe: follow-up

Confirm the agent is not blocked, then prompt it again the same way:

    herdr agent get <agent>
    herdr agent prompt <agent> "$(cat <followup-file>)" --wait

## Recipe: recover identifiers

If the create response is gone from context:

    herdr worktree list --cwd "$PWD"      # .worktrees[] by branch: path, open_workspace_id
    herdr agent list                       # live agents: name, pane_id, workspace_id
    herdr pane list --workspace <ws-id>    # panes in the worker's workspace

## Recipe: run a command in the worker's workspace

Split a sibling pane below the agent and run there. Do not run commands in
the agent's own pane.

    herdr pane split <root-pane-id> --direction down --cwd <path> --no-focus
    herdr pane run <new-pane-id> "<command>"
    herdr pane wait-output <new-pane-id> --regex '<pattern>' --timeout 60000

`wait-output` searches the whole recent snapshot, so a pattern that also
matches the echoed command line (like a bare URL regex when the command
contains a URL) matches immediately. Match on something only the program
prints, then read the pane to extract the URL:

    herdr pane read <new-pane-id> --source recent-unwrapped --lines 40

## Recipe: merge and clean up

Herdr has no merge command. Merge strategy is rebase then fast-forward.

1. Refuse if the worktree is dirty:

       git -C <path> status --porcelain

2. Rebase the branch onto its base, in the worktree:

       git -C <path> rebase <base>

3. In the source checkout, check out the base and fast-forward. Refuse if
   the source checkout is dirty. Note this leaves the source checkout on
   `<base>`.

       git status --porcelain
       git checkout <base>
       git merge --ff-only <branch>

4. Remove the worktree and close its workspace. This kills the agent pane;
   no force flag is needed for a live agent.

       herdr worktree remove --workspace <ws-id>

5. Herdr does not delete the branch:

       git branch -d <branch>
