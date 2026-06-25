---
name: split-pr
description: Break a very large pull request into a stack of small, independently-reviewable vertical slices whose cumulative diff is byte-identical to the original PR. Use when a PR/branch/diff is too big to review, or the user asks to split, chunk, stack, decompose, or carve up a large PR into smaller reviewable pieces.
---

# Split a large PR into reviewable slices

Turn one huge PR into a **stack** of small branches:

```
master ─ slice-1 ─ slice-2 ─ … ─ slice-N   (tip tree == original PR tree)
```

Each slice is a vertical slice a reviewer can hold in their head. The tip of
the stack is **byte-identical** to the original — splitting must never change
the final result.

## Slices are transformations, not subsets

A slice is **not** a subset of the final diff. Each slice transforms the tree
from the previous slice's valid state to a new valid state. Intermediate slice
routinely contain **transitional content that never appears in the final PR**,
because each slice must compile, lint, and test *on its own*.

For example, slice 1 may be about adding the CRUD API for a `foo`, while slice 2
is about some side-effect process that takes place after `foo`s are created. If
the final output looks like:

```clojure
(defendpoint :post "/foo/" [body]
 (let [foo (create-foo! body)]
  (do-some-side-effect! foo))
```

the intermediate state after slice 1 should be:

```clojure
(defendpoint :post "/foo/" [body]
 (create-foo! body))
```

and only after slice 2 will we add the `let`-binding and side effect.

Another example might be namespace `:requires` stanzas:

```clojure
;; final PR:           ;; slice 1 (only bar used yet):   ;; slice 2 (baz added):
(ns foo                (ns foo                            (ns foo
  (:require bar         (:require bar))                    (:require bar baz))
           baz          ;; listing baz now would          ;; bin still absent —
           bin))        ;; trip the unused-require lint    ;; arrives in a later slice
```

The same applies to a function signature that grows arguments across slices, a
registration/dispatch map that accumulates entries, an exports list, a `case`
that must stay exhaustive. Give each slice the freedom to be internally valid;
just guarantee the stack **converges** to the original at the tip.

## The three invariants (non-negotiable)

1. **Identical end state.** `git diff <original> <stack-tip>` is empty. Only the
   tip must match — intermediate slices are free to differ from the final.
2. **No fixes mid-flight.** If you spot a bug while slicing, **do not fix it** —
   that would change the final diff. Log it and report after completion (the
   user decides). See "Bugs-found protocol" in [REFERENCE.md](REFERENCE.md).
   (This is distinct from transitional content, which is *required*, not a fix.)
3. **Plan before cutting.** Present the slice plan and get approval before
   touching any branch.

## Per-slice gates

Every slice branch must satisfy all four before the next is built:

- **Compiles / lints / builds** — clj namespaces load, kondo is clean (no
  unused requires — a real constraint that forces transitional `:require` forms),
  TS builds. No references to not-yet-introduced code.
- **Tests green** — the slice's own tests pass on its branch (so test files
  travel with the code they cover).
- **Self-contained value** — a coherent vertical slice a reviewer understands.
  Pure-enabling foundation slices are allowed but labeled `[enabling]`.
- **Size cap** — default ≤ ~400–800 changed LOC and ≤ ~3–5 conceptual changes.
  Split further if exceeded. Confirm the cap with the user up front.

## How to slice: vertical, skeleton-first (the default)

**Strongly prefer vertical slices over horizontal layers.** A vertical slice
cuts top-to-bottom through one capability — a little DB + a little backend + a
little API + a little UI + its tests — so every slice is something you could
actually click on and demo. Horizontal layering (all backend slices, then all
frontend chunkss) is a **fallback** only for PRs that genuinely won't slice
vertically; its fatal flaw is that nothing works until the very end.

Rules of thumb for vertical slicing:

1. **Lead with a walking skeleton.** The first slice is the thinnest possible
   end-to-end path: one table, the core model(s), one create + one read endpoint,
   and one screen that shows the (empty) thing. It's unavoidably thin and may be
   `[enabling]`, but it stands up the pole every later slice hangs off.
2. **One capability per later slice**, bolted onto the skeleton top-to-bottom
   (its migration, model, backend logic, endpoint, FE, and tests together).
3. **Fold cross-cutting concerns into the slice that introduces them.** A model's
   serdes export/import, its registry entries, and its FE types land *in the same
   slice as the model*, not in a separate "serialization" or "types" slice.
4. **Vertical ≠ independent merge order.** Slices still **stack**: later slices
   will (and should!) very frequently depend on slices that came before them.
   Order by dependency; don't promise any-order merging.
5. **Expect two frictions** and plan for them: a big shared FE shell that the
   skeleton must carry (its FE slice is the heaviest), and shared wiring files
   that reviewers see touched repeatedly. Both are fine — they're the cost of
   vertical value.

See [REFERENCE.md](REFERENCE.md) for the plan presentation format (group slices
into named "movements", one block per slice, plain-language "what it does").

## Workflow

### 1 — Analyze
- **Fetch first, then diff three-dot against the *remote* integration branch:**
  `git fetch origin && git diff --stat origin/master...<feature>`. Three-dot
  (`...`) diffs from the merge base — exactly what a PR shows. **Do not trust
  local `master`**: it is often stale, and a two-dot diff against it can inflate
  the change 2–3× by folding in everything `origin/master` advanced. Confirm with
  `git rev-list --left-right --count master...origin/master` (left > 0 == stale).
  Call the merge base `<original-base>` and the feature tip `<original>`.
- Read the PR description / commits to learn the feature's sub-capabilities.
- Map the diff to **capabilities, not layers**: group files by the user-facing
  thing they serve (e.g. "create an exploration", "AI summary", "bookmarks"),
  spanning DB→model→backend→API→FE→tests. Note which files are shared *wiring*
  touched by many capabilities (model registries, `init`, serdes model lists,
  kondo config, the FE app shell) — these become transitional-content hotspots.
- Build a **dependency DAG**: what must land before what (migration before model
  use; shared util/type before consumers; rename before callers).
- Flag **possibly-separable / drive-by** changes (unrelated refactors, churn in
  shared core files) — candidates to split off as their own PRs, not in the stack.

### 2 — Plan (get approval)
- Carve the DAG into **vertical, skeleton-first slices** (see strategy above):
  walking skeleton, then one capability per slice, serdes/registry/types folded
  into the slice that introduces each model, glue + sweep last. Honor dependency
  order and the size cap.
- Present the plan grouped into named **movements**, one block per slice, each
  with: a plain-language "what it does", the layers it cuts (DB · model · backend
  · API · FE · serdes · tests) with the actual files/sizes, the gate commands,
  and `[enabling]` if it has no standalone value. Use the format in REFERENCE.md.
- Call out the two frictions (heavy skeleton FE shell; repeatedly-touched wiring
  files) and any possibly-separable changes so the user can decide scope.
- **Stop and get explicit approval.** Adjust until accepted.

### 3 — Execute (forward construction)
Build the stack from `<original-base>` (the merge base, e.g. `origin/master`)
forward. For each slice:
- Branch off the previous slice tip (slice 1 branches off `<original-base>`).
- Bring in its content. For files this slice owns whole (new namespaces,
  components, tests): `git checkout <original> -- <files>`. For files that evolve
  across slice: **author the correct intermediate state by hand** (read the
  previous-slice and `<original>` versions, then Write what this slice needs) —
  this may differ from the final, and that's expected.
- Run the four gates. If a slice can't be made valid, prefer to **reorder**
  (move a dependency earlier) over adding throwaway scaffolding; but accept
  necessary transitional content (partial requires, stubs, narrower signatures)
  — it converges at the tip. See REFERENCE.md.
- Commit. Move to the next slice.
- **Final slice** ends with a sweep — `git checkout <original> -- .` then commit —
  so anything unassigned lands here and the tip is guaranteed identical. A large
  sweep means earlier slices under-claimed; rebalance.

Track coverage with `scripts/split-status.sh <original>` (empty == done).
Do **not** push or open PRs unless the user explicitly asks.

### 4 — Verify
- `scripts/verify-identical.sh <original>` must print ✅. This proves invariant 1.
- Re-confirm each slice's gates if any rebalancing happened.

### 5 — Report
- Summarize the stack (slice → title → size → `[enabling]`?).
- List every bug found, with location, and confirm **none were fixed**. Ask
  whether to fix any now (as follow-ups), or leave the final state untouched.
- If the user wants stacked PRs, create them last with each PR's base set to the
  previous slice — only after explicit confirmation (this pushes).

## Mechanics, edge cases, shims, PR creation
See [REFERENCE.md](REFERENCE.md).
