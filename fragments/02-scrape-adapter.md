## Phase 1.5 — PR-comment scrape adapter (conditional on `--scrape-pr-comments`)

**Skip this entire phase** unless `scrape_mode == true` (captured in
Phase 0 step 0.1, possibly disabled at step 0.4 if no open PR was
found). Log one line to `trace.md` and proceed to Phase 2:

```
Phase 1.5 skipped — --scrape-pr-comments not set (or no PR found)
```

**Execution point.** This fragment runs inside Phase 1's join step —
01-detection.md step 1.5 invokes it after every internal lens has
returned, and resumes once `external_candidates` is set. Everything
here is **read-only against GitHub**: the scrape fetches bot-authored
comments; nothing is ever posted, edited, or pushed.

Scraped comments feed a single Sonnet normalizer sub-agent that emits
standard candidates. The normalizer's output pools into the
orchestrator-context `external_candidates` variable; the join step at
01-detection.md 1.5 assigns ids and commits to `artifact.findings[]`
with `source_family: "external-deep-family"` and
`origin_confidence: "low"`.

**Token accounting.** Only the Sonnet normalizer is logged, under
`phase_1_5`.

### 1.5.1. Readiness

By this point, `scratch_dir`, `phase_1_5_start_epoch` (set by
`01-detection.md` steps 1.2a/1.2b), and `scrape_pr_number` (Phase 0
step 0.4) are in working context.

### 1.5.4. PR comment scrape

The scrape (`external-scrape.sh` §21.8) fetches every bot-authored
comment on the PR; the freshness filter (`comment-freshness.sh` §21.10)
drops records whose referenced code has changed between when the
comment was posted and HEAD. Guard the exit-code captures with `||`
so `set -e` orchestrator context doesn't abort on non-zero — we
deliberately want to read the code and continue:

```bash
external-scrape.sh \
    --pr "$scrape_pr_number" \
    > "$scratch_dir/pr-scrape.raw.json" \
    2> "$scratch_dir/pr-scrape.err" \
    || scrape_exit=$?
scrape_exit=${scrape_exit:-0}

if [[ $scrape_exit -eq 0 ]]; then
    reviewed_files_csv=$(printf '%s\n' "$reviewed_files_all" \
        | awk 'NF' | paste -sd, -)

    # Pipe through comment-freshness.sh. Audit lines (`comment_freshness: …`)
    # flow into trace.md via `tee -a` — mirrors origin-crosscheck.sh
    # dispatch at 01-detection.md step 1.4 step 2a.
    if ! comment-freshness.sh \
            --pr "$scrape_pr_number" \
            --reviewed-files "$reviewed_files_csv" \
            --comments "$scratch_dir/pr-scrape.raw.json" \
            > "$scratch_dir/pr-scrape.json" \
            2> >(tee -a "$trace_log_path" >&2); then
        # Freshness helper itself failed (rare — its own errors log to
        # stderr with a `comment_freshness_api_failed` prefix). Degrade
        # gracefully: use the raw scrape. Log the tag so a reader can
        # explain why stale-but-pre-existing comments made it through.
        printf 'phase_1_5_freshness_helper_failed: using raw scrape\n' \
            >> "$trace_log_path"
        cp "$scratch_dir/pr-scrape.raw.json" "$scratch_dir/pr-scrape.json"
    fi
else
    # Scrape failed — write an empty array so downstream consumers
    # don't trip on a missing file. The scrape-failed tag is logged
    # below.
    echo "[]" > "$scratch_dir/pr-scrape.json"
fi
```

On scrape non-zero exit (rate limit, auth, network): log stderr to
`trace.md` with tag `phase_1_5_scrape_failed`; continue — the review
proceeds on internal lenses alone. Do not abort. The freshness-filter
failure path (inner `if`) is separately logged because it can fire
independently of the scrape succeeding.

### 1.5.4b. No-input early-skip

If the scrape produced zero bot comments, skip §1.5.5 (normalizer
dispatch) and §1.5.6 (token log: no sub-agent ran). Proceed directly
to §1.5.6b (scratch cleanup) and §1.5.7 (summary).

```bash
scrape_bot_count=0
if [[ -s "$scratch_dir/pr-scrape.json" ]] \
   && jq -e 'type == "array"' "$scratch_dir/pr-scrape.json" >/dev/null 2>&1; then
    scrape_bot_count=$(jq 'length' "$scratch_dir/pr-scrape.json")
fi
if [[ "$scrape_bot_count" -eq 0 ]]; then
    external_candidates="[]"
    external_candidate_count=0
    printf 'phase_1_5_no_external_inputs: skipping normalizer dispatch\n' \
        >> "$trace_log_path"
    # Fall through to §1.5.6b. The dispatch in §1.5.5 is gated on this.
fi
```

If at least one bot comment came back, dispatch the normalizer in
§1.5.5 below.

### 1.5.5. Normalize the scraped comments (single Sonnet sub-agent)

Skip this section entirely if §1.5.4b set `external_candidates="[]"`
on the no-input early-skip path.

The sub-agent produces one unified candidate list. This follows §19.2a
verbatim.

Dispatch via `Agent` with `model: sonnet`. Prompt essence:

> You are normalizing external-reviewer output into the jds-review
> candidate schema. You receive one input:
>
> **PR bot comments** (JSON array):
>
> ```
> <contents of $scratch_dir/pr-scrape.json>
> ```
>
> Each entry has `{id, author_login, author_type, created_at, body, kind,
> path?, line?, commit_id?}`.
>
> Extract concrete issues from each. If a single comment covers
> multiple distinct issues, emit one candidate per issue. Infer `file` and
> `line_range` from explicit `path`/`line` fields when present, else from
> the body text (e.g. "In `src/foo.ts:45`..."). If neither is available,
> emit the candidate with `file: null` — Phase 2 dedup may still match it
> against internal findings.
>
> Classify `impact_type` conservatively: prefer `correctness` when unclear;
> never reach for `security` without concrete evidence.
>
> Discard comments that are questions, praise, or general commentary — only
> normalize content that identifies an issue in the diff.
>
> Return a JSON array. Each candidate:
>
> ```
> {
>   "file": "src/path/to/file.ts" | null,
>   "line_range": [start, end] | null,
>   "claim": "one-sentence description",
>   "evidence_snippet": "the implicated code or the original comment body",
>   "impact_type": "correctness" | "security" | "ux" | "policy" | "architecture",
>   "origin": "introduced_by_pr" | "pre_existing" | "unknown",
>   "origin_confidence": "low",
>   "source_family": "external-deep-family",
>   "sources": ["external-pr:<author_login>"]
> }
> ```
>
> `origin_confidence` is ALWAYS `"low"` for external candidates —
> internal corroboration in Phase 4 decides whether they surface.

**After the normalizer returns**, repair missing location info and
emit the result to `external_candidates` for the join step at
01-detection.md step 1.5. Do NOT call `--add-finding` / `--add-findings` here.

**Parse-with-repair front-stop.** Pipe the raw normalizer output
through `parse-with-repair.py` before handing it to `jq`:

```bash
normalizer_clean=$(printf '%s' "$normalizer_output" \
    | parse-with-repair.py \
        2> >(tee -a "$trace_log_path" >&2))

if [[ -z "$normalizer_clean" ]]; then
    # parse-with-repair exited non-zero (already logged via tee above).
    # Drop the external pool to an empty array.
    printf 'phase_1_5_normalizer_unparseable: dropping external candidates\n' \
        >> "$trace_log_path"
    external_candidates="[]"
    external_candidate_count=0
fi
```

**Schema guard for missing location info.** Schema requires `file`
non-null and `line_range` as `[int,int]` with items `>=1`. Repair the
normalizer's `null` fields before pooling by defaulting to a sentinel:

```bash
if [[ -n "$normalizer_clean" ]]; then
    external_candidates=$(printf '%s' "$normalizer_clean" | jq -c '
      [ .[] | . + {
          file:       (.file // "(unknown)"),
          line_range: (.line_range // [1,1])
        } ]
    ')
    external_candidate_count=$(jq 'length' <<<"$external_candidates")
fi
```

Leave a one-line `trace.md` note per repaired candidate so the user
knows where the ambiguity came from (iterate with `jq -r` to produce
the notes before the merge).

### 1.5.6. Log normalizer tokens

Log the normalizer's tokens under `phase_1_5`:

```bash
log-tokens.sh \
  --review-dir "$review_dir" --phase phase_1_5 \
  --agent-role external_normalizer --agent-id <id> \
  --model sonnet --tokens <N or null>
```

### 1.5.6b. Clean up scratch_dir

```bash
rm -rf -- "$scratch_dir"
```

Any orchestrator-fatal failure before this point leaves the scratch
dir for post-mortem inspection.

### 1.5.7. Log Phase 1.5 summary

```bash
phase_1_5_elapsed=$(( $(date +%s) - phase_1_5_start_epoch ))

log-phase.sh \
  --review-dir "$review_dir" --phase 1_5 --name scrape-adapter \
  --elapsed "$phase_1_5_elapsed" \
  --summary "scrape_bots=$scrape_bot_count; normalized=$external_candidate_count"

log-phase.sh \
  --review-dir "$review_dir" --phase 1_5 --record "$(jq -nc \
    --arg name scrape-adapter \
    --argjson elapsed "$phase_1_5_elapsed" \
    --argjson added "$external_candidate_count" \
    '{name:$name, elapsed_sec:$elapsed, counts_by_state:{open:$added}, counts_by_disposition:{pending_validation:$added}, delta:"+\($added) external"}')"
```
