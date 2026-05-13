---
name: lint
description: Health-check the user's wiki — find contradictions, orphans, missing pages, missing cross-references, and knowledge gaps. Read-only; produces a report. Invokable from any directory.
user-invocable: true
---

# /jds:lint

Read-only health check on the wiki. Produces a report shown in chat and appended to the wiki's `log.md`. Does NOT auto-fix.

Optional argument: `--scope <topic>` to restrict the lint to pages tagged with or about that topic.

## Step 0: Resolve the wiki path

Read `~/.config/jds-wiki/config.yml`. The `wiki:` field is the absolute path to the wiki folder. Resolve a leading `~` to `$HOME`. If the file doesn't exist or the field is missing, default to `~/Obsidian/Wiki`.

Throughout this skill, `$WIKI` refers to that resolved path.

If `$WIKI/CLAUDE.md` doesn't exist, stop and tell the user — the wiki isn't initialized at that path.

## Step 1: Load conventions

Read `$WIKI/CLAUDE.md` in full. It defines what counts as "wiki" vs. "working memory," the frontmatter shape, the wikilink convention, and the log entry format. Lint operates on those rules.

## What's in scope

- All `.md` files at the root of `$WIKI/`.
- All `.md` files in topic subfolders inside `$WIKI/` (e.g. `Explorations/`, `Interviews/`).
- `$WIKI/index.md` itself (is it complete? does it match the actual files?).

## What's NOT in scope

- `$WIKI/current-work/` — working memory, not wiki. Skip entirely.
- `$WIKI/raw/` — sources are immutable. Don't critique them.
- `$WIKI/.claude/` — config, not content.
- `$WIKI/CLAUDE.md`, `$WIKI/log.md` — meta files.

## Checks

Run each in order. For each, list specific findings with file paths and 1-2 sentence rationale. Skip checks that found nothing — keep the report scannable.

### 1. Contradictions

Scan for pages making conflicting claims about the same entity, mechanism, or fact. Examples: two pages disagree on a schema, on a method name, on a behavior. Prioritize load-bearing claims (architectural decisions, data shapes) over stylistic ones.

For each: cite both pages with the conflicting sentences quoted.

### 2. Stale claims

A claim is stale if a newer source has likely superseded it. Heuristic: page A's `updated:` is far older than page B's `updated:`, and B describes the same area. Flag for review, not deletion.

### 3. Orphan pages

A page is an orphan if no other page in the wiki links to it (no `[[orphan-page]]` anywhere). Run a wikilink scan and report pages with zero inbound links.

`index.md` counts as inbound. Pages absent from `index.md` are a separate finding — see check 6.

### 4. Concepts mentioned but lacking a page

Find capitalized noun phrases or backticked symbols that appear repeatedly across pages but have no page of their own. Examples: data model entities, services, processes, important functions. Suggest candidates; list at most 5-10 of the most-mentioned.

### 5. Missing cross-references

Pages that mention a concept which DOES have its own wiki page, but don't use `[[wikilink]]` syntax. List up to 10 of the most-impactful misses.

### 6. `index.md` drift

- Wiki pages that exist but are not listed in `index.md`.
- Entries in `index.md` that point to pages that no longer exist.
- Sections in `index.md` that are bloated (>15 entries) or anemic (1 entry).

### 7. Frontmatter consistency

Pages that have frontmatter but are missing one of the documented fields (`tags`, `sources`, `updated`) — flag, don't fix. Pages without frontmatter at all are fine; don't flag unless they were created post-bootstrap.

### 8. Knowledge gaps suggesting new sources

Based on what's in the wiki and `log.md`, what's conspicuously absent? Examples: a feature mentioned everywhere but never explained; a system referenced by multiple pages with no page of its own; an architectural decision whose rationale isn't anywhere. Suggest concrete sources or web searches. List up to 5.

## Report format

Produce a single markdown report. Skip empty sections.

```markdown
# Lint report — YYYY-MM-DD

## Contradictions
- `page-a.md` vs `page-b.md` — <claim>. Suggested resolution: <…>

## Stale claims
- `page-x.md` — <claim>, likely superseded by `page-y.md`

## Orphan pages
- `page-z.md` — no inbound links

## Concepts mentioned but lacking a page
- `<concept>` — mentioned in `page-a.md`, `page-b.md`, `page-c.md`

## Missing cross-references
- `page-a.md` mentions <concept> in plain text; should link `[[<concept>]]`

## index.md drift
- Listed but missing: `<file>`
- Present but unlisted: `<file>`

## Frontmatter
- `page.md` has frontmatter but missing `sources:`

## Gaps / suggested sources
- <area> — consider clipping <source>; or searching for <query>
```

## After producing the report

1. Show the report in chat.
2. Prepend an entry to `$WIKI/log.md`:

   ```
   ## [YYYY-MM-DD] lint | <one-line headline summarizing the lint findings>

   <2-3 line summary: how many findings in each category, which one to act on first.>
   ```

3. Ask the user which findings (if any) they want to act on now. Do **not** apply fixes proactively — the user drives follow-ups.

## Things NOT to do

- Don't fix anything. v1 is report-only.
- Don't propose creating dozens of new pages — be selective.
- Don't lint `current-work/` or `raw/`.
- Don't critique a single page in isolation — the value of lint is the cross-page view.
