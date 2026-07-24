#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from zebrafish_tracking.repository_checks import scan_repository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a repository candidate for caches, generated data, local "
            "absolute paths, large files and likely credential material."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root to inspect.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    issues = scan_repository(args.root)

    if issues:
        print("Repository cleanliness check: FAIL")
        print()
        for issue in issues:
            print(
                f"[{issue.category}] {issue.path}: {issue.detail}"
            )
        raise SystemExit(1)

    print("Repository cleanliness check: PASS")
    print(f"Checked: {args.root.resolve()}")


if __name__ == "__main__":
    main()
