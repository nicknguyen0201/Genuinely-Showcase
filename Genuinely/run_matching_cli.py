#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run matching cron tasks")
    p.add_argument("--task", required=True, choices=["main", "feedback"])
    return p.parse_args()


def main() -> None:
    # Ensure headless backend in CI.
    os.environ.setdefault("MPLBACKEND", "Agg")

    args = parse_args()

    # Import after env is set.
    import Matching  # noqa: PLC0415

    if args.task == "main":
        Matching.main()
    elif args.task == "feedback":
        Matching.send_feedback_for_latest_round()
    else:
        raise SystemExit(f"Unknown task: {args.task}")


if __name__ == "__main__":
    main()
