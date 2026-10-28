#!/usr/bin/env python3
"""Simulation entry point for the Claude Office Visualizer.

Runs one of five pre-built scenarios against the backend API:

  basic       Simple agent spawn/complete (~60 s)
  complex     Multi-agent workflow with context compaction (~5-10 min) [default]
  edge_cases  Error handling, permissions, orphan cleanup (~2 min)
  quick       Fast (~30 s) full-lifecycle smoke scenario
  teams       Multi-session team scenario (room-orchestrator merge path)

Usage::

    python scripts/simulate_events.py
    python scripts/simulate_events.py complex
    python scripts/simulate_events.py basic
    python scripts/simulate_events.py edge_cases
    python scripts/simulate_events.py quick
    python scripts/simulate_events.py teams

    # Custom session ID
    python scripts/simulate_events.py complex --session my_session_42

    # Suppress progress output
    python scripts/simulate_events.py basic --quiet
"""

import argparse
import os
import sys
from pathlib import Path

# Make the scripts/ directory importable so ``scripts.scenarios`` resolves.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scenarios import SCENARIOS
from scripts.scenarios._base import SimulationContext

DEFAULT_SCENARIO = "complex"
DEFAULT_SESSION_ID = "sim_session_123"


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the simulation entry point."""
    parser = argparse.ArgumentParser(
        description="Run a Claude Office simulation scenario against the local backend.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        default=DEFAULT_SCENARIO,
        choices=list(SCENARIOS.keys()),
        help=f"Scenario to run (default: {DEFAULT_SCENARIO})",
    )
    parser.add_argument(
        "--session",
        default=DEFAULT_SESSION_ID,
        metavar="SESSION_ID",
        help=f"Session ID to use for events (default: {DEFAULT_SESSION_ID})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CLAUDE_OFFICE_API_KEY", ""),
        metavar="KEY",
        help=(
            "API key for the backend. Required when the backend was started with an "
            "explicit CLAUDE_OFFICE_API_KEY (every endpoint then requires it). "
            "Defaults to $CLAUDE_OFFICE_API_KEY."
        ),
    )
    return parser


def main() -> None:
    """Parse arguments and run the requested scenario."""
    parser = build_parser()
    args = parser.parse_args()

    ctx = SimulationContext(
        session_id=args.session,
        verbose=not args.quiet,
        api_key=args.api_key,
    )

    print(f"Running scenario '{args.scenario}' with session '{args.session}'...")
    SCENARIOS[args.scenario](ctx)

    if ctx.failures:
        print(
            f"Done with {ctx.failures} failed event(s) — the backend rejected them "
            f"(check CLAUDE_OFFICE_API_KEY, or that the backend is running).",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
