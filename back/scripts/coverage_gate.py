#!/usr/bin/env python3
"""Score per-package branch coverage from a coverage JSON and ratchet on it.

Run after `pytest --cov=app --cov-report=json:cov.json` in an infra-equipped job
(full suite, both markers). `coverage json` is keyed per file with no package
rollup, so this sums each package bucket's counts and compares the branch-aware
percent to its floor in coverage-baseline.json. Writes a summary to
$GITHUB_STEP_SUMMARY when set; exits non-zero if any package regressed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

COV_PATH = Path("cov.json")
BASELINE_PATH = Path("coverage-baseline.json")

# package name -> file path prefix in the coverage JSON
PACKAGES = {
    "app.routers": "app/routers/",
    "app.auth": "app/auth/",
    "app.services": "app/services/",
    "app.websocket": "app/websocket/",
}


def package_coverage(files: dict, prefix: str) -> float:
    """Branch-aware percent matching coverage's own metric (branch = true)."""
    covered = statements = 0
    for path, info in files.items():
        if not path.startswith(prefix):
            continue
        summary = info["summary"]
        covered += summary["covered_lines"] + summary["covered_branches"]
        statements += summary["num_statements"] + summary["num_branches"]
    return 100.0 * covered / statements


def render_summary(scores: dict, floors: dict, failures: list) -> str:
    rows = [
        f"| {pkg} | {scores[pkg]:.2f}% | {floors[pkg]:.2f}% | {'❌' if pkg in failures else '✅'} |" for pkg in PACKAGES
    ]
    return "\n".join(
        [
            "## Per-package coverage gate",
            "",
            "| package | coverage | floor | pass |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "Branch-aware coverage of the boundary packages, scored from the "
            "full-suite cov.json. Ratchet upward as tests grow; lower a floor "
            "only behind the `harness-change` label.",
        ]
    )


def main() -> int:
    files = json.loads(COV_PATH.read_text())["files"]
    floors = json.loads(BASELINE_PATH.read_text())["packages"]
    scores = {pkg: package_coverage(files, prefix) for pkg, prefix in PACKAGES.items()}
    failures = [pkg for pkg in PACKAGES if scores[pkg] + 1e-9 < floors[pkg]]

    summary = render_summary(scores, floors, failures)
    print(summary)

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        Path(step_summary).write_text(summary + "\n")

    for pkg in failures:
        print(f"\n::error::{pkg} coverage {scores[pkg]:.2f}% regressed below floor {floors[pkg]:.2f}%")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
