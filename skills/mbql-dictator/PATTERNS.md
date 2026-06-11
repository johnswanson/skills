# MBQL Introspection — pattern catalog

Each entry: how to spot it (grep hints), why it's a violation, and the blessed Lib remedy. Always read context — many of these tokens are innocent on app-db rows, QP *result* maps, or inside lib/lib-be/qp itself. The sin is digging into a **query** (MBQL) or a **column-metadata map** outside Lib.

## 1. Reading raw query / clause structure (hardest)

**Spot:** `get-in`/`get`/`assoc-in`/`update-in`/`select-keys` with query keypaths; destructuring or keyword-access of query internals.
```
\(:query |\(:database |\(:aggregation |\(:breakout |\(:filter |\(:source-table |\(:source-query |\(:joins |\(:expressions
get-in .*\[:query|assoc-in .*\[:query|\[:stages
\(first .*clause\)|\(= :and|\(= :field|case .*\(first
```
**Why:** Out here, nobody should know a query *has* these keys, or that clause tags like `:and`/`:field`/`:=` exist. This couples the whole codebase to MBQL's internal shape.
**Remedy:** Go through Lib. Get a query with `lib/query`, then `lib/aggregations`, `lib/breakouts`, `lib/filters`, `lib/joins`, `lib/order-bys`, `lib/stage-count`, `lib/database-id`, etc. Never read the key directly.

## 2. Reading column-metadata keys directly

**Spot:** keyword access of metadata-column keys on something that came from `returned-columns`/`visible-columns`/`breakoutable-columns` or from a result.
```
\(:lib/source |\(:base-type |\(:base_type |\(:effective-type |\(:effective_type |\(:semantic-type |\(:semantic_type |\(:field_ref |\(:field-ref |:fingerprint
```
**Why:** `:lib/source` "only tells part of the story about where a column came from"; consuming these keys directly makes it impossible to evolve Lib metadata. Nested `:fingerprint` paths (`[:fingerprint :type :type/Number :min]`, `[:fingerprint :global :distinct-count]`) have **no public accessor** — that's a Lib gap to raise, not a license to dig.
**Remedy:** Type questions → `metabase.lib.types.isa` (`isa?`, `temporal?`, `numeric?`, `boolean?`…). Display → `lib/display-name`. Bucket/binning → `lib/raw-temporal-bucket`, `lib/binning`, `lib/available-binning-strategies`. Source role → ask Lib for an accessor rather than reading `:lib/source`. If no accessor exists, **propose one in Lib.**

## 3. Building MBQL clauses by hand

**Spot:**
```
\[:field |\[:= |\[:and |\[:or |\[:expression |\[:aggregation |\[:time-interval
expression-clause|mbql.u/|mbql\.|->legacy-MBQL
```
**Why:** Hand-built clause vectors and low-level constructors (`expression-clause`) bypass Lib's invariants. *"It's definitely better to use Lib functions like `lib/and` to construct clauses but it's even better not to be constructing MBQL clauses outside of Lib at all."*
**Remedy:** `lib/and`, `lib/or`, `lib/not`, `lib/=`, `lib/filter`, `lib/expression`, `lib/with-temporal-bucket`, `lib/with-binning`, `lib/breakout`, `lib/order-by`, `lib/aggregation-ref`, `lib/expression-ref`. To collapse compound filters: `(lib/simplify-compound-filter (apply lib/and clauses))`. If you're assembling something Lib can't express, that capability belongs *in* Lib.

## 4. Hand-rolled normalization / conversion

**Spot:** manual cleanup of a stored/legacy query — keywordizing, stripping namespaces, `mbql.normalize`, ad-hoc `->mbql5`/`->legacy-MBQL` chains, or `(:database dq)` to bootstrap a metadata provider.
**Why:** This re-implements (incompletely) what Lib already does, and any per-clause normalization gap should be fixed *in Lib*, not patched around it.
**Remedy:** `lib-be/normalize-query` combines all of these operations. To get the database id from a query, `lib/database-id`. If a stored query needs a metadata provider before it can become a lib query, that bootstrap path belongs in `lib-be` — raise it.

## 5. Off-label Lib use

**Spot:** calls to functions whose `metabase.lib.core` docstring is marked `Smelly`, `Single use`, `Leak`, or `Deprecated`; or any code that traffics in field-refs (refs are "a code smell" per the lib core docstring).
**Why:** these are exported but not blessed for new callers; new uses need justification.
**Remedy:** check the docstring's **Code Health** line. Prefer a `Healthy` alternative. If only a `Single use`/`Leak` fn does what you need, that's a signal Lib is missing the right API — flag it for the Querying team.

## Quick triage grep

Run against the kept (non-lib/qp) changed files, then read each hit in context:
```bash
grep -nE '\(:query |\(:database |\(:aggregation |\(:breakout |\(:filter |\(:source-table |\(:source-query |get-in.*\[:query|assoc-in.*\[:query|\[:stages|\(first [a-z-]*clause|\(= :(and|or|field|=)|\(:lib/source|\(:base-?type|\(:effective-?type|\(:semantic-?type|:field-?ref|:fingerprint|\[:field |\[:= |\[:and |expression-clause|mbql\.u/|mbql/normalize' <files>
```
A hit is *evidence*, not a verdict — confirm it's touching a query/metadata map (not a QP result `:cols`, not an app-db row) before you rule.
