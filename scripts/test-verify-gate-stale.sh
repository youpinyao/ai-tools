#!/usr/bin/env bash
# Fixture tests for scripts/check-verify-gate-markers.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECK="$ROOT/scripts/check-verify-gate-markers.sh"
DOC="$ROOT/docs/ai-tools-integration.md"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

command -v rg >/dev/null || fail "ripgrep (rg) is required"

rg -q --fixed-strings 'required="AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1"' "$DOC" \
  || fail "docs/ai-tools-integration.md apply required= drifted"
rg -q --fixed-strings 'required="AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1"' "$DOC" \
  || fail "docs/ai-tools-integration.md verify required= drifted"
rg -q --fixed-strings 'required="AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1"' "$CHECK" \
  || fail "scripts/check-verify-gate-markers.sh apply required= drifted"
rg -q --fixed-strings 'required="AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1"' "$CHECK" \
  || fail "scripts/check-verify-gate-markers.sh verify required= drifted"

if rg -n '或能读到对应 `SKILL.md`' "$DOC" >/dev/null; then
  fail "docs still treat readable SKILL.md as skill availability"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p \
  "$tmp/.cursor/commands" \
  "$tmp/.cursor/skills/openspec-apply-change" \
  "$tmp/.cursor/skills/openspec-verify-change" \
  "$tmp/.cursor/skills/openspec-sync-specs" \
  "$tmp/.cursor/skills/openspec-archive-change"

write_gate() {
  local path="$1"
  shift
  {
    echo '<!-- AI_TOOLS_VERIFY_GATE_V1 -->'
    for marker in "$@"; do
      echo "$marker"
    done
  } > "$path"
}

# Current apply/verify injection markers → OK
write_gate "$tmp/.cursor/commands/opsx-apply.md" \
  AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1
write_gate "$tmp/.cursor/skills/openspec-apply-change/SKILL.md" \
  AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1
write_gate "$tmp/.cursor/commands/opsx-verify.md" \
  AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1
write_gate "$tmp/.cursor/skills/openspec-verify-change/SKILL.md" \
  AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1
# sync/archive only need the gate marker
write_gate "$tmp/.cursor/commands/opsx-sync.md"
write_gate "$tmp/.cursor/skills/openspec-sync-specs/SKILL.md"
write_gate "$tmp/.cursor/commands/opsx-archive.md"
write_gate "$tmp/.cursor/skills/openspec-archive-change/SKILL.md"

out="$("$CHECK" "$tmp")"
echo "$out" | rg -q '^OK        \.cursor/commands/opsx-apply.md$' || fail "current apply should be OK: $out"
echo "$out" | rg -q '^OK        \.cursor/commands/opsx-sync.md$' || fail "sync without parallel marker should be OK: $out"
non_ok="$(echo "$out" | rg -v '^OK ' || true)"
[ -z "$non_ok" ] || fail "current fixtures should all be OK: $out"

# Missing worker marker → STALE (old parallel injection)
write_gate "$tmp/.cursor/commands/opsx-apply.md" \
  AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q 'STALE     \.cursor/commands/opsx-apply.md \(missing AI_TOOLS_WORKER_APPLY_V1\)' \
  || fail "apply without worker marker should be STALE: $out"

# Missing parallel marker → STALE
write_gate "$tmp/.cursor/commands/opsx-verify.md" \
  AI_TOOLS_DELEGATED_VERIFY_V1
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q 'STALE     \.cursor/commands/opsx-verify.md \(missing AI_TOOLS_PARALLEL_DISPATCH_V1\)' \
  || fail "verify without parallel marker should be STALE: $out"

# No gate → MISSING
printf 'plain text\n' > "$tmp/.cursor/commands/opsx-archive.md"
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q '^MISSING   \.cursor/commands/opsx-archive.md$' \
  || fail "archive without gate should be MISSING: $out"

# Duplicate gate → DUPLICATE
{
  echo '<!-- AI_TOOLS_VERIFY_GATE_V1 -->'
  echo '<!-- AI_TOOLS_VERIFY_GATE_V1 -->'
} > "$tmp/.cursor/skills/openspec-sync-specs/SKILL.md"
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q '^DUPLICATE \.cursor/skills/openspec-sync-specs/SKILL.md' \
  || fail "duplicate gate should be DUPLICATE: $out"

# Missing file → NOFILE
rm -f "$tmp/.cursor/commands/opsx-sync.md"
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q '^NOFILE    \.cursor/commands/opsx-sync.md$' \
  || fail "removed sync command should be NOFILE: $out"

# Superpowers SKILL.md in cache must not affect STALE
mkdir -p "$tmp/plugin-cache/dispatching-parallel-agents"
echo '# dispatching-parallel-agents' > "$tmp/plugin-cache/dispatching-parallel-agents/SKILL.md"
write_gate "$tmp/.cursor/commands/opsx-apply.md" \
  AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1
out="$("$CHECK" "$tmp")"
echo "$out" | rg -q '^OK        \.cursor/commands/opsx-apply.md$' \
  || fail "plugin-cache SKILL.md must not change marker check: $out"

echo "PASS: verify-gate STALE fixtures"
