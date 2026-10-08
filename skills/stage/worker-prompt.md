Implement the work described by `<issue id>`

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, review the code in two ways:
- use /code-review, with the additional instruction to launch each sub-agent as a herdr agent in its own pane, using
  the **reviewer pane** recipe in `<stage dir>/herdr-recipes.md` (not a native subagent).
- read `<stage dir>/review-lenses.md`, and the repo's own (if it exists) at `<repo>/.claude/review-lenses.md`.
  Launch a reviewer for each lens, again, as a herdr agent in its own pane.

Use your best judgment about which findings to fix. Run the full test suite after any substantive fixes.

Commit your work to the current branch.
