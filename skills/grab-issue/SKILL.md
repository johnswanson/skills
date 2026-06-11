---
name: grab-issue
description: Pick up an issue from the project's issue tracker and work it end-to-end — plan it with the grill-with-docs skill, implement it with the tdd skill, then close out the issue and commit. Use when the user wants to grab, pick up, or work an issue, start the next issue, or take a ticket from selection through implementation.
user-invocable: true
---

# /jds:grab-issue

Work one issue from the current project's tracker end-to-end: select → plan (grill-with-docs) → implement (tdd) → close out and commit.

The argument is optional and free-form: an issue path, issue number, or feature slug to work on, and/or selection guidance (e.g. "just start, no confirmation", "only ready-for-agent issues").

## Step 1: Resolve the project's issue tracker conventions

Look for issue tracker documentation in the project — check `CLAUDE.md` and anything it points to (e.g. `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`). Follow those conventions for locating, reading, and updating issues throughout this skill.

If the project has no documented issue tracker, stop and ask the user where issues live.

## Step 2: Select an issue

- If the argument names a specific issue, use it.
- Otherwise, scan the tracker for open issues (anything not done/closed/wontfix). Skip issues blocked on information (`needs-info`). **Do not filter on `ready-for-agent` vs `ready-for-human`** — both are equally grabbable unless the user's prompt says otherwise.
- Respect ordering: issue numbering and any stated dependencies indicate intended sequence. Prefer the earliest unblocked issue in an in-progress feature over starting a new feature.
- **Default: recommend and confirm.** Present the pick with a one-line rationale (and the runner-up, if there's a plausible alternative) and wait for the user's go-ahead. If the prompt says to just start, skip the confirmation.

Once selected, mark the issue in-progress per the tracker's conventions (e.g. its `Status:` line) so a parallel agent doesn't grab it too.

## Step 3: Plan with grill-with-docs

Read the issue file fully, plus its surrounding context: the feature's PRD if one exists, sibling issues, and any comments at the bottom of the file.

Then invoke the `grill-with-docs` skill via the Skill tool, seeding it with the issue as the plan under interrogation. That skill drives an interactive interview: challenge the issue's approach against the codebase and domain docs, resolve open decisions one at a time, and update `CONTEXT.md`/ADRs inline as decisions crystallise.

When the grilling converges:

- If scope or approach materially changed, update the issue file body to reflect the real plan before implementing.
- Carry the resolved decisions forward as the spec for implementation.

## Step 4: Implement with tdd

Invoke the `tdd` skill via the Skill tool and implement the plan: vertical slices, red-green-refactor, one test → one implementation → repeat. The decisions from Step 3 define the behavior under test.

## Step 5: Close out

1. Run the project's full test suite. Only proceed once green — if something fails, fix it first (or report honestly and stop if blocked).
2. Update the issue file: set its status to done per the tracker's conventions, and append a comment (e.g. under `## Comments`) summarizing what shipped and any decisions that diverged from the original issue text.
3. Commit on the current branch: implementation, issue file update, and any doc updates from Step 3 together. Follow the repo's existing commit message style and reference the issue in the message.

If either the `grill-with-docs` or `tdd` skill is not installed on this machine, say so before starting and ask whether to continue with an inline approximation of it.
