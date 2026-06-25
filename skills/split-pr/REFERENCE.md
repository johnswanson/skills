# split-pr — mechanics & edge cases

## Mental model: a convergent sequence of valid states

The stack is a sequence of tree states `s0=<original-base> → s1 → s2 → … → sN`
(the base is the merge base, e.g. `origin/master` — not stale local `master`) where
every `si` compiles, lints, and tests, and `sN == original`. A slice is the
*transformation* `s(i-1) → si`, not a slice of the final diff.

This matters because an internally-valid intermediate state often **cannot** be
a subset of the final tree. The canonical case is `ns` `:require` forms: kondo
fails an unused require, so slice 1 may legally list `(:require bar)` while the
final lists `(:require bar baz bin)`. slice 1's content for that file appears
*nowhere* in the final diff — it's transitional, and that's correct. Same for
growing function arities, accumulating registration maps, exhaustive `case`
forms, and exports lists.

You build forward from the base PR (default `master`), authoring each slice directly. The tip equals the
original **because you make it so and verify it**, not because slices are
disjoint hunk-subsets. The verify step (`git diff <original> tip` empty) is the
proof.

Do **not** try to derive slices by reverting pieces of the squashed PR — it's
error-prone and easy to leave the tip non-identical.

## Plan presentation format (vertical slices)

Present the step-2 plan so a human can judge it fast. Group slices into named
**movements** (a short plain-language intro per movement), then one block per
slice. Keep each block scannable — newlines, not prose paragraphs — and explain
in plain language ("ELI5") what a user gets, not just which files move.

Per-slice block template:

```
## Slice N — <imperative title: the user-facing capability>
*One plain-language line: what a user can now do / see.*
- DB:      <migration files, or “—”>
- model:   <model files + registry entries>
- backend: <impl/logic files>
- API:     <endpoint files>
- FE:      <types, hooks, components>
- serdes:  <export/import + entity_id, folded in here>
- tests:   <which layers>
*Why here:* <dependency / ordering reason>          [enabling] if no standalone value
```

Omit layers a slice doesn't touch. Lead with **Slice 1 = walking skeleton**
(thinnest end-to-end path). After the slices, list: the two frictions (heavy
skeleton FE shell; repeatedly-touched wiring files), any possibly-separable
changes, and a one-paragraph vertical-vs-horizontal note if the user is choosing.

## Vertical vs horizontal — when to use which

Default to **vertical** (capability slices cutting DB→…→FE). Each slice is
demoable; reviewers see a whole feature. Costs: bigger cross-discipline slices
(backend + frontend in one review) and shared wiring files edited in many slices.

Fall back to **horizontal** (all backend slices, then all FE) only when the PR
won't slice vertically — e.g. a pure backend refactor with no UI, or layers so
entangled that every slice would drag in most of the diff. Its cost is that
nothing works until the last slice, so reserve it for cases where per-slice
demoability was never achievable anyway.

Either way the slices **stack** (see strategy in SKILL.md): migrations and shared
wiring impose a global order, so don't promise any-order independent merging.

## Carving a slice

**Evolving files (a file changes across several slices).** Note that this is the
most common case. You can't `git checkout` part of a file, and the intermediate
content you want is often *not* any subset of the final file. Author it directly:
Read the previous-slice version and the `<original>` version, then write the
version this slice needs to be internally valid. That may mean a shorter
`:require`, fewer map entries, or a narrower signature than the final. A
later slice grows it; the final sweep guarantees it lands exactly at
`<original>`. Avoid interactive `git checkout -p` — it can only produce
subsets of the final, which is often not what an intermediate state needs.

**Whole-file** Big PRs are often full of new files (new namespaces, new
components, new tests). When a new file belongs entirely to one slice, you may:

```bash
git checkout <original> -- path/to/new_namespace.clj path/to/Component.tsx
```

**Deleted-in-PR files**: `git rm path` on the owning slice. Renames: do the rename
on the slice that owns the moved code (`git mv`, or checkout the new path and
`git rm` the old).

## The final sweep (safety net)

The last slice always finishes with:

```bash
git checkout <original> -- .
git add -A && git commit -m "slice-N: <title>"
scripts/verify-identical.sh <original>   # must be ✅
```

This catches anything missed. If the sweep produces anything other than
whitespace changes, this is a strong signal that previous slices under-claimed.
Go re-balance or create new slices as necessary rather than shipping a giant
final slice.

## Satisfying the gates: transitional content is normal; minimize churn

Making each slice valid will require content that isn't in the final PR. Two
flavors, both legitimate:

- **Trimming** — a file is present but *smaller* than final: a `:require` with
  only the symbols used so far, a registration map with only this slice's
  entries, a function with only the args its current callers pass. This is the
  common, cheap case and adds little review churn.
- **Stubbing** — a placeholder that a later slice replaces (e.g. a fn referenced
  before its real implementation lands). Heavier; use when trimming + reordering
  can't make the slice valid.

Order of preference when slice K won't compile/lint/test:

1. **Reorder.** Move the dependency (shared util, schema, type, rename) into an
   earlier slice. The DAG from analysis tells you the legal orderings. Often
   removes the need for any transitional content.
2. **Trim.** Author the smaller-but-valid intermediate state (above).
3. **Stub.** Only when 1–2 can't. The stub must be fully overwritten before the
   tip. Note stubs in the plan — they add review churn.

In all three, `verify-identical` at the tip is what proves you converged. Keep
gratuitous divergence down (don't reshuffle a file just because you can), but
never contort the ordering to avoid *necessary* transitional content — that's
the whole point of giving slices their own valid states.

Test files travel with the code they test, because "tests green per slice"
otherwise forces awkward orderings. A test that exercises code from slices K and
K+2 belongs in K+2 (or is split).

## Bugs-found protocol

While slicing you will read the whole diff closely and may notice real bugs.
**Do not fix them** — the contract is an identical final state. Keep a running
list:

```
BUGS FOUND (not fixed — final diff preserved):
- <file:line> — <what's wrong> — <which slice surfaces it>
```

Report this list in step 5. The user decides whether to address any as
follow-ups. The only edits you make are those required to carve slices and
satisfy gates via reorder/trim/stub — never behavioral fixes.

## Edge cases

- **Migrations (Liquibase).** A migration slice must come before any slice that
  reads/writes the new columns. Keep changeSet `id`/`author` exactly as in the
  original (don't renumber). One migration per logical schema change makes a
  clean early slice.
- **Generated / lockfiles** (yarn.lock, deps, OpenAPI snapshots, i18n
  catalogs): assign to the slice whose code requires them, or a trailing
  "generated artifacts" slice. They don't count toward the conceptual-change cap.
- **Snapshot / fixture files**: travel with the feature that produces them.
- **Binary files**: `git checkout <original> -- <path>` works fine; just assign
  ownership.
- **Formatting-only churn** unrelated to the feature: isolate into a first
  mechanical slice (trivial to review) if it's large.
- **Cross-cutting renames** that touch hundreds of files: make them their own
  early mechanical slice so feature slices read cleanly.

## Stacked PRs (only when asked — this pushes)

After verification and explicit user confirmation:

```bash
git push -u origin slice-1 slice-2 ... slice-N
gh pr create --base master   --head slice-1 --title "..." --body "..."
gh pr create --base slice-1  --head slice-2 --title "..." --body "..."
# … each PR's base is the previous slice
```

Per the user's standing rules: never push or open PRs/comments without an
explicit ask. Building local branches in step 3 is fine; publishing is a
separate gated action.

## Sizing reference

- Conceptual change ≈ one idea a reviewer evaluates as a unit (a new endpoint, a
  schema, a hydration method, a component). Aim ≤ 3–5 per slice.
- LOC cap is a guide, not a law: a 900-line chunk that is one new self-contained
  namespace + its tests can be fine; a 300-line chunk touching 12 files across 4
  concerns is too big conceptually. Optimize for *reviewability*, not raw LOC.
