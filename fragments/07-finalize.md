## Phase 6 — Finalize

### 6.1. Schema-validate the artifact

```bash
artifact-validate.sh --path "$artifact_path"
```

On non-zero exit: log the validator stderr verbatim to `trace.md`;
surface to the user as "Final artifact fails schema validation — see
trace.md." Dump a copy to `/tmp/jds-review-invalid-$(date -u +%Y%m%dT%H%M%SZ).json`
for debugging. Do NOT proceed to render — a broken artifact
should not masquerade as a finished review.

### 6.2. Tally `subagent_tokens` from `tokens.jsonl`

```bash
tally-subagent-tokens.sh \
  --tokens-log "$tokens_log_path" \
  --artifact   "$artifact_path"
```

`tokens: null` entries coerce to 0; an empty log produces a zero
rollup rather than an error.

### 6.2b. Tally `orchestrator_tokens` from the session transcript(s)

```bash
review_started_at=$(jq -r '.review_started_at // empty' "$artifact_path")

orchestrator-tokens.sh \
  --artifact "$artifact_path" \
  --since    "$review_started_at"
```

Companion to the sub-agent tally; the two are non-overlapping. Don't
override `--cwd` — passing `$repo_root` mis-points in worktrees where
the session was started from the worktree path. Safe to call when
the transcript directory is absent (zero rollup, no error).

The helper is **opt-in** via `JDS_REVIEW_TALLY_ORCHESTRATOR=1`
(default skip). When opted out it exits 0 with one
`orchestrator-tally: skipped (...)` stdout line and does not touch
the artifact, so the rendered report simply omits the
**Orchestrator tokens** line.

### 6.3a. Recompute `reviewer_sources` from actual findings

Top-level `reviewer_sources` is the union of providers that produced
at least one candidate. Compute it from `findings[].sources[]`:

- `internal` — present when any lens produced a candidate (any
  `sources[]` entry matches `L[0-9]+-.*` — L1–L7 today, forward-compat for future lenses).
- `external-pr:<bot-login>` — present when any entry starts with
  `external-pr:`.

```bash
reviewer_sources=$(jq -c '
  [.findings[] | .sources[]]
  | map(
      # Internal lens tags: L1..L7 today (L7 is the --holistic-gated
      # lens). Regex is [0-9]+ for forward-compatibility — new L-N
      # lenses slot in without this needing an update. Any entry that
      # doesn't match falls through to `empty` and gets dropped from
      # the union.
      if test("^L[0-9]+-") then "internal"
      elif startswith("external-pr:") then .
      else empty end
    )
  | unique
' "$artifact_path")

printf '%s\n' "$reviewer_sources" > "/tmp/jds-review-rs-$review_id.json"
artifact-patch.py \
  --path "$artifact_path" \
  --set-json "reviewer_sources=@/tmp/jds-review-rs-$review_id.json"
rm -f "/tmp/jds-review-rs-$review_id.json"
```

If `findings[]` is empty (no candidates detected), the union is `[]` —
the schema accepts an empty array.

### 6.3. Populate `metrics`

```bash
start_epoch=$(date -d "$review_started_at" +%s 2>/dev/null || python3 -c "
import sys
from datetime import datetime
print(int(datetime.fromisoformat('$review_started_at'.replace('Z','+00:00')).timestamp()))
")
now_epoch=$(date +%s)
elapsed=$((now_epoch - start_epoch))

# At review time (Stage 2), phase_9_verified_pct and required_followup
# are null — they're set by /jds:fix's Phase 9.
metrics=$(jq -n \
  --argjson elapsed "$elapsed" \
  --argjson files_changed "$num_files" \
  --argjson lines_changed "$lines_changed" \
  '{
    phase_9_verified_pct: null,
    required_followup: null,
    time_elapsed_seconds: $elapsed,
    pr_size_buckets: {files_changed: $files_changed, lines_changed: $lines_changed}
  }')

echo "$metrics" > "/tmp/jds-review-metrics-$review_id.json"
artifact-patch.py \
  --path "$artifact_path" \
  --set-json "metrics=@/tmp/jds-review-metrics-$review_id.json"
rm -f "/tmp/jds-review-metrics-$review_id.json"
```

### 6.4. Append Phase 6 record to `phases.jsonl`

```bash
by_disp=$(artifact-read.sh \
  --path "$artifact_path" --summary | jq -c '.counts_by_disposition')
by_state=$(artifact-read.sh \
  --path "$artifact_path" --summary | jq -c '.counts_by_state')

log-phase.sh \
  --review-dir "$review_dir" --phase 6 --name finalize \
  --elapsed 0 \
  --summary "rendering; total findings=$(jq '.findings | length' $artifact_path)"

log-phase.sh \
  --review-dir "$review_dir" --phase 6 --record "$(jq -nc \
    --argjson by_disp "$by_disp" \
    --argjson by_state "$by_state" \
    '{name:"finalize", elapsed_sec:0, counts_by_state:$by_state, counts_by_disposition:$by_disp}')"
```

### 6.5. Render `artifact.md`

```bash
artifact-render.py \
  --input "$artifact_path" --output "$review_dir/artifact.md"
```

On non-zero exit: log stderr to `trace.md` and stop — rendering is a
prerequisite for mirror-to-chat.

### 6.6. Re-assert `latest.txt` (atomic)

```bash
tmp="$reviews_root/$repo_slug/$head_branch/latest.txt.tmp.$$"
printf '%s\n' "$review_id" > "$tmp"
mv "$tmp" "$reviews_root/$repo_slug/$head_branch/latest.txt"
```

### 6.7. Publish (local trace entry only)

This command never publishes anywhere — the artifact and rendered
report on disk ARE the deliverable. Call the publisher in local mode
for the audit trail:

```bash
artifact-publish.sh \
  --mode local --review-id "$review_id" --review-dir "$review_dir"
```

No-op that appends a one-line trace entry. Exit should be 0.

### 6.8. Mirror the rendered report to chat

Read `$review_dir/artifact.md` and output the full content directly to
the Claude Code chat — NOT a summary, the full sectioned report. This
is the review's primary user-facing output.

Prepend a one-line header:

`### Code review (local — \`$head_branch\` vs \`$base_branch\`)`

After the main report body (the contents of `artifact.md`), add a
**Next steps** block. Do NOT use `AskUserQuestion` here.

Render this block verbatim:

```markdown
---

**Next steps**

- **Artifacts** — the machine-readable review lives at
  `$review_dir/artifact.json`; the rendered report at
  `$review_dir/artifact.md`. Both persist across sessions;
  `latest.txt` in the parent directory points at this review.

- **Apply the auto-eligible findings** — `/jds:fix 60` applies every
  finding in the deep-lane "✓ Auto-fixable" table that scores at or
  above the threshold, committing locally (never pushing). Light-lane
  rows are skipped by default; promote them first with the
  walkthrough.

- **Walk through the skipped findings** — `/jds:walkthrough` presents
  each deep-lane manual finding and every light-lane row one at a
  time with a briefing (what it's about, options, a recommendation)
  and promotes the ones you approve with tailored fix-hints. Writes a
  decisions log into the review directory for audit. Works
  same-session, later, or in a new session — the artifact persists.

You can run either step independently, or both in either order.
```

(These trailing lines are chat-only, not part of `artifact.md` itself.)

### 6.9. Pop stash (if Phase 0 took one)

If `stash_taken == true` from Phase 0 step 0.8:

```bash
git stash pop
```

If the pop conflicts, do NOT auto-resolve. Tell the user clearly: "Your
stashed changes conflict with something in the tree. Resolve manually;
your stash is preserved under `git stash list`." Leave the stash in
place (it doesn't auto-drop on conflict).

If `stash_taken == false`, skip this step.

### 6.10. Final status + surface any deferred failures

If any of render / validation failed, surface them as the primary
user-visible failure now, after the chat mirror. Each failure should
name the step and the next action the user should take.

If everything succeeded: nothing more to say — the chat mirror + the
on-disk artifact is the deliverable.
