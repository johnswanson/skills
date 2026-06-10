# skills

A [Claude Code](https://claude.com/claude-code) plugin (`jds`) packaging the personal skills I use across machines, kept in version control.

Currently focused on the **jds-wiki** pattern (an LLM-maintained personal wiki). Skills:

- **`jds:ingest`** — `/jds:ingest <url-or-path>` — fetch a source, stage it in the wiki's `raw/`, then write/update wiki pages.
- **`jds:lint`** — `/jds:lint` — read-only health check (contradictions, orphans, gaps).
- **`jds:ask`** — `/jds:ask <question>` — answer from the wiki, with citations; offer to file the synthesis back.
- **`jds:research`** — `/jds:research <question>` — investigate a question against the codebase at the current working directory using parallel exploration; offers to file the synthesis to the wiki.

The wiki-touching skills resolve the wiki path from `~/.config/jds-wiki/config.yml` (single field: `wiki: <path>`). Default if missing: `~/Obsidian/Wiki`.

## Code review

A local-only port of the [adamsreview](https://github.com/adamjgmiller/adamsreview) pipeline:

- **`jds:review`** — `/jds:review [--scrape-pr-comments] [--holistic] [--full]` — deep multi-lens code review of the current branch vs its base. Produces `artifact.json` + `artifact.md`.
- **`jds:fix`** — `/jds:fix [threshold] [--granular-commits]` — applies auto-fixable findings via fix-group agents, post-fix-reviews the tree, commits survivors **locally** (never pushes), reverts regressions.
- **`jds:walkthrough`** — `/jds:walkthrough [threshold]` — interactive briefing/decide loop over the findings `/jds:fix` would skip; writes `walkthrough-decisions.md` and (for pre-existing findings) `follow-ups.md` into the review directory instead of PR comments / GitHub issues.
- **`jds:promote`** — `/jds:promote <finding_id> [--reason ...] [--fix-hint ...] [--force] [--defer-render]` — single-finding human override to auto-fixable.
- **`jds:add`** — `/jds:add [paste or flags]` — inject externally-sourced findings (cloud reviews, manual finds) into the latest artifact; validates them via Phase 4.

Differences from the original:

- **Local-only writes.** Artifacts (`artifact.json`, `artifact.md`, logs) land under `~/.jds-reviews/<repo-slug>/<branch>/<review-id>/` (override with `JDS_REVIEW_REVIEWS_ROOT`). It never posts PR comments, never pushes, never writes to GitHub in any way.
- **`--scrape-pr-comments`** replaces `--ensemble`: a read-only scrape of bot-authored comments on the branch's GitHub PR (if one exists), normalized into review candidates. The original's Codex CLI dispatch was dropped.
- **`--holistic`** gates the L7 holistic lens (was bundled into `--ensemble` upstream).
- **Audit trails land locally**: fix's auto-rec decisions (`fix-autorec-decisions.md`), walkthrough decisions, and pre-existing follow-up drafts are documents in the review directory, not PR comments or GitHub issues.
- **Fable instead of Opus** for the deep subagents (L2/L7 lenses, deep-lane validators, cross-cutting); Sonnet/Haiku subagents unchanged. Override the deep-lane model with `JDS_REVIEW_HIGH_MODEL` (`fable` | `opus` | `sonnet` | `haiku`, default `fable`).

(The supporting `fragments/` and `bin/` directories at the repo root belong to these commands; the plugin runtime puts `bin/` on `$PATH` automatically. The original's `codex-review` command and Codex CLI integration were not ported.)

## Bootstrap on a new machine

```bash
# 1. Clone the repo
git clone <this-repo> ~/projects/skills
```

Then inside Claude Code:

```
/plugin marketplace add ~/projects/skills
/plugin install jds@jds
```

Finally, point the skills at your wiki on this machine:

```bash
mkdir -p ~/.config/jds-wiki
cat > ~/.config/jds-wiki/config.yml <<'EOF'
wiki: /absolute/path/to/your/wiki
EOF
```

The config file is per-machine and **not** part of the repo — filesystem layouts differ across machines.

## Layout

```
skills/                       # repo root
├── .claude-plugin/
│   ├── plugin.json           # plugin manifest (name: "jds")
│   └── marketplace.json      # marketplace manifest
├── commands/                 # review pipeline orchestrators
│   ├── review.md             # /jds:review
│   ├── fix.md                # /jds:fix
│   ├── walkthrough.md        # /jds:walkthrough
│   ├── promote.md            # /jds:promote
│   └── add.md                # /jds:add
├── fragments/                # review phase fragments + lens prompts
├── bin/                      # review helper scripts (auto on $PATH)
└── skills/                   # default skills directory
    ├── ingest/SKILL.md
    ├── lint/SKILL.md
    ├── ask/SKILL.md
    └── research/SKILL.md
```

Each folder under `skills/` containing a `SKILL.md` becomes a skill in the `jds:` namespace.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the standard frontmatter (`name`, `description`, `user-invocable: true`).
2. Commit and push.
3. On each machine: `/plugin update jds@jds`.
