---
name: frontier
description: "Find the issue tracker's frontier issue — the first unblocked, non-terminal ticket in shipping order — and route it to the right next move. Use when the user wants the next ticket worked, asks what's next in the tracker, or says to work the frontier."
---

Find the **frontier issue** of the repo's issue tracker and route it.

Note that the issue tracker will never be on Github or Linear. You're looking for John's private issue tracker; if you can't find it, abort.

## 1. Find the frontier

The frontier is the first issue, walking features in shipping order and
issues by number, that is:

- **non-terminal** — not `done`, not `wontfix`; and
- **unblocked** — its `Blocked by:` line names nothing unfinished, and
  its feature's own gate (recorded in the feature's PRD or the issue)
  is satisfied.

Rules of the walk:

- Scope is the features the user names; absent that, every feature with
  open issues.
- Shipping order is whatever the PRDs or issues record as settled. If no
  order is recorded across the candidate features, present the leading
  candidate per feature and ask — don't invent an order.
- Scan `Status:` lines fresh from the files. Never trust a snapshot,
  handoff, or earlier conversation state — statuses change between
  sessions.

Done when: every issue ahead of the frontier in the walk is verified
terminal or blocked, and the frontier's own `Blocked by:` line and
feature gate are verified satisfied — a ticket blocked in halves counts
only for its unblocked half.

## 2. Route it by status

- **`needs-triage`** — the user's own placeholder capture. Hand them:
  `/triage <vault-path>`.
- **`ready-for-human`** — can't be delegated (for one example, maybe it
  needs a human grill session to flesh it out). Again, `/triage <vault-path>`.
- **`ready-for-agent`** — implementation happens via `/stage <issue>`;
  hand them that command. Don't substitute another implementation flow.
- **`needs-info`** — ask the blocking question.

## 3. Report

Name the frontier issue (vault path), its status, what the walk
verified (what's done, what's blocked and by what), and the exact
command to run next. If the walk found a ticket whose status no longer
matches reality — half shipped, superseded — say so and propose the fix
(e.g. split it into a done ticket and a blocked one) rather than
silently routing past it.
