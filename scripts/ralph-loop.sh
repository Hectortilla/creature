#!/usr/bin/env bash
#
# ralph-loop.sh — drive an execution plan to completion, one Ralph iteration at a time.
#
# Inspired by Geoffrey Huntley's "Ralph" technique (https://ghuntley.com/ralph/):
#   in its purest form, `while :; do cat PROMPT.md | claude-code; done`.
# Here each turn of the loop spawns a FRESH, clean-context Claude Code run that
# executes the `/ralph-iteration` skill against a checkbox plan under
# `docs/exec-plans/active/`. The skill does ONE step, verifies it, ticks its box,
# commits, and stops — then this loop starts the next clean run. State lives in
# the plan file and git history, exactly as Ralph intends.
#
# The loop stops when the plan is finished (the skill moves the file out of
# `active/`, or no `- [ ]` boxes remain), when it hits the iteration cap, when it
# stalls (no progress for N runs in a row), or when you Ctrl-C.
#
# Usage:  scripts/ralph-loop.sh [PLAN] [options]      (see --help)

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults (override via flags)
# ---------------------------------------------------------------------------
PLAN_ARG=""                 # positional / --plan: plan name or path (auto-detect if empty)
MAX_ITER=20                 # safety cap; 0 = unlimited
MAX_STALLS=3                # consecutive no-progress runs before aborting; 0 = never
SLEEP_SECS=3                # pause between iterations
MODEL=""                    # --model passed to claude (e.g. opus, sonnet)
PERM_MODE=""                # --permission-mode passed to claude (overrides bypass)
BYPASS=true                 # add --dangerously-skip-permissions (needed for unattended)
MAX_BUDGET=""               # --max-budget-usd cap per iteration
PROMPT_OVERRIDE=""          # full custom per-iteration prompt
LOG_DIR=""                  # where to write logs (default: <repo>/.ralph/logs/<runid>)
ASSUME_YES=false            # -y: skip the confirmation prompt
DRY_RUN=false               # print the plan & command, run nothing
CLAUDE_VERBOSE=false        # pass --verbose to claude
USE_COLOR=true
EXTRA_ARGS=()               # everything after `--` is forwarded to claude

# ---------------------------------------------------------------------------
# Colors (empty until setup_colors; defined here so --help works under set -u)
# ---------------------------------------------------------------------------
BOLD=""; DIM=""; RED=""; GRN=""; YEL=""; BLU=""; CYN=""; RST=""

setup_colors() {
  if [[ -t 1 && -z "${NO_COLOR:-}" ]] && $USE_COLOR; then
    BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GRN=$'\033[32m'
    YEL=$'\033[33m'; BLU=$'\033[34m'; CYN=$'\033[36m'; RST=$'\033[0m'
  else
    BOLD=""; DIM=""; RED=""; GRN=""; YEL=""; BLU=""; CYN=""; RST=""
  fi
}

say()  { printf '%b\n' "$*"; }
warn() { printf '%b\n' "${YEL}warning:${RST} $*" >&2; }
err()  { printf '%b\n' "${RED}error:${RST} $*" >&2; }
die()  { err "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
${BOLD}ralph-loop.sh${RST} — run /ralph-iteration in a loop until an exec-plan is done.

${BOLD}USAGE${RST}
  scripts/ralph-loop.sh [PLAN] [options]

  PLAN  Plan to drive: a name (with or without .md) resolved under
        docs/exec-plans/active/, or an explicit path. If omitted, the single
        active plan is auto-detected (errors if there are zero or several).

${BOLD}OPTIONS${RST}
  -p, --plan <file>          Plan name or path (same as the PLAN positional).
  -n, --max-iterations <N>   Stop after N iterations. 0 = unlimited. (default: ${MAX_ITER})
      --max-stalls <N>       Abort after N consecutive no-progress runs. 0 = never. (default: ${MAX_STALLS})
  -s, --sleep <secs>         Pause between iterations. (default: ${SLEEP_SECS})
  -m, --model <model>        Model passed to claude (e.g. opus, sonnet, a full id).
      --max-budget-usd <amt> Cap spend PER ITERATION (claude --max-budget-usd; we always pass -p,
                             which it requires). There is NO cumulative cap — worst-case total
                             spend is roughly this x --max-iterations.
      --permission-mode <m>  claude permission mode (default|acceptEdits|auto|bypassPermissions|plan|dontAsk).
                             Overrides the default --dangerously-skip-permissions.
      --no-bypass            Do NOT pass --dangerously-skip-permissions. Unattended runs
                             will likely stall on permission prompts unless you also pass
                             --permission-mode acceptEdits (or an allowlist via -- ...).
      --prompt <text>        Full custom per-iteration prompt (must reference the plan itself).
                             Default: "/ralph-iteration do the next iteration of @<plan>".
      --log-dir <dir>        Directory for per-iteration logs. (default: <repo>/.ralph/logs/<runid>)
  -v, --verbose              Pass --verbose to claude (more per-turn detail in the logs).
  -y, --yes                  Skip the safety confirmation prompt.
      --dry-run              Show the resolved plan, config, and command; run nothing.
      --no-color             Disable colored output.
  -h, --help                 Show this help.
  --                         Forward all following args verbatim to each claude run
                             (e.g. -- --output-format stream-json --add-dir ../shared).

${BOLD}EXAMPLES${RST}
  # Auto-detect the single active plan and run to completion:
  scripts/ralph-loop.sh

  # Drive the e2e harness plan, capped at 12 runs, no prompt:
  scripts/ralph-loop.sh e2e-verification-harness -n 12 -y

  # Use Opus, cap each run at \$5, watch tool activity:
  scripts/ralph-loop.sh --model opus --max-budget-usd 5 -v

  # See exactly what it would do without spending anything:
  scripts/ralph-loop.sh --dry-run

${BOLD}STOPPING${RST}
  • plan complete  — file moved to docs/exec-plans/completed/ or no "- [ ]" boxes left
  • iteration cap  — --max-iterations reached
  • stalled        — --max-stalls consecutive runs made no commit and ticked no box
  • interrupted    — Ctrl-C (prints a summary and exits)

${BOLD}NOTES${RST}
  • Each iteration is a fresh \`claude -p\` run — that clean context is the point of Ralph.
  • --dangerously-skip-permissions is ON by default because the skill must run builds,
    tests and git unattended. Run this in a trusted repo; you'll be asked to confirm once
    (use -y to skip). The article recommends running Ralph in a sandbox/container.
  • Logs land under a gitignored .ralph/ dir so the skill's commits never sweep them.
  • Ralph burns tokens. --max-budget-usd caps EACH iteration, not the run — your worst-case
    total is roughly (--max-budget-usd x --max-iterations), so set both deliberately.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)            usage; exit 0 ;;
      -p|--plan)            PLAN_ARG="${2:?--plan needs a value}"; shift 2 ;;
      -n|--max-iterations)  MAX_ITER="${2:?--max-iterations needs a value}"; shift 2 ;;
      --max-stalls)         MAX_STALLS="${2:?--max-stalls needs a value}"; shift 2 ;;
      -s|--sleep)           SLEEP_SECS="${2:?--sleep needs a value}"; shift 2 ;;
      -m|--model)           MODEL="${2:?--model needs a value}"; shift 2 ;;
      --max-budget-usd)     MAX_BUDGET="${2:?--max-budget-usd needs a value}"; shift 2 ;;
      --permission-mode)    PERM_MODE="${2:?--permission-mode needs a value}"; shift 2 ;;
      --no-bypass)          BYPASS=false; shift ;;
      --prompt)             PROMPT_OVERRIDE="${2:?--prompt needs a value}"; shift 2 ;;
      --log-dir)            LOG_DIR="${2:?--log-dir needs a value}"; shift 2 ;;
      -v|--verbose)         CLAUDE_VERBOSE=true; shift ;;
      -y|--yes)             ASSUME_YES=true; shift ;;
      --dry-run)            DRY_RUN=true; shift ;;
      --no-color)           USE_COLOR=false; shift ;;
      --)                   shift; EXTRA_ARGS=("$@"); break ;;
      -*)                   die "unknown option: $1 (use -- to forward args to claude, or --help)" ;;
      *)
        [[ -z "$PLAN_ARG" ]] || die "plan specified twice: '$PLAN_ARG' and '$1'"
        PLAN_ARG="$1"; shift ;;
    esac
  done

  [[ "$MAX_ITER"   =~ ^[0-9]+$ ]] || die "--max-iterations must be a non-negative integer (got '$MAX_ITER')"
  [[ "$MAX_STALLS" =~ ^[0-9]+$ ]] || die "--max-stalls must be a non-negative integer (got '$MAX_STALLS')"
  [[ "$SLEEP_SECS" =~ ^[0-9]+$ ]] || die "--sleep must be a non-negative integer (got '$SLEEP_SECS')"
  [[ -z "$MAX_BUDGET" || "$MAX_BUDGET" =~ ^[0-9]+(\.[0-9]+)?$ ]] || die "--max-budget-usd must be a number (got '$MAX_BUDGET')"
}

# ---------------------------------------------------------------------------
# Plan resolution
# ---------------------------------------------------------------------------
resolve_plan() {
  local arg="$1"
  if [[ -n "$arg" ]]; then
    if [[ -f "$arg" ]]; then
      PLAN_ABS="$(cd "$(dirname "$arg")" && pwd)/$(basename "$arg")"; return
    fi
    local name="$arg"; [[ "$name" == *.md ]] || name="${name}.md"
    if [[ -f "$ACTIVE_DIR/$name" ]]; then PLAN_ABS="$ACTIVE_DIR/$name"; return; fi
    if [[ -f "$REPO_ROOT/$arg" ]]; then PLAN_ABS="$REPO_ROOT/$arg"; return; fi
    die "plan not found: '$arg' (looked in $ACTIVE_DIR/ and $REPO_ROOT/)"
  fi

  # Auto-detect: exactly one non-README plan in active/.
  local plans=() p
  shopt -s nullglob
  for p in "$ACTIVE_DIR"/*.md; do
    [[ "$(basename "$p")" == "README.md" ]] && continue
    plans+=("$p")
  done
  shopt -u nullglob

  case ${#plans[@]} in
    0) die "no active plans in $ACTIVE_DIR/ — name one explicitly." ;;
    1) PLAN_ABS="${plans[0]}" ;;
    *) err "multiple active plans — pick one:"
       for p in "${plans[@]}"; do printf '    %s\n' "$(basename "$p")" >&2; done
       exit 1 ;;
  esac
}

# Count remaining unchecked "- [ ]" boxes in the plan (0 if the file is gone).
count_unchecked() {
  if [[ -f "$PLAN_ABS" ]]; then
    grep -cE '^[[:space:]]*- \[ \]' "$PLAN_ABS" 2>/dev/null || true
  else
    echo 0
  fi
}

# Done = plan moved out of active/, or no unchecked boxes remain.
is_complete() {
  [[ ! -f "$PLAN_ABS" ]] && return 0
  [[ "$(count_unchecked)" -eq 0 ]]
}

# Keep loop logs out of the skill's commits.
ensure_gitignored() {
  case "$LOG_DIR/" in
    "$REPO_ROOT"/.ralph/*) ;;            # only manage the default in-repo location
    *) return 0 ;;
  esac
  if ! git -C "$REPO_ROOT" check-ignore -q "$REPO_ROOT/.ralph/probe" 2>/dev/null; then
    printf '\n# Ralph loop logs (scripts/ralph-loop.sh)\n.ralph/\n' >> "$REPO_ROOT/.gitignore"
    say "${DIM}added .ralph/ to .gitignore${RST}"
  fi
}

# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------
bypasses_permissions() {
  if [[ -n "$PERM_MODE" ]]; then
    [[ "$PERM_MODE" == "bypassPermissions" ]]
  else
    $BYPASS
  fi
}

confirm() {
  $ASSUME_YES && return 0
  # Non-interactive (cron/CI, piped stdin, or a tool harness): refuse rather than
  # silently launch an autonomous, permission-bypassing agent. Opt in with -y.
  [[ -t 0 ]] || die "stdin is not a TTY — refusing to start unattended. Pass -y/--yes to run non-interactively."
  local reply
  printf '%b' "${BOLD}Start the loop?${RST} "
  if bypasses_permissions; then
    printf '%b' "${RED}Permissions will be bypassed${RST} — this runs builds, tests and git unattended.\n"
  fi
  printf '%b' "Type ${BOLD}yes${RST} to continue: "
  read -r reply < /dev/tty || true
  [[ "$reply" == "yes" ]] || die "aborted."
}

# ---------------------------------------------------------------------------
# Build the per-iteration claude command
# ---------------------------------------------------------------------------
build_cmd() {
  CLAUDE_CMD=(claude -p "$PROMPT")
  [[ -n "$MODEL" ]]      && CLAUDE_CMD+=(--model "$MODEL")
  if [[ -n "$PERM_MODE" ]]; then
    CLAUDE_CMD+=(--permission-mode "$PERM_MODE")
  elif $BYPASS; then
    CLAUDE_CMD+=(--dangerously-skip-permissions)
  fi
  [[ -n "$MAX_BUDGET" ]] && CLAUDE_CMD+=(--max-budget-usd "$MAX_BUDGET")
  $CLAUDE_VERBOSE        && CLAUDE_CMD+=(--verbose)
  ((${#EXTRA_ARGS[@]}))  && CLAUDE_CMD+=("${EXTRA_ARGS[@]}")
  return 0   # never let the trailing && short-circuit make this function "fail" under set -e
}

# ---------------------------------------------------------------------------
# Summary / signal handling
# ---------------------------------------------------------------------------
ITERATIONS_RUN=0
declare -a COMMITS=()
START_TS=0
STOP_REASON="(none)"

summary() {
  local secs=$(( $(date +%s) - START_TS ))
  say ""
  say "${BOLD}── Ralph loop summary ─────────────────────────────────${RST}"
  say "  plan        ${PLAN_REL}"
  say "  stopped     ${BOLD}${STOP_REASON}${RST}"
  say "  iterations  ${ITERATIONS_RUN}"
  say "  commits     ${#COMMITS[@]}"
  local c
  if ((${#COMMITS[@]})); then
    for c in "${COMMITS[@]}"; do say "                ${DIM}${c}${RST}"; done
  fi
  say "  boxes left  $(count_unchecked)"
  say "  elapsed     ${secs}s"
  say "  logs        ${LOG_DIR}"
  say "${BOLD}───────────────────────────────────────────────────────${RST}"
}

on_interrupt() {
  STOP_REASON="interrupted (Ctrl-C)"
  say ""
  warn "interrupted — finishing up."
  summary
  exit 130
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"
  setup_colors

  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1 || die "not a git repo: $REPO_ROOT"
  cd "$REPO_ROOT"
  ACTIVE_DIR="$REPO_ROOT/docs/exec-plans/active"

  command -v claude >/dev/null 2>&1 || die "'claude' CLI not found on PATH."

  resolve_plan "$PLAN_ARG"
  PLAN_REL="${PLAN_ABS#"$REPO_ROOT"/}"

  if [[ -n "$PROMPT_OVERRIDE" ]]; then
    PROMPT="$PROMPT_OVERRIDE"
  else
    PROMPT="/ralph-iteration do the next iteration of @${PLAN_REL}"
  fi

  local runid; runid="$(date +%Y%m%d-%H%M%S)"
  [[ -n "$LOG_DIR" ]] || LOG_DIR="$REPO_ROOT/.ralph/logs/$runid"

  build_cmd

  # Config banner
  say "${BOLD}${CYN}Ralph loop${RST} — ${PLAN_REL}"
  say "  ${DIM}prompt${RST}        ${PROMPT}"
  say "  ${DIM}model${RST}         ${MODEL:-(default)}"
  say "  ${DIM}max-iter${RST}      $([[ "$MAX_ITER" -eq 0 ]] && echo 'unlimited' || echo "$MAX_ITER")"
  say "  ${DIM}max-stalls${RST}    $([[ "$MAX_STALLS" -eq 0 ]] && echo 'never' || echo "$MAX_STALLS")"
  say "  ${DIM}sleep${RST}         ${SLEEP_SECS}s"
  if bypasses_permissions; then
    say "  ${DIM}permissions${RST}   ${RED}bypassed${RST}"
  else
    say "  ${DIM}permissions${RST}   ${PERM_MODE:-default}"
  fi
  if [[ -n "$MAX_BUDGET" ]]; then
    if [[ "$MAX_ITER" -ne 0 ]]; then
      local budget_total; budget_total="$(awk "BEGIN{printf \"%.2f\", ${MAX_ITER}*${MAX_BUDGET}}")"
      say "  ${DIM}budget${RST}        \$${MAX_BUDGET}/iter  ${DIM}(worst case \$${budget_total} over ${MAX_ITER} iters)${RST}"
    else
      say "  ${DIM}budget${RST}        \$${MAX_BUDGET}/iter  ${YEL}(unlimited iterations — no total cap)${RST}"
    fi
  fi
  say "  ${DIM}boxes left${RST}    $(count_unchecked)"
  say "  ${DIM}logs${RST}          ${LOG_DIR}"
  say "  ${DIM}command${RST}       $(printf '%q ' "${CLAUDE_CMD[@]}")"
  say ""

  if ! bypasses_permissions && [[ -z "$PERM_MODE" || "$PERM_MODE" == "default" || "$PERM_MODE" == "plan" ]]; then
    warn "permissions are not bypassed; in -p mode the skill can't answer prompts and will likely stall."
    warn "consider --permission-mode acceptEdits, an allowlist via '-- --allowedTools …', or drop --no-bypass."
  fi

  if is_complete; then
    STOP_REASON="already complete"
    say "${GRN}Plan is already complete — nothing to do.${RST}"
    return 0
  fi

  if $DRY_RUN; then
    say "${YEL}dry run — not invoking claude.${RST}"
    return 0
  fi

  confirm
  mkdir -p "$LOG_DIR"
  ensure_gitignored
  trap on_interrupt INT TERM
  START_TS="$(date +%s)"

  local iter=0 stalls=0
  while true; do
    if is_complete; then STOP_REASON="plan complete"; break; fi
    if [[ "$MAX_ITER" -ne 0 && "$iter" -ge "$MAX_ITER" ]]; then
      STOP_REASON="hit iteration cap ($MAX_ITER)"; break
    fi

    iter=$((iter + 1))
    ITERATIONS_RUN="$iter"
    local before_head before_boxes
    before_head="$(git rev-parse HEAD 2>/dev/null || echo none)"
    before_boxes="$(count_unchecked)"
    local iter_log="$LOG_DIR/iter-$(printf '%03d' "$iter").log"

    say ""
    say "${BOLD}${BLU}┌─ iteration ${iter}$([[ "$MAX_ITER" -ne 0 ]] && echo "/$MAX_ITER") ${RST}${DIM}$(date '+%H:%M:%S') · ${before_boxes} boxes left · log: ${iter_log##"$REPO_ROOT"/}${RST}"

    local rc=0
    set +e
    "${CLAUDE_CMD[@]}" < /dev/null 2>&1 | tee "$iter_log"
    rc=${PIPESTATUS[0]}
    set -e

    local after_head after_boxes
    after_head="$(git rev-parse HEAD 2>/dev/null || echo none)"
    after_boxes="$(count_unchecked)"

    local progressed=false commit_note="" last_commit=""
    if [[ "$after_head" != "$before_head" ]]; then
      progressed=true
      last_commit="$(git log -1 --format='%h %s' 2>/dev/null || echo "$after_head")"
      COMMITS+=("$last_commit")
      commit_note=" ${last_commit} ·"
    fi
    [[ "$after_boxes" -lt "$before_boxes" ]] && progressed=true
    [[ ! -f "$PLAN_ABS" ]] && progressed=true   # moved to completed/

    if $progressed; then stalls=0; else stalls=$((stalls + 1)); fi

    local status_color="$GRN" status="ok" stall_note=""
    [[ "$rc" -ne 0 ]] && { status_color="$YEL"; status="claude exit $rc"; }
    $progressed || { status_color="$YEL"; status="no progress"; }
    [[ "$stalls" -gt 0 ]] && stall_note=" · stall ${stalls}/${MAX_STALLS}"
    say "${BOLD}${BLU}└─${RST} ${status_color}${status}${RST}  ${DIM}·${commit_note} ${after_boxes} boxes left${stall_note}${RST}"

    if is_complete; then STOP_REASON="plan complete"; break; fi
    if [[ "$MAX_STALLS" -ne 0 && "$stalls" -ge "$MAX_STALLS" ]]; then
      STOP_REASON="stalled — $stalls runs with no progress"; break
    fi

    [[ "$SLEEP_SECS" -gt 0 ]] && sleep "$SLEEP_SECS"
  done

  trap - INT TERM
  summary
  case "$STOP_REASON" in
    "plan complete") return 0 ;;
    *) return 1 ;;
  esac
}

main "$@"
