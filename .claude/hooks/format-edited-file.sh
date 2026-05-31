#!/usr/bin/env bash
# PostToolUse hook: best-effort auto-format the file Claude just edited, so the
# agent's output stays gate-green. Always exits 0 — never blocks an edit. The
# authoritative checks are `make check` (backend) and the npm gate (frontend).
file="$(python3 -c 'import sys, json
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")' 2>/dev/null || true)"

[ -n "$file" ] && [ -f "$file" ] || exit 0
root="$(git -C "$(dirname "$file")" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$root" ] || exit 0

case "$file" in
  *"/back/"*.py)
    (cd "$root/back" && uv run ruff format "$file" && uv run ruff check --fix "$file") >/dev/null 2>&1 || true
    ;;
  *"/front/"*.ts | *"/front/"*.svelte | *"/front/"*.js | *"/front/"*.cjs | *"/front/"*.mjs | *"/front/"*.css | *"/front/"*.scss | *"/front/"*.json)
    (cd "$root/front" && npx --no-install prettier --write "$file") >/dev/null 2>&1 || true
    ;;
esac
exit 0
