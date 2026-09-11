---
name: bump-version
description: "Stage all changes, bump the plugin version, commit, and push."
---

Bump the project's version and ship it.

1. **Stage.** `git add -A` (review `git status` first for anything that
   shouldn't go in, e.g. secrets).

2. **Bump.** Default to a patch bump unless the user says otherwise (minor,
   major, or an explicit version). Update the `version` field in both:
   - `.claude-plugin/plugin.json`
   - `.claude-plugin/marketplace.json` (under `plugins[0].version`)

   Both files must end up with the same version. Stage the edits.

3. **Commit.** `git commit -m "Bump version to <version>"` (plus whatever else
   was staged in step 1 — summarize it in the message if it's non-trivial).

4. **Push.** `git push`.
