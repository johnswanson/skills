# Review lenses

Extra reviewers that run alongside `/code-review` in step 3 of `stage` and
`stage-feature`. Lenses come from two files, both optional, and all lenses
found in either run:

- **Global:** this file. Lenses here apply to every repository.
- **Per-repo:** `.claude/review-lenses.md` at the root of the source
  checkout the skill was invoked from. Read it from there, not from the
  worktree; it is usually untracked and so absent from a fresh checkout.

Both files use the same format. Each `##` heading is one lens; its body is
the brief handed to that reviewer verbatim, after filling these placeholders:

- `{worktree}` — absolute path to the worktree under review
- `{base}` — the ref the branch left, for `git diff {base}...HEAD`
- `{issue}` — issue ref and body, acceptance criteria as a numbered list

Every lens is report-only. It hunts one kind of problem, fixes nothing, and
leaves the tree as it found it; fixes flow through step 4 to the worker. Its
findings are presented under the lens's own heading, never merged into the
Standards or Spec axes. If a per-repo lens shares a heading with a global
one, the per-repo lens wins.

No global lenses are defined yet. To add one here or in a repo file, append
a section like:

    ## verbose-comments
    Review the diff `git -C {worktree} diff {base}...HEAD` for comments that
    restate the code beside them ...
