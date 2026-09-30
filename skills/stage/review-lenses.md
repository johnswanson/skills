# Review lenses

Extra reviewers that run alongside `/code-review` in step 3 of `stage` and
`stage-feature`. Each `##` heading below is one lens; its body is the brief
handed to that reviewer verbatim, after filling these placeholders:

- `{worktree}` — absolute path to the worktree under review
- `{base}` — the ref the branch left, for `git diff {base}...HEAD`
- `{issue}` — issue ref and body, acceptance criteria as a numbered list

Every lens is report-only. It hunts one kind of problem, fixes nothing, and
leaves the tree as it found it; fixes flow through step 4 to the worker. Its
findings are presented under the lens's own heading, never merged into the
Standards or Spec axes.

## verbose-comments
Review the diff `git -C {worktree} diff {base}...HEAD` for comments that:
- provide too much implementation detail that callers do not need to know
- are about "today's work" rather than why the code works the way it does (for
  example, "XYZ is out of scope here" can be a red flag)
- are about how things USED to work, rather than how they work now
