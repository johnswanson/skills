---
name: ask
description: Ask a question against the user's wiki. Reads the wiki's index, opens relevant pages, synthesizes an answer with citations, and offers to file the answer back as a new wiki page. Invokable from any directory.
user-invocable: true
---

# /ask

Answer a question by reading the user's wiki — not by recalling from memory or searching the web. The argument is a free-form question.

## Step 0: Resolve the wiki path

Read `~/.config/jds-wiki/config.yml`. The `wiki:` field is the absolute path to the wiki folder. Resolve a leading `~` to `$HOME`. If the file doesn't exist or the field is missing, default to `~/Obsidian/Metabase`.

Throughout this skill, `$WIKI` refers to that resolved path. Key paths:

- `$WIKI/CLAUDE.md` — wiki conventions.
- `$WIKI/index.md` — content catalog (always your starting point).
- `$WIKI/log.md` — chronological log.
- `$WIKI/raw/` — raw sources (only open if the wiki doesn't have the answer).

If `$WIKI/CLAUDE.md` doesn't exist, stop and tell the user — the wiki isn't initialized at that path.

## Step 1: Load conventions

Read `$WIKI/CLAUDE.md` in full. It defines how to cite, how filing works, and what's in/out of scope for the wiki.

## Step 2: Read the index

Read `$WIKI/index.md` in full. This is your map of which pages exist and what they cover. Use the section structure and one-line summaries to pick the 1-5 most relevant pages for the question.

If the index doesn't obviously cover the question, scan `$WIKI/log.md` for recent ingests on related topics — sometimes a page exists but is poorly summarized in the index.

## Step 3: Read the pages

Read the pages you identified. Be willing to open more if the first batch points elsewhere. Stop when you have enough to answer — don't read the whole wiki.

If the wiki genuinely doesn't have the answer, say so directly. **Do not fall back to web search or memory unless the user explicitly asks** — the value of `/ask` is that it answers from the wiki. Offer one of:

- "Not in the wiki — want me to ingest a source about it?"
- "Not in the wiki — want me to answer from general knowledge instead?"
- "Not in the wiki — but `[[page-X]]` and `[[page-Y]]` are adjacent; want a partial answer from those?"

## Step 4: Synthesize the answer

Write a concise, well-structured answer. Conventions:

- **Cite by wikilink** — `[[Page Name]]` whenever a wiki page is the source. Never cite raw files (`raw/<file>`).
- **Quote sparingly.** Prefer your own concise synthesis. Quote only when the exact wording is load-bearing (a schema, a method signature, an API contract).
- **Use the wiki's structure.** If the user asks about a concept the wiki has a page for, lead with what that page says, then layer in cross-references.
- **Flag conflicts.** If two pages disagree, name the disagreement explicitly — don't paper over it.
- **Be honest about gaps.** If part of the question is answered and part isn't, say so.

Format the answer in chat (markdown is fine — the user has a Markdown-rendering terminal). Output the synthesis directly; don't write a wiki page yet.

## Step 5: Offer to file the answer (PAUSE)

After the answer, **proactively ask** whether to file it as a wiki page. The pitch is from the wiki pattern: synthesis answers compound the wiki. Phrase it like:

> "This synthesis pulls together [[Page A]] and [[Page B]] into a take that isn't on its own page yet. Want me to file it as `<suggested-page-name>` and link from [[Page A]] / [[Page B]]?"

Suggest skipping the filing offer only when the answer is trivial (a single fact lookup, a one-line definition) or already exists on a single existing page (in which case offer to *update* that page if your answer adds something).

Wait for the user's response.

### If the user accepts

Follow `$WIKI/CLAUDE.md` filing conventions:

1. Create the new page with frontmatter (`tags`, `sources: []` unless you cited raw files, `updated: <today>`).
2. Add `[[wikilinks]]` throughout where concepts appear.
3. Update `$WIKI/index.md` — add a line under the right section.
4. Update the existing pages you cited heavily — add `[[<new-page>]]` backlinks where natural.
5. Prepend a new entry to `$WIKI/log.md`, op = `file-answer`.

Report what you wrote and where.

### If the user declines

Move on. The answer remains in chat history; no log entry is needed.

## Things NOT to do

- Don't read raw sources before exhausting the wiki. The point of the wiki is to be the compiled answer.
- Don't fall back to web search or general knowledge without asking. Explicit > silent.
- Don't write to the wiki without confirmation. Synthesis happens in chat first; filing is opt-in.
- Don't modify pages you cited just to make your answer "fit better." If you find issues during reading, mention them at the end as "while I was in there, I noticed…" — let the user decide whether to fix.
