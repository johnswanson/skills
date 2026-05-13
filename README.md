# skills

User-global [Claude Code](https://claude.com/claude-code) skills, kept in version control so they can be installed on multiple machines.

Currently focused on the **jds-wiki** pattern (an LLM-maintained personal wiki — see [`idea.md`](https://github.com/) or wherever you keep the pattern doc). Skills:

- **`ingest/`** — `/ingest <url-or-path>` — fetch a source, stage it in the wiki's `raw/`, then write/update wiki pages.
- **`lint/`** — `/lint` — read-only health check (contradictions, orphans, gaps).
- **`ask/`** — `/ask <question>` — answer from the wiki, with citations; offer to file the synthesis back.

All three resolve the wiki path from `~/.config/jds-wiki/config.yml` (single field: `wiki: <path>`). Default if missing: `~/Obsidian/Metabase`.

## Bootstrap on a new machine

```bash
# 1. Clone the repo
git clone <this-repo> ~/projects/skills

# 2. Symlink each skill into Claude Code's discovery path
mkdir -p ~/.claude/skills
ln -s ~/projects/skills/ingest ~/.claude/skills/ingest
ln -s ~/projects/skills/lint   ~/.claude/skills/lint
ln -s ~/projects/skills/ask    ~/.claude/skills/ask

# 3. Point the skills at your wiki on this machine
mkdir -p ~/.config/jds-wiki
cat > ~/.config/jds-wiki/config.yml <<'EOF'
wiki: /absolute/path/to/your/wiki
EOF
```

The config file is per-machine and **not** part of the repo — filesystem layouts differ across machines.

## Layout

```
skills/
├── ingest/SKILL.md
├── lint/SKILL.md
└── ask/SKILL.md
```

Each skill is a folder containing a `SKILL.md` with YAML frontmatter (`name`, `description`, `user-invocable: true`). That's all Claude Code needs to register them.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the frontmatter shape above.
2. `ln -s ~/projects/skills/<name> ~/.claude/skills/<name>` on each machine.
3. Commit and push.
