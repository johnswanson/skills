---
allowed-tools: Bash(artifact-read.sh:*), Bash(artifact-patch.py:*), Bash(artifact-validate.sh:*), Bash(artifact-render.py:*), Bash(artifact-publish.sh:*), Bash(claude-md-paths.sh:*), Bash(staleness.sh:*), Bash(external-scrape.sh:*), Bash(comment-freshness.sh:*), Bash(prior-fix-diff.sh:*), Bash(line-range-check.sh:*), Bash(assign-finding-ids.sh:*), Bash(origin-crosscheck.sh:*), Bash(parse-with-repair.py:*), Bash(parse-validator-result.py:*), Bash(source-family-map.py:*), Bash(log-phase.sh:*), Bash(log-tokens.sh:*), Bash(tally-subagent-tokens.sh:*), Bash(orchestrator-tokens.sh:*), Bash(repo-slug.sh:*), Bash(freshness-gate.sh:*), Bash(trivial-check.sh:*), Bash(artifact-seed.sh:*), Bash(git:*), Bash(gh pr view:*), Bash(jq:*), Bash(date:*), Bash(mkdir:*), Bash(mv:*), Bash(rm:*), Bash(mktemp:*), Bash(cat:*), Bash(printf:*), Bash(echo:*), Bash(grep:*), Bash(awk:*), Bash(sed:*), Bash(tr:*), Bash(wc:*), Bash(head:*), Bash(tail:*), Bash(cut:*), Bash(sort:*), Bash(diff:*), Bash(openssl:*), Bash(python3:*), Bash(find:*), AskUserQuestion, Agent, Read
argument-hint: "[--scrape-pr-comments] [--holistic] [--full]"
description: Deep multi-lens local code review producing artifact.json and artifact.md under ~/.jds-reviews. Never writes to GitHub.
disable-model-invocation: false
---

Flags (optional):
- `--scrape-pr-comments` adds Phase 1.5: a read-only scrape of
  bot-authored comments on this branch's GitHub PR (if one exists),
  normalized into review candidates. Reads GitHub; never writes to it.
- `--holistic` adds the L7 holistic lens to Phase 1 — a checklist-free
  skeptical read of the whole diff. Off by default; costs roughly
  1.5–2x an L2 pass.
- `--full` forces `trivial_mode=false` for this run (overrides the
  doc/config-change early-exit).

**Read `fragments/_prelude-shared.md` before proceeding — it lists
rules that apply to every phase below (sub-agent return handling,
helper-script error-as-prompt).**

## Execution overview

This command orchestrates Phases 0–6 in order. Each phase is
defined in a fragment under `fragments/NN-<name>.md`. At each phase
boundary below, read the named fragment with the `Read` tool and
execute the instructions inside before proceeding to the next phase.

**Before you start, build a TaskList that mirrors the phases below**
(one task per phase, plus one for argument parsing). Mark each
`in_progress` when you start it and `completed` when you finish.

If a phase genuinely cannot run, mark the task `completed` with a
one-line `trace.md` note and move on. Phase 6 (finalize) runs
unconditionally — a partial review is still worth rendering so the
user can inspect what did succeed.

Sub-agent failures (non-zero, unparseable output, timeouts) get
logged to `trace.md` and drop that candidate from the run — they
don't abort the whole command.

## Sub-agent dispatch pattern

Every Agent tool-use specifies:
- `subagent_type: general-purpose`.
- `model:` explicitly — `haiku`, `sonnet`, or `$high_model` per the
  fragment's instructions. `$high_model` is the deep-lane model
  resolved in Phase 0 step 0.1 from `JDS_REVIEW_HIGH_MODEL`
  (default `fable`; `opus` and `sonnet` are valid overrides).

**Parallel fan-outs** happen by firing multiple Agent tool-use blocks
in a single orchestrator turn. Always batch within one turn.

## Argument handling

Parse `$ARGUMENTS` (whitespace-split) for:
- `--scrape-pr-comments` → `scrape_mode=true` (else `false`)
- `--holistic` → `holistic_mode=true` (else `false`)
- `--full` → `force_full=true` (else `false`)
- Any other token → stop and ask the user to clarify.

Capture all three in your working context before executing Phase 0.

---

**Phase 0 — Preflight.** Read `fragments/00-preflight.md` and execute
the instructions inside before proceeding to Phase 1.

---

**Phase 1 — Detection.** Read `fragments/01-detection.md` and execute
the instructions inside before proceeding to Phase 1.5.

---

**Phase 1.5 — PR-comment scrape (conditional).** If
`--scrape-pr-comments` was passed, read `fragments/02-scrape-adapter.md`
and execute the instructions inside; otherwise skip to Phase 2. (Phase
1's join step at 01-detection.md 1.5 may have already executed it — if
`external_candidates` is already set, proceed straight to Phase 2.)

---

**Phase 2 — Dedup.** Read `fragments/03-dedup.md` and execute the
instructions inside before proceeding to Phase 3.

---

**Phase 3 — Scoring gate.** Read `fragments/04-scoring-gate.md` and
execute the instructions inside before proceeding to Phase 4.

---

**Phase 4 — Validation.** Read `fragments/05-validation.md` and execute
the instructions inside before proceeding to Phase 5.

---

**Phase 5 — Cross-cutting.** Read `fragments/06-cross-cutting.md` and
execute the instructions inside before proceeding to Phase 5.5.

---

**Phase 5.5 — Auto-fix-hint generation.** Read
`fragments/06b-auto-fix-hint.md` and execute the instructions inside
before proceeding to Phase 6.

---

**Phase 6 — Finalize.** Read `fragments/07-finalize.md` and execute
the instructions inside.

---

## What this command does NOT do

- No writes to GitHub of any kind — no comments, no pushes, no edits.
  GitHub access is read-only and only happens under
  `--scrape-pr-comments` (plus the optional fetch in Phase 0's
  freshness gate).
- No git operations that mutate history or remotes. No commits, tags,
  branches, pushes, deletes, or renames anywhere in the working tree
  (the optional Phase 0 stash/pop is the only tree mutation).
