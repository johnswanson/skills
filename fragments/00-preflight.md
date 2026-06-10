## Phase 0 — Pre-flight

This phase is mostly deterministic shell — the only LLM call is the Sonnet
user-facing-change classifier (step 0.12), and that's skipped in trivial mode.

**Run every Bash command in this phase in the foreground — do NOT use
`run_in_background`.** Phase 0's output (branch detection, dirty-tree
status, freshness prompts) is consumed inline by later steps and by
`AskUserQuestion` dispatches; backgrounded shells leave the orchestrator
unable to read the output and the session stalls on a variable that
never gets assigned.

Work through the steps below in order. Capture each named variable into
your working context — later phases will reference them by name ("the
`review_id` captured in Phase 0").

### 0.1. Resolve argument flags and the deep-lane model

Parse `$ARGUMENTS` for `--scrape-pr-comments`, `--holistic`, and
`--full`. Set `scrape_mode=true/false`, `holistic_mode=true/false`,
and `force_full=true/false` in your context.

Any token not recognized as one of those three flags is unexpected —
stop and ask the user to clarify.

Then resolve the deep-lane model — the model used for every dispatch
the fragments mark as `model: $high_model` (L2/L7 lenses, Phase 4a
deep-lane validators, Phase 5 cross-cutting):

```bash
high_model="${JDS_REVIEW_HIGH_MODEL:-fable}"
case "$high_model" in
    fable|opus|sonnet|haiku) ;;
    *)  echo "JDS_REVIEW_HIGH_MODEL='$high_model' is not a recognized model (fable|opus|sonnet|haiku) — using fable." >&2
        high_model=fable ;;
esac
```

Capture `high_model` in your working context. If the fallback branch
fired, also surface the one-line warning to the user in chat.

### 0.2. Resolve branch, base, and repo root

Run:

```bash
head_branch=$(git rev-parse --abbrev-ref HEAD)
repo_root=$(git rev-parse --show-toplevel)
```

Capture `head_branch` and `repo_root`.

For `base_branch`, try in order:

1. `git symbolic-ref --short refs/remotes/origin/HEAD` (strip the `origin/`
   prefix).
2. Probe `main`, then `master` via
   `git show-ref --verify --quiet refs/heads/<name>` or
   `refs/remotes/origin/<name>`. Use the first that resolves.
3. If neither resolves, stop and ask the user to rerun with explicit base
   (future flag; for now, tell them which refs you tried).

Capture `base_branch`.

### 0.2a. Reconcile base-branch freshness (§13.10)

Phase-0 invariant preventing stale-local-`base_branch` runs from poisoning
downstream lenses / blame. `freshness-gate.sh` owns remote detect, fetch,
and behind-count; orchestrator owns `AskUserQuestion`.

```bash
# Initialize preflight_warnings ONCE — prior-call warnings must survive
# across a --after-choice re-invocation. The jq-extraction loop below
# runs after EACH freshness-gate.sh call (first + any --after-choice)
# and appends; it must not reset the array.
preflight_warnings=()

fg_out=$(freshness-gate.sh --base-branch "$base_branch" --head-branch "$head_branch")
comparison_ref=$(echo "$fg_out" | jq -r '.comparison_ref // empty')
base_freshness=$(echo "$fg_out" | jq -r '.base_freshness')
remote_sha=$(echo "$fg_out" | jq -r '.remote_sha // empty')
behind_count=$(echo "$fg_out" | jq -r '.behind_count // empty')
while IFS= read -r w; do
    [[ -n "$w" ]] && preflight_warnings+=("$w")
done < <(echo "$fg_out" | jq -r '.preflight_warnings[]?')
```

First four values feed `base_context` at 0.15; `preflight_warnings` flushes
to `trace.md` at 0.15 (after `trace_log_path` exists). If `base_freshness ==
"pending_user_gate"`, ask the user — offer (a) Fast-forward local `$base_branch`
[drop when `ff_available: false`], (b) Compare against `origin/$base_branch`,
(c) Proceed with stale local `$base_branch` (discouraged), (d) Abort; include
`behind_count` in the prompt. Re-invoke `freshness-gate.sh ... --after-choice
<a|b|c>` and re-run the **same jq extractions** on the new `fg_out` — do NOT
reset `preflight_warnings` (the array is initialized once above); the while
loop appends any additional warnings to the prior-call set. A second
`pending_user_gate` (non-FF on (a)) re-asks with only (b)/(c)/(d). (d) exits 0
with a one-line message — no `review_dir` exists yet.

**Sanity check (against `comparison_ref`):**

```bash
if [[ "$(git rev-list --count "$comparison_ref..HEAD")" -eq 0 ]]; then
    echo "No commits to review on $head_branch relative to $comparison_ref. Nothing to do." >&2
    exit 0
fi
```

### 0.3. Derive repo slug

Delegate to the canonical helper (single source of truth shared with
Phase 7's fix-loader so the two paths cannot drift):

```bash
repo_slug=$(repo-slug.sh --repo-root "$repo_root")
```

Capture as `repo_slug`.

### 0.4. Locate the PR for scraping (read-only; `scrape_mode` only)

This command always runs in local mode — `mode=local`, `pr_state=""`,
`pr_number=""`, `pr_author=""` (empty-string sentinels; the `${var:-}`
expansions at step 0.15's `artifact-seed.sh` call turn `""` into JSON
null. Do NOT use the literal string `null` — the helper rejects it at
argument validation). The artifact is never published anywhere;
GitHub is never written to.

When `scrape_mode == true`, additionally locate the PR whose bot
comments Phase 1.5 will scrape. Run
`gh pr view --json number,state,headRefName` (no PR arg — picks up
the PR for the current branch if any).

- If the command succeeds and returns an open or draft PR whose
  `headRefName == head_branch`: capture `scrape_pr_number` (working
  context only — NOT written to the artifact; the artifact stays
  `mode=local` with `pr_number: null`).
- In every other case — no PR found, closed/merged PR, headRefName
  mismatch, or any `gh` error (auth, network) — set
  `scrape_mode=false`, append a one-line entry to
  `preflight_warnings[]` (e.g. `scrape_disabled reason=<no-pr|closed|
  branch-mismatch|gh-error>`), tell the user in one line that the
  scrape was disabled and why, and continue. A scrape problem never
  aborts a local review.

When `scrape_mode == false` (not passed, or just disabled), skip the
`gh` call entirely.

### 0.5. Capture `review_started_at`

Run `date -u +%Y-%m-%dT%H:%M:%SZ` and capture as `review_started_at`.
This is the review's start time — consumed by Phase 6 `metrics.time_elapsed_seconds`
for cost-vs-size tracking.

### 0.6. Compute `reviewed_files_all`, `num_files`, and `lines_changed`

Run (using `$comparison_ref` — §13.10 — not `$base_branch`; the two
differ when the freshness gate resolved to option (b) `used_remote_ref`,
in which case `comparison_ref = "origin/$base_branch"`):

```bash
reviewed_files_all=$(git diff --name-only "$comparison_ref..HEAD")
num_files=$(printf '%s\n' "$reviewed_files_all" | grep -c . || true)
lines_changed=$(git diff --shortstat "$comparison_ref..HEAD" | \
  awk '{insertions=0; deletions=0; for(i=1;i<=NF;i++){if($i ~ /insertion/){insertions=$(i-1)}else if($i ~ /deletion/){deletions=$(i-1)}}; print insertions+deletions}')
# Fallback if awk path fails: lines_changed=0.
[[ -n "$lines_changed" ]] || lines_changed=0
```

Capture `reviewed_files_all` (newline-separated list — pass through stdin
with `@-` to scripts that accept it; join with commas when a CSV arg is
expected). Capture `num_files` and `lines_changed` as integers; they're
used by step 0.11 (trivial check) AND by step 0.15 (seed's
`pr_size_buckets`) AND by Phase 6's `metrics` block. Compute them here
unconditionally — if step 0.11 is skipped by `--full`, these still need
to exist.

### 0.6a. Branch-behind-base advisory

Step 0.2a already attempted a fetch, so this is passive — `$comparison_ref`
is whatever ref freshness-gate.sh produced (which may still be local on
`no_remote` / `no_fetch`). When HEAD is behind it, the lens diff includes
phantom deletions for code that landed on the base after this branch was
cut. When `$comparison_ref` doesn't resolve to a count at all, append a
`branch_behind_base unresolvable` entry to `preflight_warnings[]` (flushed
at §0.15 into the artifact) so an operator inspecting the artifact later
can distinguish a genuinely-up-to-date branch (`behind=0`) from a
silently-degraded gate (also `behind=0`).

```bash
if behind=$(git rev-list --count "HEAD..$comparison_ref" 2>/dev/null); then
    :  # behind already populated
else
    behind=0
    preflight_warnings+=("branch_behind_base unresolvable comparison_ref=$comparison_ref")
fi
```

If `$behind > 0`, `AskUserQuestion` once:

> Branch `$head_branch` is `$behind` commits behind `$comparison_ref`
> (the diff base for this review). The lens diff includes phantom
> deletions for code that landed on `$comparison_ref` after this branch
> was cut, and may have shifted code your branch calls into. Recommend
> merging `$comparison_ref` into `$head_branch` first — this updates
> your feature branch tip, separate from any earlier diff-base choice.

- **(a) Stop — I'll merge `$comparison_ref` into `$head_branch` first, then re-run.** Exit 0 with: `Stopping. Run \`git merge $comparison_ref\` (or fast-forward) on \`$head_branch\`, then re-run /jds:review.` (No `review_dir` exists yet — nothing to clean up.)
- **(b) Proceed.** Append a buffered warning and continue:
  ```bash
  preflight_warnings+=("branch_behind_base proceeded behind=$behind comparison_ref=$comparison_ref")
  ```
- **(c) Abort.** Exit 0 with `Aborted.`.

### 0.7. Enumerate `claude_md_paths`

Run:

```bash
printf '%s\n' $reviewed_files_all | \
  claude-md-paths.sh \
    --repo-root "$repo_root" --files @-
```

(`@-` reads from stdin so large `reviewed_files_all` doesn't blow past
`ARG_MAX`.) Capture the output as `claude_md_paths` — one absolute path per
line, already deduped and root-first-sorted. Empty output is fine (plenty of
repos have no CLAUDE.md).

### 0.8. Dirty-tree gate

Run `git status --porcelain`. If output is non-empty, briefly list what's
uncommitted (filenames only, categorized as Modified / Staged / Untracked —
do NOT dump the diff). Then use `AskUserQuestion` once with three options:

- **Stash my changes, run review, restore** (recommended). Run
  `git stash push -u -m "pre-jds-review-stash"` now; at end of Phase 6,
  run `git stash pop`. Capture `stash_taken=true` so Phase 6 knows to pop.
- **Include uncommitted changes in the review** — the review will include
  whatever's in the tree as-is; no stash. Warn explicitly: "Uncommitted
  files will appear in the diff the lenses see, so the review covers
  more than what's committed on this branch."
- **Stop so I can handle them first** — exit.

If the tree is clean, no prompt. Record `stash_taken=false`.

**Capture `pre_validator_clean`** as the final action of this step.
This is the baseline Phase 4's tree-cleanliness sweep gates on — the
`git status --porcelain` check is done AFTER the user's choice has
applied (post-stash, or post-confirm-to-include). Mirrors the
pattern in `commands/add.md` step 7.0 (see `commands/add.md:574-578`).

```bash
pre_validator_clean=true
if [[ -n "$(git -C "$repo_root" status --porcelain 2>/dev/null)" ]]; then
    pre_validator_clean=false
fi
```

When the user picked **Stash** or the tree was clean to begin with,
`pre_validator_clean=true` — Phase 4's sweep can safely revert any
dirt as validator-sourced. When the user picked **Include
uncommitted changes in the review**, `pre_validator_clean=false` —
Phase 4 must skip the sweep, since a blind revert would clobber the
very changes the user asked to include.

### 0.9. (Removed — no pushes)

The upstream pipeline pushed unpushed commits here in PR mode. This
command never pushes; nothing to do. Step numbering is preserved so
cross-references from other fragments stay valid.

### 0.10. Capture `reviewed_sha`

Now (after any push), run `git rev-parse HEAD` and capture as `reviewed_sha`.
This is the staleness-envelope anchor.

### 0.11. Trivial-diff check (§13.9)

If `force_full=true`, set `trivial_mode=false` and `trivial_reason=null`
and skip the rest of this step. Otherwise delegate to `trivial-check.sh`
(allow-list walk + count thresholds + reason emission):

```bash
tc_json=$(printf '%s\n' $reviewed_files_all | trivial-check.sh --num-files "$num_files" --lines-changed "$lines_changed")
trivial_mode=$(printf '%s' "$tc_json" | jq -r '.trivial_mode')
trivial_reason=$(printf '%s' "$tc_json" | jq -r '.reason')
```

### 0.12. User-facing-change classifier (Sonnet — skipped in trivial mode)

If `trivial_mode == true`, set `user_facing=false` and skip this step
(L5 is already off in trivial mode; Phase 1's L5 gating will also
re-check `trivial_mode`).

Otherwise, launch a Sonnet sub-agent with this input:

```
Diff files (with short descriptions of each file's apparent type):
<list each file in reviewed_files_all with a one-line "what is this file"
hint based on its extension / path — e.g. "src/components/Foo.tsx — React
component", "config/database.yml — backend config">

Return JSON: {"user_facing": true|false, "surfaces": ["..."]}

Return user_facing: true if the diff touches any of: UI components,
route or page files, templates, user-visible strings/copy, CSS/styles,
i18n files. Return false for pure backend logic, build tooling,
internal utilities, config.
```

Dispatch with the `Agent` tool, `model: sonnet`. After the sub-agent returns,
parse `user_facing` + `surfaces`. Then log tokens (every required arg is
explicit here to match the helper's argparse — don't infer):

```bash
log-tokens.sh \
  --review-dir "$review_dir" \
  --phase phase_0 \
  --agent-role user_facing_classifier \
  --agent-id "$classifier_agent_id" \
  --model sonnet \
  --tokens "$classifier_tokens_or_null"
```

Where `$classifier_agent_id` is the id in the Agent tool result and
`$classifier_tokens_or_null` is either the parsed token count or the literal
word `null` on parse failure.

If JSON parsing of the classifier result fails after one retry, default
`user_facing=true` (fail-safe — better to run L5 unnecessarily than skip
a real UX finding).

### 0.13. Prior-artifact detection

Resolve the reviews root: `$JDS_REVIEW_REVIEWS_ROOT` if set, else
`~/.jds-reviews`. Build the path:
`<reviews_root>/<repo_slug>/<head_branch>/latest.txt`.

If the file exists and is non-empty, read its contents as
`prior_review_id`. Read `<reviews_root>/<repo_slug>/<head_branch>/<prior_review_id>/artifact.json`
and determine the prior state:

| Condition | AskUserQuestion prompt |
|---|---|
| `prior.reviewed_sha == reviewed_sha` AND no `fix_attempts` on any finding | "You have a review for this exact commit from `<date>`. Re-run fresh, or abort?" |
| `prior.reviewed_sha == reviewed_sha` AND some finding has a `fix_attempts[-1]` whose `output_sha` matches `HEAD` | "You have a review that was already fixed at this commit. Re-run fresh, or abort?" |
| Any finding has `current_state=open` AND `is_actionable=true` | "Previous review has unresolved actionable findings. Options: (a) run `/jds:fix` first, (b) proceed with fresh review, (c) abort." |
| Otherwise (prior exists but HEAD has moved beyond any known sha) | "Prior review at `<prior.reviewed_sha>`. Current HEAD is `<reviewed_sha>`. Proceed with fresh review?" |

A "fresh review" supersedes the prior local artifact (new `review_id`,
new `review_dir`, `latest.txt` re-pointed).

If `latest.txt` is missing: skip this step.

### 0.14. (Removed — no PR comments)

The upstream pipeline detected its own prior PR review comment here to
offer replace-in-place publishing. This command never posts or edits
PR comments; nothing to do. Step numbering is preserved so
cross-references to step 0.15 stay valid.

### 0.15. Create the review directory and initialize the artifact

Generate a `review_id`. Schema requires `^rev_[A-Za-z0-9]+$` (see
`schema-v1.json`) so the prefix is mandatory. Prefer ULID; fall back to
a timestamp+random tail. Both paths MUST produce a `rev_`-prefixed id:

```bash
if ulid=$(uv run --with ulid-py python3 -c 'import ulid; print(ulid.new())' 2>/dev/null); then
    review_id="rev_${ulid}"
else
    # Schema (schema-v1.json) pins review_id to ^rev_[A-Za-z0-9]+$ —
    # the character class excludes underscores, so concatenate without
    # a separator between the timestamp and the random tail.
    review_id="rev_$(date -u +%Y%m%dT%H%M%SZ)$(openssl rand -hex 3)"
fi
```

Capture as `review_id`.

Build the artifact directory:

```bash
reviews_root="${JDS_REVIEW_REVIEWS_ROOT:-$HOME/.jds-reviews}"
review_dir="$reviews_root/$repo_slug/$head_branch/$review_id"
mkdir -p "$review_dir"
artifact_path="$review_dir/artifact.json"
```

Capture `reviews_root`, `review_dir`, `artifact_path`. Also capture the three
log paths:

- `phases_log_path = "$review_dir/phases.jsonl"`
- `tokens_log_path = "$review_dir/tokens.jsonl"`
- `trace_log_path = "$review_dir/trace.md"`

Build the initial seed doc. `remote_sha` / `behind_count` may be null
on the offline / no-remote paths. Build the `base_context` sub-object
inline, then hand the rest of the seed shape to `artifact-seed.sh`:

```bash
base_context_json=$(jq -n \
  --arg freshness "$base_freshness" \
  --arg comparison_ref "$comparison_ref" \
  --arg remote_sha "${remote_sha:-}" \
  --arg behind_count "${behind_count:-}" \
  '{
    freshness: $freshness,
    comparison_ref: $comparison_ref,
    remote_sha: (if $remote_sha == "" then null else $remote_sha end),
    behind_count: (if $behind_count == "" then null else ($behind_count | tonumber) end)
  }')

artifact-seed.sh \
  --review-id "$review_id" --review-started-at "$review_started_at" \
  --reviewed-sha "$reviewed_sha" \
  --base-branch "$base_branch" --head-branch "$head_branch" \
  --mode local --pr-state "" \
  --pr-number "" --comment-id "" \
  --trivial-mode "$trivial_mode" --base-context "$base_context_json" \
  --reviewed-files-all "$reviewed_files_all" \
  --claude-md-paths "$claude_md_paths" \
  --files-changed "$num_files" --lines-changed "$lines_changed" \
  --reviewer-sources internal \
  | artifact-patch.py --init - --path "$artifact_path"
```

**Flush `preflight_warnings` to `trace.md`** (only after `--init`
succeeds — else `trace_log_path` points at a directory that may be
about to be `rm -rf`-ed):

```bash
if [[ ${#preflight_warnings[@]} -gt 0 ]]; then
    for w in "${preflight_warnings[@]}"; do
        printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$w" >> "$trace_log_path"
    done
fi
```

On non-zero exit from `artifact-patch.py --init`: the stderr will be error-
as-prompt. Parse the message, adjust the seed, retry once. If still failing
after retry, escalate to the user with the stderr content AND delete the
empty `review_dir` you created (`rm -rf -- "$review_dir"`). Leaving it
behind makes step 0.13 on the next run think a prior review exists when
none does. Do NOT write `latest.txt` (step 0.16) on this failure path.

### 0.16. Update `latest.txt` (atomic) — only after --init succeeds

Step 0.15's `--init` must have succeeded for this step to run. If the
`--init` call failed in step 0.15, skip this step — `latest.txt` stays
pointing at whatever prior review_id was there (or doesn't exist at
all on first run).

```bash
tmp="$reviews_root/$repo_slug/$head_branch/latest.txt.tmp.$$"
printf '%s\n' "$review_id" > "$tmp"
mv "$tmp" "$reviews_root/$repo_slug/$head_branch/latest.txt"
```

### 0.17. Log Phase 0

```bash
elapsed=$(( $(date +%s) - phase_0_start_epoch ))
log-phase.sh \
  --review-dir "$review_dir" --phase 0 --name preflight \
  --elapsed "$elapsed" \
  --summary "mode=local; high_model=$high_model; trivial_mode=$trivial_mode; user_facing=$user_facing; files=$num_files; lines=$lines_changed; claude_md_paths=$(printf '%s\n' $claude_md_paths | wc -l | tr -d ' ')"

log-phase.sh \
  --review-dir "$review_dir" --phase 0 --record "$(jq -nc \
    --arg name preflight \
    --argjson elapsed_sec "$elapsed" \
    --argjson trivial "$trivial_mode" \
    --argjson user_facing "${user_facing:-false}" \
    --argjson files_changed "$num_files" \
    --argjson lines_changed "$lines_changed" \
    '{name:$name, elapsed_sec:$elapsed_sec, trivial_mode:$trivial, user_facing:$user_facing, counts_by_state:{}, counts_by_disposition:{}, pr_size:{files_changed:$files_changed, lines_changed:$lines_changed}}')"
```

(Capture `phase_0_start_epoch` at step 0.1 entry via
`phase_0_start_epoch=$(date +%s)`.)

### Working set now established

At the end of Phase 0, you should have captured:

| Name | Source |
|---|---|
| `scrape_mode`, `holistic_mode`, `force_full`, `high_model` | Step 0.1 |
| `head_branch`, `base_branch`, `repo_root` | Step 0.2 |
| `comparison_ref`, `base_freshness`, `remote_sha`, `behind_count` | Step 0.2a |
| `preflight_warnings` (flushed at 0.15) | Step 0.2a |
| `repo_slug` | Step 0.3 |
| `scrape_pr_number` (scrape_mode only, may be unset) | Step 0.4 |
| `review_started_at` | Step 0.5 |
| `reviewed_files_all`, `num_files`, `lines_changed` | Step 0.6 |
| `claude_md_paths` | Step 0.7 |
| `stash_taken` | Step 0.8 |
| `reviewed_sha` | Step 0.10 |
| `trivial_mode` | Step 0.11 |
| `user_facing` | Step 0.12 |
| `review_id`, `review_dir`, `artifact_path`, `reviews_root` | Step 0.15 |
| `phases_log_path`, `tokens_log_path`, `trace_log_path` | Step 0.15 |

Every later phase references these by name. Don't recompute; don't rediscover.

**Reminder on `comparison_ref` vs `base_branch`.** `base_branch` is the
human name ("main") recorded in the artifact for display. `comparison_ref`
is the ref every later `git diff` / `git blame` / lens-prompt uses. They
match on the happy path (`fresh`, `fast_forwarded`) and diverge only
under option (b) (`used_remote_ref`), when `comparison_ref = "origin/main"`
while `base_branch` stays `"main"`. Phases 1–6 always read
`comparison_ref`; the renderer's header is the one place that still
shows `base_branch` (plus the freshness line when non-default).
