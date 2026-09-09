# Implementer brief (`stage` step 2)

For the orchestrator. Paste everything below the rule into the Opus implementer's prompt and replace
every `{placeholder}`. Attach documents; do not merely name them.

- `{issue-ref}` — tracker id and title, plus the issue body verbatim: what to build, design, acceptance criteria.
- `{worktree}` — absolute path of the worktree you pre-created; `{branch}` — the ticket branch checked out there.
- `{integration-branch}` — the branch this merges into, or `none` if the issue ships alone.
- `{file-pointers}` — absolute paths (with line ranges) the work starts from.
- `{project-docs}` — spec, PRD, ADRs, glossary/context docs.
- `{worktree-recipe}` — the project's worktree/dev-env/test doc, attached in full. For Metabase that is
  `Projects/Metabase/worktrees.md` in the vault. Rules under "Environment and tests" bind to it; without
  it they say nothing.

Delete the Metabase block for other projects.

---

Implement {issue-ref}. The issue, its spec and context docs, and the worktree recipe are attached.

Issue: {issue-ref}
Worktree: {worktree} (branch `{branch}`, integrating into `{integration-branch}`)
Start here: {file-pointers}

## Where you work

Work only inside `{worktree}`, by absolute path, always. Do not call `EnterWorktree` — it is refused for
subagents with a pinned cwd, and wastes a turn. Commit to `{branch}` as you go. Never push, never touch
another worktree, never touch main.

## Environment and tests

Follow the attached worktree recipe for the dev environment and for running tests. If it gives a test
wrapper, invoke that wrapper by absolute path and never the project's own test command directly: the dev
env's generated env file overrides the test alias, so a direct run binds the dev port and executes
against the live dev app database.

## Process

Use /tdd wherever a seam allows it: a failing test first, then the code. Run the single test namespace
you are working on often; run the full relevant module once, at the end. Typecheck or lint as the
project documents.

## Evidence, not self-report

Your final report contains a table with one row per acceptance criterion:

| Test (ns/name) | Criterion | Mutation applied | Confirmed failed |

The mutation is a change you actually made and ran — revert the production change, or flip the predicate
— to watch that test go red, then undo. A test you never saw fail is not evidence that it covers
anything. The orchestrator hands this table to an adversarial reviewer who treats it as untrusted.

## Tests must exercise the real path

Build request maps and fixtures that actually contain the key under test; a request map missing the
filter key satisfies any assertion about it for the wrong reason. When a model hook would short-circuit
the thing you are testing, go around the hook: deactivating a user through the User model deletes their
sessions, so a test that deactivates that way never exercises a session-liveness predicate — write the
row through the raw table instead, and say in a `;;` comment why the test bypasses the model.

## Cross-database behaviour

Any behaviour the spec relies on that databases implement differently — NULL ordering, `LEAST` /
`COALESCE`, case sensitivity — gets a test on each app DB the recipe supports. If you do not run one of
them, say so explicitly in the report; silence reads as coverage.

## Comments and docstrings

Docstrings state the contract for the caller. Design rationale, rejected alternatives, and "why this
way" go in `;;` comments beside the code, or in the commit message.

## Schemas

Response schemas are closed unless the spec says otherwise, so a field cannot reach the client without
having been reviewed.

## Module boundaries

To reach a var in another module, re-export it through that module's public `.core` namespace (or
whatever the project's module doc prescribes). Do not widen an `:api` set, and never add a whole
namespace to the surface to reach two vars.

## Optional scope

Anything the issue marks optional is off by default. Take it only after checking its premise against the
code — an optional index migration once duplicated indexes the engines already create for foreign keys,
and was reverted in review. If you take it, name it in the report; if you decline it, say why.

## Parallel-branch etiquette

`{integration-branch}` may be receiving sibling branches at the same time. Keep edits to shared files
additive and inside a delimited block, one block per issue, commented with the issue ref. Leave
`:details`-style maps and enum sets open so siblings merge textually. Do not reformat, reorder, or
re-sort code you did not otherwise need to touch — it turns a clean merge into a conflict.

## Report

End with: what you built; the evidence table; design calls you made beyond the spec; optional scope taken
or declined and why; anything left undone with the reason.

## Metabase

- Docstring versus `;;` comment: follow `.claude/skills/clojure-write/SKILL.md`, "Writing Docstrings".
  Read it; do not re-derive it.
- Module boundaries: `CLAUDE.md`, "Module Boundaries". After any change that shifts them, run
  `./bin/mage fix-modules-config`, then `./bin/mage project-tests modules`.
- Fix kondo warnings rather than suppressing them, and do not lower budgets in `.clj-kondo/ratchets.edn`
  on a feature branch (`CLAUDE.md`, "Kondo Ignore Ratchets").
- App DBs for the cross-database rule: H2, Postgres, MySQL. The recipe says how to reach each.
- Add an API changelog entry when the issue changes an endpoint's contract.
