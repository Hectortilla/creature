#!/usr/bin/env python3
"""
ralph_loop.py — drive an execution plan to completion, one Ralph iteration at a time.

Inspired by Geoffrey Huntley's "Ralph" technique (https://ghuntley.com/ralph/):
  in its purest form, `while :; do cat PROMPT.md | claude-code; done`.
Here each turn of the loop spawns a FRESH, clean-context Claude Code run that
executes the `/ralph-iteration` skill against a checkbox plan under
`docs/exec-plans/active/`. The skill does ONE step, verifies it, ticks its box,
**stacks a branch on the previous step's and opens/updates a PR (Graphite)**, and
stops — then this loop starts the next clean run. State lives in the plan file and
git history, exactly as Ralph intends; a full run leaves a stack of stacked PRs.

The loop stops when the plan is finished (the skill moves the file out of
`active/`, or no `- [ ]` boxes remain), when it hits the iteration cap, when it
stalls (no progress for N runs in a row), or when you Ctrl-C.

Usage:  scripts/ralph_loop.py [PLAN] [options]      (see --help)
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MAX_ITER = 20  # safety cap; 0 = unlimited
DEFAULT_MAX_STALLS = 3  # consecutive no-progress runs before aborting; 0 = never
DEFAULT_SLEEP_SECS = 3  # pause between iterations

UNCHECKED_RE = re.compile(r"^\s*- \[ \]")


# ---------------------------------------------------------------------------
# Colors (disabled when stdout isn't a TTY, NO_COLOR is set, or --no-color)
# ---------------------------------------------------------------------------
class Colors:
    def __init__(self, enabled: bool) -> None:
        if enabled:
            self.BOLD, self.DIM = "\033[1m", "\033[2m"
            self.RED, self.GRN, self.YEL = "\033[31m", "\033[32m", "\033[33m"
            self.BLU, self.CYN, self.RST = "\033[34m", "\033[36m", "\033[0m"
        else:
            self.BOLD = self.DIM = self.RED = self.GRN = ""
            self.YEL = self.BLU = self.CYN = self.RST = ""


# ---------------------------------------------------------------------------
# Logging — INFO is the script's normal output (stdout); WARNING/ERROR go to
# stderr with a colored `warning:`/`error:` label. The "%(message)s" formatter
# keeps the existing colored banners and summaries byte-for-byte identical.
# ---------------------------------------------------------------------------
log = logging.getLogger("ralph_loop")


class _ConsoleFormatter(logging.Formatter):
    """Render INFO records bare and WARNING/ERROR with a colored label."""

    def __init__(self) -> None:
        super().__init__("%(message)s")
        self.colors = Colors(False)

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        c = self.colors
        if record.levelno >= logging.ERROR:
            return f"{c.RED}error:{c.RST} {msg}"
        if record.levelno >= logging.WARNING:
            return f"{c.YEL}warning:{c.RST} {msg}"
        return msg


_formatter = _ConsoleFormatter()


def _init_logging() -> None:
    """Send INFO to stdout and WARNING/ERROR to stderr."""
    out = logging.StreamHandler(sys.stdout)
    out.addFilter(lambda r: r.levelno < logging.WARNING)
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.WARNING)
    for handler in (out, err):
        handler.setFormatter(_formatter)
    log.setLevel(logging.INFO)
    log.handlers = [out, err]
    log.propagate = False


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    log.error(msg)
    raise SystemExit(2)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
@dataclass
class Config:
    plan_arg: str = ""
    max_iter: int = DEFAULT_MAX_ITER
    max_stalls: int = DEFAULT_MAX_STALLS
    sleep_secs: int = DEFAULT_SLEEP_SECS
    model: str = ""
    perm_mode: str = ""
    bypass: bool = True
    max_budget: str = ""
    prompt_override: str = ""
    log_dir: str = ""
    assume_yes: bool = False
    dry_run: bool = False
    verbose: bool = False
    use_color: bool = True
    extra_args: list[str] = field(default_factory=list)


EPILOG = """\
EXAMPLES
  # Auto-detect the single active plan and run to completion:
  scripts/ralph_loop.py

  # Drive the e2e gameplay harness plan, capped at 12 runs, skip the confirm prompt:
  scripts/ralph_loop.py e2e-gameplay-harness -n 12 -y

  # Use Opus, cap each run at $5, stream tool activity into the logs:
  scripts/ralph_loop.py --model opus --max-budget-usd 5 -v

  # See exactly what it would do without spending anything:
  scripts/ralph_loop.py --dry-run

STOPPING
  - plan complete  : file moved to docs/exec-plans/completed/ or no "- [ ]" boxes left
  - iteration cap  : --max-iterations reached
  - stalled        : --max-stalls consecutive runs made no commit and ticked no box
  - interrupted    : Ctrl-C (prints a summary and exits)

NOTES
  - Each iteration is a fresh `claude -p` run — that clean context is the point of Ralph.
  - The /ralph-iteration skill STACKS each step on the previous via Graphite (`gt`) and
    opens/updates a PR per iteration, so a full run leaves a reviewable stack of PRs.
    Graphite must be set up once on this machine (`gt init` + `gt auth`).
  - The gate the skill must leave green is `cd back && make check` (backend) or the
    `cd front && npm run …` test/build gate (frontend); `make check` at the repo root runs
    both. Postgres + Redis come from `make up` (only integration tests need them).
  - --dangerously-skip-permissions is ON by default because the skill must run builds,
    tests, git and `gt` unattended. Run this in a trusted repo; you'll be asked to confirm
    once (use -y to skip). Ralph is best run in a sandbox/container.
  - Logs land under a gitignored .ralph/ dir so the skill's commits never sweep them.
  - Ralph burns tokens. --max-budget-usd caps EACH iteration, not the run — worst-case
    total is roughly (--max-budget-usd x --max-iterations); set both deliberately.
"""


def split_forwarded(argv: list[str]) -> tuple[list[str], list[str]]:
    """Everything after a standalone `--` is forwarded verbatim to claude."""
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def parse_args(argv: list[str]) -> Config:
    main_args, extra = split_forwarded(argv)

    parser = argparse.ArgumentParser(
        prog="scripts/ralph_loop.py",
        description="Run /ralph-iteration in a loop until an exec-plan is done.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )
    parser.add_argument(
        "plan_pos",
        nargs="?",
        metavar="PLAN",
        help="Plan to drive: a name (with or without .md) resolved under "
        "docs/exec-plans/active/, or an explicit path. If omitted, the "
        "single active plan is auto-detected (errors on zero or several).",
    )
    parser.add_argument(
        "-p",
        "--plan",
        dest="plan_opt",
        metavar="FILE",
        help="Plan name or path (same as the PLAN positional).",
    )
    parser.add_argument(
        "-n",
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITER,
        metavar="N",
        help=f"Stop after N iterations. 0 = unlimited. (default: {DEFAULT_MAX_ITER})",
    )
    parser.add_argument(
        "--max-stalls",
        type=int,
        default=DEFAULT_MAX_STALLS,
        metavar="N",
        help=f"Abort after N consecutive no-progress runs. 0 = never. (default: {DEFAULT_MAX_STALLS})",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=DEFAULT_SLEEP_SECS,
        metavar="SECS",
        help=f"Pause between iterations. (default: {DEFAULT_SLEEP_SECS})",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="",
        metavar="MODEL",
        help="Model passed to claude (e.g. opus, sonnet, a full id).",
    )
    parser.add_argument(
        "--max-budget-usd",
        dest="max_budget",
        default="",
        metavar="AMT",
        help="Cap spend PER ITERATION (claude --max-budget-usd). No cumulative cap.",
    )
    parser.add_argument(
        "--permission-mode",
        dest="perm_mode",
        default="",
        metavar="M",
        help="claude permission mode (default|acceptEdits|auto|bypassPermissions|plan|dontAsk). "
        "Overrides the default --dangerously-skip-permissions.",
    )
    parser.add_argument(
        "--no-bypass",
        dest="bypass",
        action="store_false",
        help="Do NOT pass --dangerously-skip-permissions (unattended runs may stall on prompts).",
    )
    parser.add_argument(
        "--prompt",
        dest="prompt_override",
        default="",
        metavar="TEXT",
        help="Full custom per-iteration prompt (must reference the plan itself).",
    )
    parser.add_argument(
        "--log-dir",
        default="",
        metavar="DIR",
        help="Directory for per-iteration logs. (default: <repo>/.ralph/logs/<runid>)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Pass --verbose to claude."
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="assume_yes",
        action="store_true",
        help="Skip the safety confirmation prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the resolved plan, config, and command; run nothing.",
    )
    parser.add_argument(
        "--no-color",
        dest="use_color",
        action="store_false",
        help="Disable colored output.",
    )

    ns = parser.parse_args(main_args)

    # Reconcile positional vs --plan (mirror the shell's "specified twice" guard).
    if ns.plan_pos and ns.plan_opt and ns.plan_pos != ns.plan_opt:
        die(f"plan specified twice: '{ns.plan_opt}' and '{ns.plan_pos}'")
    plan_arg = ns.plan_opt or ns.plan_pos or ""

    for name, val in (
        ("--max-iterations", ns.max_iterations),
        ("--max-stalls", ns.max_stalls),
        ("--sleep", ns.sleep),
    ):
        if val < 0:
            die(f"{name} must be a non-negative integer (got '{val}')")
    if ns.max_budget and not re.fullmatch(r"[0-9]+(\.[0-9]+)?", ns.max_budget):
        die(f"--max-budget-usd must be a number (got '{ns.max_budget}')")

    return Config(
        plan_arg=plan_arg,
        max_iter=ns.max_iterations,
        max_stalls=ns.max_stalls,
        sleep_secs=ns.sleep,
        model=ns.model,
        perm_mode=ns.perm_mode,
        bypass=ns.bypass,
        max_budget=ns.max_budget,
        prompt_override=ns.prompt_override,
        log_dir=ns.log_dir,
        assume_yes=ns.assume_yes,
        dry_run=ns.dry_run,
        verbose=ns.verbose,
        use_color=ns.use_color,
        extra_args=extra,
    )


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------
class _Interrupted(Exception):
    pass


class RalphLoop:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.c = Colors(
            cfg.use_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
        )
        _formatter.colors = self.c  # color the warning:/error: labels per config
        self.repo_root: Path
        self.active_dir: Path
        self.plan_abs: Path
        self.plan_rel: str
        self.prompt: str = ""
        self.log_dir: Path
        self.claude_cmd: list[str] = []
        # state
        self.iterations_run = 0
        self.commits: list[str] = []
        self.start_ts = 0.0
        self.stop_reason = "(none)"
        self._proc: subprocess.Popen | None = None

    # -- git / plan helpers -------------------------------------------------
    def _git(self, *args: str) -> str:
        out = subprocess.run(
            ["git", "-C", str(self.repo_root), *args], capture_output=True, text=True
        )
        return out.stdout.strip()

    def count_unchecked(self) -> int:
        if not self.plan_abs.exists():
            return 0
        text = self.plan_abs.read_text(encoding="utf-8", errors="replace")
        return sum(1 for line in text.splitlines() if UNCHECKED_RE.match(line))

    def is_complete(self) -> bool:
        return (not self.plan_abs.exists()) or self.count_unchecked() == 0

    def resolve_plan(self) -> None:
        arg = self.cfg.plan_arg
        if arg:
            p = Path(arg)
            if p.is_file():
                self.plan_abs = p.resolve()
                return
            name = arg if arg.endswith(".md") else f"{arg}.md"
            if (self.active_dir / name).is_file():
                self.plan_abs = self.active_dir / name
                return
            if (self.repo_root / arg).is_file():
                self.plan_abs = self.repo_root / arg
                return
            die(
                f"plan not found: '{arg}' (looked in {self.active_dir}/ and {self.repo_root}/)"
            )

        plans = (
            sorted(p for p in self.active_dir.glob("*.md") if p.name != "README.md")
            if self.active_dir.is_dir()
            else []
        )
        if not plans:
            die(f"no active plans in {self.active_dir}/ — name one explicitly.")
        if len(plans) > 1:
            listing = "\n".join(f"    {p.name}" for p in plans)
            log.error(f"multiple active plans — pick one:\n{listing}")
            raise SystemExit(1)
        self.plan_abs = plans[0]

    def ensure_gitignored(self) -> None:
        # Only manage the default in-repo .ralph/ location.
        try:
            self.log_dir.relative_to(self.repo_root / ".ralph")
        except ValueError:
            return
        probe = self.repo_root / ".ralph" / "probe"
        ignored = subprocess.run(
            ["git", "-C", str(self.repo_root), "check-ignore", "-q", str(probe)]
        )
        if ignored.returncode != 0:
            gi = self.repo_root / ".gitignore"
            with gi.open("a", encoding="utf-8") as fh:
                fh.write("\n# Ralph loop logs (scripts/ralph_loop.py)\n.ralph/\n")
            log.info(f"{self.c.DIM}added .ralph/ to .gitignore{self.c.RST}")

    # -- command / env ------------------------------------------------------
    def build_cmd(self) -> None:
        cmd = ["claude", "-p", self.prompt]
        if self.cfg.model:
            cmd += ["--model", self.cfg.model]
        if self.cfg.perm_mode:
            cmd += ["--permission-mode", self.cfg.perm_mode]
        elif self.cfg.bypass:
            cmd += ["--dangerously-skip-permissions"]
        if self.cfg.max_budget:
            cmd += ["--max-budget-usd", self.cfg.max_budget]
        if self.cfg.verbose:
            cmd += ["--verbose"]
        cmd += self.cfg.extra_args
        self.claude_cmd = cmd

    def bypasses_permissions(self) -> bool:
        if self.cfg.perm_mode:
            return self.cfg.perm_mode == "bypassPermissions"
        return self.cfg.bypass

    # -- confirmation -------------------------------------------------------
    def confirm(self) -> None:
        if self.cfg.assume_yes:
            return
        if not sys.stdin.isatty():
            die(
                "stdin is not a TTY — refusing to start unattended. Pass -y/--yes to run non-interactively."
            )
        c = self.c
        # Interactive prompt: written straight to stdout (not the logger) so it
        # shares a line with the reply the user types.
        sys.stdout.write(f"{c.BOLD}Start the loop?{c.RST} ")
        if self.bypasses_permissions():
            sys.stdout.write(
                f"{c.RED}Permissions will be bypassed{c.RST} — this runs builds, "
                "tests, git and gt unattended,\n"
                "and opens/updates PRs each iteration.\n"
            )
        try:
            with open("/dev/tty") as tty:
                sys.stdout.write(f"Type {c.BOLD}yes{c.RST} to continue: ")
                sys.stdout.flush()
                reply = tty.readline().strip()
        except OSError:
            reply = ""
        if reply != "yes":
            die("aborted.")

    # -- output -------------------------------------------------------------
    def banner(self) -> None:
        c = self.c
        max_iter = "unlimited" if self.cfg.max_iter == 0 else str(self.cfg.max_iter)
        max_stalls = "never" if self.cfg.max_stalls == 0 else str(self.cfg.max_stalls)
        log.info(f"{c.BOLD}{c.CYN}Ralph loop{c.RST} — {self.plan_rel}")
        log.info(f"  {c.DIM}prompt{c.RST}        {self.prompt}")
        log.info(f"  {c.DIM}model{c.RST}         {self.cfg.model or '(default)'}")
        log.info(f"  {c.DIM}max-iter{c.RST}      {max_iter}")
        log.info(f"  {c.DIM}max-stalls{c.RST}    {max_stalls}")
        log.info(f"  {c.DIM}sleep{c.RST}         {self.cfg.sleep_secs}s")
        if self.bypasses_permissions():
            log.info(f"  {c.DIM}permissions{c.RST}   {c.RED}bypassed{c.RST}")
        else:
            log.info(f"  {c.DIM}permissions{c.RST}   {self.cfg.perm_mode or 'default'}")
        if self.cfg.max_budget:
            if self.cfg.max_iter != 0:
                total = f"{self.cfg.max_iter * float(self.cfg.max_budget):.2f}"
                log.info(
                    f"  {c.DIM}budget{c.RST}        ${self.cfg.max_budget}/iter  "
                    f"{c.DIM}(worst case ${total} over {self.cfg.max_iter} iters){c.RST}"
                )
            else:
                log.info(
                    f"  {c.DIM}budget{c.RST}        ${self.cfg.max_budget}/iter  "
                    f"{c.YEL}(unlimited iterations — no total cap){c.RST}"
                )
        log.info(f"  {c.DIM}boxes left{c.RST}    {self.count_unchecked()}")
        log.info(f"  {c.DIM}logs{c.RST}          {self.log_dir}")
        log.info(
            f"  {c.DIM}command{c.RST}       {' '.join(shlex.quote(a) for a in self.claude_cmd)}"
        )
        log.info("")

    def summary(self) -> None:
        c = self.c
        secs = int(time.time() - self.start_ts) if self.start_ts else 0
        log.info("")
        log.info(
            f"{c.BOLD}── Ralph loop summary ─────────────────────────────────{c.RST}"
        )
        log.info(f"  plan        {self.plan_rel}")
        log.info(f"  stopped     {c.BOLD}{self.stop_reason}{c.RST}")
        log.info(f"  iterations  {self.iterations_run}")
        log.info(f"  commits     {len(self.commits)}")
        for commit in self.commits:
            log.info(f"                {c.DIM}{commit}{c.RST}")
        log.info(f"  boxes left  {self.count_unchecked()}")
        log.info(f"  elapsed     {secs}s")
        log.info(f"  logs        {self.log_dir}")
        log.info(
            f"{c.BOLD}───────────────────────────────────────────────────────{c.RST}"
        )

    # -- one iteration ------------------------------------------------------
    def run_iteration(self, iter_log: Path) -> int:
        """Stream a fresh `claude -p` run to console + log file (tee). Returns claude's rc."""
        self._proc = subprocess.Popen(
            self.claude_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        try:
            with iter_log.open("w", encoding="utf-8") as logf:
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    logf.write(line)
            return self._proc.wait()
        finally:
            self._proc = None

    # -- main ---------------------------------------------------------------
    def setup(self) -> None:
        toplevel = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
        if toplevel.returncode != 0:
            die("not inside a git repository.")
        self.repo_root = Path(toplevel.stdout.strip())
        os.chdir(self.repo_root)
        self.active_dir = self.repo_root / "docs" / "exec-plans" / "active"

        if (
            subprocess.run(
                ["sh", "-c", "command -v claude"], capture_output=True
            ).returncode
            != 0
        ):
            die("'claude' CLI not found on PATH.")
        if (
            subprocess.run(
                ["sh", "-c", "command -v gt"], capture_output=True
            ).returncode
            != 0
        ):
            log.warning(
                "'gt' (Graphite) not found on PATH — the /ralph-iteration skill "
                "needs it to stack branches/PRs. Install it and run `gt init` "
                "+ `gt auth`."
            )

        self.resolve_plan()
        self.plan_rel = str(self.plan_abs.relative_to(self.repo_root))
        self.prompt = (
            self.cfg.prompt_override
            or f"/ralph-iteration do the next iteration of @{self.plan_rel}"
        )

        runid = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_dir = (
            Path(self.cfg.log_dir)
            if self.cfg.log_dir
            else self.repo_root / ".ralph" / "logs" / runid
        )

        self.build_cmd()

    def run(self) -> int:
        self.setup()
        self.banner()

        if not self.bypasses_permissions() and self.cfg.perm_mode in (
            "",
            "default",
            "plan",
        ):
            log.warning(
                "permissions are not bypassed; in -p mode the skill can't answer "
                "prompts and will likely stall."
            )
            log.warning(
                "consider --permission-mode acceptEdits, an allowlist via "
                "'-- --allowedTools …', or drop --no-bypass."
            )

        if self.is_complete():
            self.stop_reason = "already complete"
            log.info(
                f"{self.c.GRN}Plan is already complete — nothing to do.{self.c.RST}"
            )
            return 0

        if self.cfg.dry_run:
            log.info(f"{self.c.YEL}dry run — not invoking claude.{self.c.RST}")
            return 0

        self.confirm()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_gitignored()

        signal.signal(signal.SIGTERM, self._on_signal)
        self.start_ts = time.time()

        iteration = 0
        stalls = 0
        try:
            while True:
                if self.is_complete():
                    self.stop_reason = "plan complete"
                    break
                if self.cfg.max_iter != 0 and iteration >= self.cfg.max_iter:
                    self.stop_reason = f"hit iteration cap ({self.cfg.max_iter})"
                    break

                iteration += 1
                self.iterations_run = iteration
                before_head = self._git("rev-parse", "HEAD") or "none"
                before_boxes = self.count_unchecked()
                iter_log = self.log_dir / f"iter-{iteration:03d}.log"

                c = self.c
                cap = f"/{self.cfg.max_iter}" if self.cfg.max_iter != 0 else ""
                log.info("")
                log.info(
                    f"{c.BOLD}{c.BLU}┌─ iteration {iteration}{cap} {c.RST}{c.DIM}"
                    f"{datetime.now().strftime('%H:%M:%S')} · {before_boxes} boxes left · "
                    f"log: {iter_log.relative_to(self.repo_root)}{c.RST}"
                )

                rc = self.run_iteration(iter_log)

                after_head = self._git("rev-parse", "HEAD") or "none"
                after_boxes = self.count_unchecked()

                progressed = False
                commit_note = ""
                if after_head != before_head:
                    progressed = True
                    last_commit = self._git("log", "-1", "--format=%h %s") or after_head
                    self.commits.append(last_commit)
                    commit_note = f" {last_commit} ·"
                if after_boxes < before_boxes:
                    progressed = True
                if not self.plan_abs.exists():  # moved to completed/
                    progressed = True

                stalls = 0 if progressed else stalls + 1

                status_color, status = c.GRN, "ok"
                if rc != 0:
                    status_color, status = c.YEL, f"claude exit {rc}"
                if not progressed:
                    status_color, status = c.YEL, "no progress"
                stall_note = (
                    f" · stall {stalls}/{self.cfg.max_stalls}" if stalls > 0 else ""
                )
                log.info(
                    f"{c.BOLD}{c.BLU}└─{c.RST} {status_color}{status}{c.RST}  "
                    f"{c.DIM}·{commit_note} {after_boxes} boxes left{stall_note}{c.RST}"
                )

                if self.is_complete():
                    self.stop_reason = "plan complete"
                    break
                if self.cfg.max_stalls != 0 and stalls >= self.cfg.max_stalls:
                    self.stop_reason = f"stalled — {stalls} runs with no progress"
                    break

                if self.cfg.sleep_secs > 0:
                    time.sleep(self.cfg.sleep_secs)
        except (KeyboardInterrupt, _Interrupted):
            self.stop_reason = "interrupted (Ctrl-C)"
            log.info("")
            log.warning("interrupted — finishing up.")
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
            self.summary()
            return 130

        self.summary()
        return 0 if self.stop_reason == "plan complete" else 1

    def _on_signal(self, *_args: object) -> None:
        raise _Interrupted()


def main() -> int:
    _init_logging()
    cfg = parse_args(sys.argv[1:])
    return RalphLoop(cfg).run()


if __name__ == "__main__":
    raise SystemExit(main())
