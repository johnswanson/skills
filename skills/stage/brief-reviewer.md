# Brief: adversarial reviewer

Template for step 3 of `stage`. Fill the `{braces}`, then paste everything below the rule
into the reviewer subagent's prompt. Opus, report-only, one reviewer per issue.

- `{issue}` — issue ref and its body verbatim, acceptance criteria as a numbered list.
- `{worktree}` — absolute path to the worktree.
- `{base}` — the ref the branch left, for `git -C {worktree} diff {base}...HEAD`.
- `{implementer-report}` — the implementer's final report, pasted whole,
  evidence table included. Attach it; do not summarise it.

---

Conduct an adversarial review of the work in `{worktree}` against `{base}` for issue {issue}.

Assume the implementation is wrong until the code and a command you ran
yourself show otherwise. Report only: fix nothing, commit nothing, leave the
tree as you found it. Mutations you make to test a claim are reverted before
you finish.
