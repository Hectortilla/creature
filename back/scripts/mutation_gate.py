#!/usr/bin/env python3
"""Surface the engine mutation score from mutmut's CI/CD stats and ratchet on it.

Run after `mutmut run && mutmut export-cicd-stats` (cwd = back/). Writes a
summary to $GITHUB_STEP_SUMMARY when set and exits non-zero if the score
regressed below the committed baseline (mutation-baseline.json).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATS_PATH = Path("mutants/mutmut-cicd-stats.json")
BASELINE_PATH = Path("mutation-baseline.json")


def mutation_score(stats: dict) -> float:
    """Coverage-conditioned score: caught / viable, excluding uncovered (no_tests) mutants."""
    caught = stats["killed"] + stats["timeout"]
    viable = caught + stats["survived"] + stats["suspicious"]
    return 100.0 * caught / viable


def render_summary(stats: dict, score: float, baseline: float) -> str:
    return "\n".join(
        [
            "## Engine mutation score",
            "",
            f"**{score:.2f}%** caught (baseline floor **{baseline:.2f}%**)",
            "",
            "| killed | timeout | survived | suspicious | no_tests | total |",
            "| --- | --- | --- | --- | --- | --- |",
            f"| {stats['killed']} | {stats['timeout']} | {stats['survived']} "
            f"| {stats['suspicious']} | {stats['no_tests']} | {stats['total']} |",
            "",
            "Score = (killed + timeout) / (killed + timeout + survived + suspicious); "
            "uncovered (no_tests) mutants are excluded so this tracks test *strength*, "
            "not line coverage. Lower it only behind the `harness-change` label.",
        ]
    )


def main() -> int:
    stats = json.loads(STATS_PATH.read_text())
    score = mutation_score(stats)
    baseline = float(json.loads(BASELINE_PATH.read_text())["min_score"])

    summary = render_summary(stats, score, baseline)
    print(summary)

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        Path(step_summary).write_text(summary + "\n")

    if score + 1e-9 < baseline:
        print(f"\n::error::Mutation score {score:.2f}% regressed below baseline {baseline:.2f}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
