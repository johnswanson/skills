---
name: ingest
description: Ingest a source (URL, file path, or pasted content) into the user's wiki. Fetches/copies the source into the wiki's raw/, then writes/updates wiki pages, the index, and the log. Invokable from any directory.
user-invocable: true
---

# /ingest

Ingest a new source into the wiki. The argument can be a URL, an absolute or relative file path, or a path already inside the wiki's `raw/`. You handle retrieval and filing — the user doesn't have to pre-stage anything.

## Step 0: Resolve the wiki path

Read `~/.config/jds-wiki/config.yml`. The `wiki:` field is the absolute path to the wiki folder. Resolve a leading `~` to `$HOME`. If the file doesn't exist or the field is missing, default to `~/Obsidian/Metabase`.

Throughout this skill, `$WIKI` refers to that resolved path. Concrete paths you'll use:

- `$WIKI/CLAUDE.md` — wiki conventions (read this in step 1).
- `$WIKI/index.md` — content catalog.
- `$WIKI/log.md` — chronological log.
- `$WIKI/raw/` — raw sources (staged sources land here).

If `$WIKI/CLAUDE.md` doesn't exist, stop and tell the user — the wiki isn't initialized at that path.

## Step 1: Load conventions

Read `$WIKI/CLAUDE.md` in full. It defines the naming, frontmatter, wikilink, and log conventions you'll follow. The rest of this skill assumes you've internalized that file.

## Default mode: interactive

Run these steps in order. Pause where indicated.

### 2. Retrieve and stage the source

Detect the argument shape and act accordingly:

- **URL** (`http://`, `https://`): use the `obsidian:defuddle` skill (preferred — strips chrome, saves tokens) to extract clean markdown. Fall back to WebFetch only if defuddle fails. Save to `$WIKI/raw/YYYY-MM-DD-<slug>.md`, where `<slug>` is a short kebab-case derivation of the article title (or URL path if no title).
- **Absolute path** outside `$WIKI/raw/` (e.g. `/home/jds/Downloads/foo.pdf`, `~/notes/transcript.txt`): copy the file into `$WIKI/raw/`, preserving the filename. PDFs copy as-is — Read can handle them.
- **Relative path** that exists in the current working directory: treat as a local file; copy into `$WIKI/raw/`.
- **Relative path** of the form `raw/<file>` or already-resolved path inside `$WIKI/raw/`: use directly, no copy.
- **Pasted content** (the user pastes a wall of text instead of a path): ask for a short title, save to `$WIKI/raw/YYYY-MM-DD-<slug>.md`.

If the source has inline image references, read the text first; offer to view specific images on request.

**Filename collision in `$WIKI/raw/`**: ask the user — overwrite, append a suffix (`-2.md`), or skip. Don't silently clobber.

Tell the user where you saved it (one line) before moving on.

### 3. Read the source

Read whatever you just staged. For large files (>50KB), see "Edge cases" below.

### 4. Read the wiki

- Read `$WIKI/index.md` in full.
- Skim or read pages the source clearly touches. Don't open everything — use the index summaries to scope.

### 5. Discuss takeaways with the user (PAUSE)

Output a short summary of the source (3-8 bullets), then call out:

- **Primary topic** — which wiki section this most belongs to.
- **Existing pages this touches** — list them with one-line rationale each.
- **New pages worth creating** — if any. Suggest titles; explain why.
- **Contradictions or updates** — anything in the source that disagrees with or supplements an existing page.
- **Open questions** — anything ambiguous you want guidance on before editing.

**Stop here and wait for the user's input.** Do not proceed until they've responded with guidance on emphasis, what to keep/skip, and which pages to update.

### 6. Propose the diffs (PAUSE)

Based on the discussion, lay out a concrete plan:

- New summary page (or new concept page): name, location, headings, frontmatter.
- For each existing page to update: a brief description of the change — not the full text.
- Index update: which section, what the new line says.
- Log entry: the exact line.

**Wait for the user to approve or revise.** Then proceed.

### 7. Apply the changes

- Create new pages with proper frontmatter (`tags`, `sources: [raw/<file>]`, `updated: <today>`).
- Update existing pages. Append to existing `sources` lists; bump `updated` when present. Don't add frontmatter to pages that don't already have it unless the user OKs.
- Add wikilinks where concepts appear.
- Update `$WIKI/index.md`.
- Prepend a new entry to `$WIKI/log.md` (newest first), op = `ingest`.

### 8. Report

A single closing message listing every file you created or modified, with a one-line note each. Flag anything you skipped or punted.

## Batch mode: `--batch`

If invoked as `/ingest --batch <args...>`:

- Skip step 5 (the discussion).
- Still do step 6 (propose diffs) — auto-approval is too risky.
- Compress step 8 into a single per-source summary.

Use batch only when the user has explicitly asked for bulk loading.

## Edge cases

- **Source is already ingested** (already in some page's `sources:` list): tell the user; ask whether to re-ingest (full reread) or skip.
- **Source is empty / unreadable / off-topic for the wiki**: don't force it. Report what you found and ask whether to keep, move, or delete the raw file. Don't move/delete unless explicitly told.
- **Source contradicts an existing page**: in step 5, surface the contradiction explicitly. In step 6, propose options ("keep existing, append new claim with a note" / "replace existing with new claim" / "leave both, flag for lint"). Let the user choose.
- **Source is huge** (>50KB): break the read into a structured pass — read in chunks, build a working outline before step 5. Don't try to ingest a book in one ingest call; suggest chapter-by-chapter.

## Things NOT to do

- Don't modify any file outside `$WIKI/` (except staging into `$WIKI/raw/`).
- Don't touch `$WIKI/current-work/` if it exists — that's working memory, not wiki.
- Don't bulk-rename existing pages for style consistency.
- Don't silently invent wikilinks to pages that don't exist. If a concept seems load-bearing and needs its own page, surface it as a "new pages worth creating" suggestion in step 5.
- Don't auto-resolve contradictions. Always ask.
