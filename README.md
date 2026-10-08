# skills

A [Claude Code](https://claude.com/claude-code) plugin (`jds`) packaging the personal skills I use across machines, kept in version control.

Currently focused on the **jds-wiki** pattern (an LLM-maintained personal wiki). Skills:

- **`jds:ingest`** — `/jds:ingest <url-or-path>` — fetch a source, stage it in the wiki's `raw/`, then write/update wiki pages.
- **`jds:lint`** — `/jds:lint` — read-only health check (contradictions, orphans, gaps).
- **`jds:ask`** — `/jds:ask <question>` — answer from the wiki, with citations; offer to file the synthesis back.
- **`jds:research`** — `/jds:research <question>` — investigate a question against the codebase at the current working directory using parallel exploration; offers to file the synthesis to the wiki.

The wiki-touching skills resolve the wiki path from `~/.config/jds-wiki/config.yml` (single field: `wiki: <path>`). Default if missing: `~/Obsidian/Wiki`.

## Issue workflow

- **`jds:stage`** — `/jds:stage <issue>... [--onto <branch>]` — implement an issue in a worktree through subagents, adversarially review it, and stage it running for inspection before merge.
- **`jds:frontier`** — `/jds:frontier` — find the issue tracker's frontier issue — the first unblocked, non-terminal ticket in shipping order — and route it to the right next move.
- **`jds:workspace`** — `/jds:workspace <task naming a branch or PR>` — open a branch or PR in its own worktree and Herdr workspace, start a Claude agent there, hand it the task, and return.

## Other skills

- **`jds:split-pr`** — `/jds:split-pr` — break a very large pull request into a stack of small, independently-reviewable vertical slices whose cumulative diff is byte-identical to the original PR.
- **`jds:mbql-dictator`** — `/jds:mbql-dictator` — review a Clojure/ClojureScript diff for MBQL introspection: queries, clauses, refs, and column metadata may only be inspected or built through the public Lib API, never by digging into query data outside of Lib or the QP.
- **`jds:simplified`** — `/jds:simplified` — explain the provided input, or the last message in the conversation, in ASD-STE100 Simplified Technical English, with a little context.

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
└── skills/                   # default skills directory
    ├── stage/                # SKILL.md + herdr-recipes.md + review-lenses.md, agents/
    ├── frontier/SKILL.md
    ├── workspace/SKILL.md
    ├── split-pr/             # SKILL.md + REFERENCE.md, scripts/
    ├── mbql-dictator/        # SKILL.md + PATTERNS.md
    └── simplified/SKILL.md
```

Each folder under `skills/` containing a `SKILL.md` becomes a skill in the `jds:` namespace.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the standard frontmatter (`name`, `description`, `user-invocable: true`).
2. Commit and push.
3. On each machine: `/plugin update jds@jds`.
