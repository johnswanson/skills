# skills

A [Claude Code](https://claude.com/claude-code) plugin (`jds`) packaging the personal skills I use across machines, kept in version control.

Currently focused on the **jds-wiki** pattern (an LLM-maintained personal wiki). Skills:

- **`jds:ingest`** — `/jds:ingest <url-or-path>` — fetch a source, stage it in the wiki's `raw/`, then write/update wiki pages.
- **`jds:lint`** — `/jds:lint` — read-only health check (contradictions, orphans, gaps).
- **`jds:ask`** — `/jds:ask <question>` — answer from the wiki, with citations; offer to file the synthesis back.

All three resolve the wiki path from `~/.config/jds-wiki/config.yml` (single field: `wiki: <path>`). Default if missing: `~/Obsidian/Metabase`.

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
    ├── ingest/SKILL.md
    ├── lint/SKILL.md
    └── ask/SKILL.md
```

Each folder under `skills/` containing a `SKILL.md` becomes a skill in the `jds:` namespace.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the standard frontmatter (`name`, `description`, `user-invocable: true`).
2. Commit and push.
3. On each machine: `/plugin update jds@jds`.
