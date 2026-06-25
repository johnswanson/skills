#!/usr/bin/env bash
# verify-identical.sh <original-ref> [chunk-tip]
#
# Proves invariant #1: the stack tip is byte-identical to the original PR tree.
# Exits 0 and prints ✅ when identical; exits 1 and prints the diff stat otherwise.
set -euo pipefail

ORIG="${1:?usage: verify-identical.sh <original-ref> [chunk-tip]}"
TIP="${2:-HEAD}"

if git diff --quiet "${ORIG}" "${TIP}"; then
  echo "✅ IDENTICAL: ${TIP} tree matches ${ORIG}. Final diff preserved."
  exit 0
else
  echo "❌ NOT IDENTICAL: ${TIP} differs from ${ORIG} — do NOT ship the stack."
  echo
  git diff --stat "${ORIG}" "${TIP}"
  exit 1
fi
