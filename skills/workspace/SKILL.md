---
name: workspace
description: Open a branch or PR in its own worktree and Herdr workspace, start a Claude agent there, hand it the task, and return. Usage - /workspace <task naming a branch or PR>
disable-model-invocation: true
---

# Workspace hand-off

Fire and forget: set up a worktree and a Herdr workspace for the task in `$ARGUMENTS`, brief a fresh Claude agent there, and return to the user the moment the brief is submitted. The user works with that agent directly.

Preflight: `test "${HERDR_ENV:-}" = 1` must pass, and load the `herdr` skill for CLI syntax. Every path below is absolute; the shell's cwd resets between calls.

`REPO` is the main checkout of the repository the session is in, even when the session sits in one of its worktrees:

```sh
REPO=$(git worktree list --porcelain | head -1 | sed 's/^worktree //')
```

Abort if the session is not inside a git repository.

## 1. Resolve the branch

- A PR link or number: `gh pr view <url|number> --json headRefName,url` gives the branch.
- A named branch: use it as given.
- Neither: coin a kebab-case name from the task, `git -C $REPO fetch origin`, and create it with `git -C $REPO branch <branch> origin/HEAD`. Skip the fetch and the ahead/behind check below; there is no remote branch yet.

Fetch it: `git -C $REPO fetch origin <branch>`. `Permission denied (publickey)` means the SSH agent holds no key: ask the user to run `ssh-add`, then retry. This is the one place you stop for input.

Make sure a local branch exists, and record its state for the brief:

- None: `git -C $REPO branch --track <branch> origin/<branch>`.
- Present: `git -C $REPO rev-list --left-right --count <branch>...origin/<branch>` prints ahead and behind. Only behind: fast-forward it in step 2. Ahead: leave it alone and list the unpushed commits (`git log --oneline origin/<branch>..<branch>`); the agent reconciles them with the user.

Done when `origin/<branch>` is fresh and `refs/heads/<branch>` exists.

## 2. Worktree

An existing checkout wins: if `git -C $REPO worktree list --porcelain` already shows the branch, that path is the worktree (git refuses a second checkout of one branch). Otherwise create it the way `claude --worktree` would under the active Claude config, which differs between the work and personal setups. Look for a WorktreeCreate hook in that config:

```sh
HOOK=$(jq -r '.hooks.WorktreeCreate[]?.hooks[]?.command // empty' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" 2>/dev/null | head -1)
```

- Hook present: it owns the location and any per-repo setup (symlinked local Claude files, tool shims), and the last line of its stdout is the path:

  ```sh
  printf '{"name":"%s","cwd":"%s"}' "<branch>" "$REPO" | "$HOOK"
  ```

- No hook: use Claude's default location, `$REPO/.claude/worktrees/<branch>`:

  ```sh
  git -C $REPO worktree add "$REPO/.claude/worktrees/<branch>" <branch>
  ```

Both paths check out the local branch from step 1, so step 1 comes first. A behind-only branch fast-forwards with `git -C <path> merge --ff-only origin/<branch>`.

Done when `git -C <path> status --short` is empty and `git -C <path> rev-parse --abbrev-ref HEAD` prints the branch.

## 3. Workspace and agent

```sh
herdr worktree open --cwd "$REPO" --path <path> --label <branch> --no-focus
```

Read `.result.root_pane.pane_id`, then start Claude in that pane:

```sh
herdr agent start <name> --kind claude --pane <pane_id> --timeout 90000
```

Agent name: the branch lowercased, runs of other characters collapsed to `-`, leading non-letters dropped, at most 32 characters, unique in `herdr agent list`.

Done when `agent start` returns `agent_started`.

## 4. Brief

Write the brief to a file in your scratchpad and submit it without `--wait`:

```sh
herdr agent prompt <name> "$(cat <file>)"
```

The brief carries, in this order, and nothing else:

1. Worktree path, branch, PR link if any, and "use absolute paths in every command".
2. Branch state worth knowing: at origin's tip, or the unpushed commits by hash and subject.
3. The user's task, verbatim.

House rules (pushing and PR comments only when told, test wrappers, dev env) reach the agent through the repo's own Claude instructions and whatever the worktree hook links in, so the brief leaves them out.

## 5. Return

As soon as `agent prompt` returns, report to the user: workspace id, agent name, worktree path, branch and its state, and any judgment call you made. Then stop; the user takes it from there.
