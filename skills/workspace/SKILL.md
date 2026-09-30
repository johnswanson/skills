---
name: workspace
description: Open a branch or PR in its own worktree and Herdr workspace, start a Claude agent there, hand it the task, and return. Usage - /workspace <task naming a branch or PR>
disable-model-invocation: true
---

# Workspace hand-off

Fire and forget: set up a worktree and a Herdr workspace for the task in `$ARGUMENTS`, brief a fresh Claude agent there, and return to the user the moment the brief is submitted. The user works with that agent directly.

Preflight: `test "${HERDR_ENV:-}" = 1` must pass, and load the `herdr` skill for CLI syntax. Every path below is absolute; the shell's cwd resets between calls. `REPO=/home/jds/work/metabase`.

## 1. Resolve the branch

- A PR link or number: `gh pr view <url|number> --json headRefName,url` gives the branch.
- A named branch: use it as given.
- Neither: coin a kebab-case name from the task. The hook in step 2 branches it from `origin/HEAD`, so `git -C $REPO fetch origin` first.

Fetch it: `git -C $REPO fetch origin <branch>`. `Permission denied (publickey)` means the SSH agent holds no key: ask the user to run `ssh-add`, then retry. This is the one place you stop for input.

Make sure a local branch exists, and record its state for the brief:

- None: `git -C $REPO branch --track <branch> origin/<branch>`.
- Present: `git -C $REPO rev-list --left-right --count <branch>...origin/<branch>` prints ahead and behind. Only behind: fast-forward it in step 2. Ahead: leave it alone and list the unpushed commits (`git log --oneline origin/<branch>..<branch>`); the agent reconciles them with the user.

Done when `origin/<branch>` is fresh and `refs/heads/<branch>` exists.

## 2. Worktree

An existing checkout wins: if `git -C $REPO worktree list --porcelain` already shows the branch, that path is the worktree (git refuses a second checkout of one branch). Otherwise create it through the Claude WorktreeCreate hook, which owns the location (`~/work/worktrees/<branch>`) and the setup symlinks (`bin/bb`, `CLAUDE.local.md`, `.claude/settings.local.json`); the last line of its stdout is the path:

```sh
printf '{"name":"%s","cwd":"%s"}' "<branch>" "$REPO" | /home/jds/.claude-work/hooks/worktree-create.sh
```

The hook checks out the local branch from step 1 when it exists, so step 1 comes first. A behind-only branch fast-forwards with `git -C <path> merge --ff-only origin/<branch>`.

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

House rules (pushing and PR comments only when told, test wrappers, dev env) reach the agent through the worktree's symlinked `CLAUDE.local.md`, so the brief leaves them out.

## 5. Return

As soon as `agent prompt` returns, report to the user: workspace id, agent name, worktree path, branch and its state, and any judgment call you made. Then stop; the user takes it from there.
