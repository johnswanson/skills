---
name: research
description: Investigate a question about the codebase at the current working directory using parallel Explore agents. Synthesizes a markdown answer with file:line citations and offers to file the result as a wiki page.
user-invocable: true
---

# /jds:research

Research a question about the codebase at the current working directory. The argument is a free-form question — often with explicit facets ("How does X work? Pay particular attention to Y and Z").

## Step 0: Sanity-check the location

The current working directory is the codebase under investigation. If it doesn't look like a code project (no `.git/`, no obvious source files), say so and ask the user where to look instead. Otherwise proceed silently — don't narrate the check.

Also resolve the wiki path from `~/.config/jds-wiki/config.yml` (single field: `wiki: <path>`; default `~/Obsidian/Wiki`). This is only used in step 5.

## Step 1: Decompose the question into facets

Identify 2-4 facets the question is asking about. Some questions name them explicitly ("X, with attention to Y and Z"); others are one broad ask that needs sub-questions teased out.

State the facets in one short line so the user can redirect before you spend tokens — but don't pause. Move straight into step 2.

Example: for *"How do Explorations work in the codebase? Pay particular attention to the permissions system and how the job queue works"* the facets are:

1. Explorations — data model, lifecycle, key code paths
2. Permissions — how access is checked for Explorations
3. Job queue — how work is enqueued and processed

## Step 2: Investigate facets in parallel

Spawn one `Explore` agent per facet in a **single message** so they run concurrently. Each agent gets:

- A specific, narrow sub-question (not the full original question)
- A breadth hint: `"medium"` by default; `"very thorough"` if the facet is cross-cutting
- An explicit instruction to return file paths with line numbers (e.g. `apps/api/jobs/queue.ts:42`) for the most load-bearing locations

Don't grep yourself for things the agents are already chasing. Wait for all agents to return before moving on.

## Step 3: Read the load-bearing files

From the agents' returns, identify the small set of files that actually need to be opened (in full or in large chunks) to ground the answer. Read them with the `Read` tool.

If a facet came back thin (agent couldn't find much), say so in the synthesis rather than papering over it with general knowledge.

## Step 4: Synthesize the answer

Write a single markdown response. Required:

- **Lead with a one-paragraph summary** that answers the headline question.
- **Use `file:line` citations** for every load-bearing claim. Prefer the dedicated location format (`apps/api/jobs/queue.ts:42`) over prose like "in queue.ts around line 42".
- **Mirror the user's facets as section headings** so the answer maps cleanly onto what was asked.
- **Flag uncertainty explicitly** — if something is convention rather than enforced (e.g. "callers are expected to do X, but nothing checks it"), say so.
- **No preamble**, no restatement of the question, no "I will now…" — open with the summary.

Length: as long as it needs to be. A three-facet question typically lands in 300-800 words plus citations.

## Step 5: Offer to file the synthesis

End the chat response with a single short offer:

> Want me to file this as a wiki page? I'd suggest `<title>` under `<section>`.

If the user says yes, hand the synthesis to `/jds:ingest` as pasted content (the user will be prompted for a title there).

If the user says no, do nothing — the chat output is the deliverable.

## Edge cases

- **Agents return contradictory or partial info**: surface the contradiction in the synthesis rather than picking one silently. A footnote like "*two code paths exist; the older one in `lib/legacy/` may be unused — flagged for confirmation*" is fine.
- **The user follows up with a refinement** ("now dig into X"): re-run from step 2 with the narrower facets. Don't re-investigate what you already know.

## Things NOT to do

- Don't answer from general knowledge unless the agents came back empty and the user explicitly accepts that fallback.
- Don't invent file paths or line numbers. If you didn't read it, don't cite it.
- Don't sequence the Explore agents — fan-out is the whole point of this skill.
- Don't write to the wiki directly; route through `/jds:ingest` in step 5.
- Don't modify any code in the codebase. This is read-only research.
