#!/usr/bin/env bash
# Check AI_TOOLS_VERIFY_GATE_V1 injection markers in a target project root.
# Keep the required= lists in sync with docs/ai-tools-integration.md section 5.1.
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

command -v rg >/dev/null || {
  echo 'ERROR: ripgrep (rg) is required'
  exit 1
}

for file in \
  .cursor/commands/opsx-{apply,verify,sync,archive}.md \
  .cursor/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  if [ ! -f "$file" ]; then
    echo "NOFILE    $file"
    continue
  fi
  count="$( { rg -o --fixed-strings 'AI_TOOLS_VERIFY_GATE_V1' "$file" || true; } | wc -l | tr -d ' ')"
  case "$count" in
    0) echo "MISSING   $file" ;;
    1)
      required=""
      case "$file" in
        *opsx-apply.md|*openspec-apply-change/SKILL.md)
          required="AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1"
          ;;
        *opsx-verify.md|*openspec-verify-change/SKILL.md)
          required="AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1"
          ;;
      esac
      stale_missing=""
      for marker in $required; do
        if ! rg -q --fixed-strings "$marker" "$file"; then
          stale_missing="$marker"
          break
        fi
      done
      if [ -n "$stale_missing" ]; then
        echo "STALE     $file (missing $stale_missing)"
      else
        echo "OK        $file"
      fi
      ;;
    *) echo "DUPLICATE $file ($count markers)" ;;
  esac
done
