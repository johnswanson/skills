#!/usr/bin/env bash
# split-status.sh <original-ref>
#
# Shows the work on the current branch (HEAD) that has NOT yet been carved out,
# i.e. how the current chunk tip still differs from the original PR tip.
# Empty output means the stack is complete (HEAD == original).
set -euo pipefail

ORIG="${1:?usage: split-status.sh <original-ref>}"

echo "== Unassigned work: HEAD vs ${ORIG} =="
git diff --stat "${ORIG}" HEAD || true
echo

read -r added deleted <<<"$(git diff --numstat "${ORIG}" HEAD \
  | awk '{a+=$1; d+=$2} END {print (a+0), (d+0)}')"

if [[ "${added}" -eq 0 && "${deleted}" -eq 0 ]]; then
  echo "✅ Nothing left — HEAD matches ${ORIG}. Stack is complete."
else
  echo "Remaining vs ${ORIG}: +${added} / -${deleted} (still to assign to chunks)"
fi
