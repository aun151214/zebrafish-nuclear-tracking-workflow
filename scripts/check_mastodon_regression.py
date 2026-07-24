#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROFILES = {
    "tenframe": {
        "manual_spots": 450,
        "adjacent_links": 398,
        "thresholds": {
            6.0: {
                "matched": 395,
                "both": 334,
                "recovered": 318,
                "spot_percent": 87.8,
                "overall_percent": 79.9,
                "conditional_percent": 95.2,
            },
            8.0: {
                "spot_percent": 93.3,
                "overall_percent": 83.9,
                "conditional_percent": 92.5,
            },
            10.0: {
                "spot_percent": 98.7,
                "overall_percent": 86.9,
                "conditional_percent": 88.9,
            },
        },
    },
    "full75": {
        "manual_spots": 2910,
        "adjacent_links": 2791,
        "thresholds": {
            6.0: {
                "matched": 2584,
                "both": 2392,
                "recovered": 2214,
                "spot_percent": 88.80,
                "overall_percent": 79.33,
                "conditional_percent": 92.56,
            },
            8.0: {
                "spot_percent": 95.84,
                "overall_percent": 83.81,
                "conditional_percent": 88.94,
            },
            10.0: {
                "spot_percent": 99.55,
                "overall_percent": 85.38,
                "conditional_percent": 86.06,
            },
        },
    },
}


def rounded_matches(actual: float, expected: float) -> bool:
    decimal_places = len(str(expected).split(".")[1]) if "." in str(expected) else 0
    return round(actual, decimal_places) == expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    with args.summary.open(newline="", encoding="utf-8-sig") as handle:
        rows = {float(row["threshold_itec_units"]): row for row in csv.DictReader(handle)}

    profile = PROFILES[args.profile]
    failures: list[str] = []

    for threshold, expected in profile["thresholds"].items():
        row = rows.get(threshold)
        if row is None:
            failures.append(f"missing threshold {threshold:g}")
            continue

        manual_spots = int(row["manual_spots_evaluated"])
        matched = int(row["matched_manual_spots"])
        adjacent = int(row["evaluated_adjacent_links"])
        both = int(row["links_with_both_endpoints_matched"])
        recovered = int(row["recovered_adjacent_links"])

        spot_percent = 100.0 * float(row["spot_recovery"])
        overall_percent = 100.0 * float(row["overall_link_recovery"])
        conditional_percent = 100.0 * float(row["conditional_link_recovery"])

        print(
            f"threshold {threshold:g}: spots={matched}/{manual_spots} "
            f"({spot_percent:.4f}%), links={recovered}/{adjacent} "
            f"({overall_percent:.4f}%), conditional={recovered}/{both} "
            f"({conditional_percent:.4f}%)"
        )

        if manual_spots != profile["manual_spots"]:
            failures.append(
                f"threshold {threshold:g}: manual spots {manual_spots} != "
                f"{profile['manual_spots']}"
            )
        if adjacent != profile["adjacent_links"]:
            failures.append(
                f"threshold {threshold:g}: adjacent links {adjacent} != "
                f"{profile['adjacent_links']}"
            )

        for key, actual in [
            ("matched", matched),
            ("both", both),
            ("recovered", recovered),
        ]:
            if key in expected and actual != expected[key]:
                failures.append(
                    f"threshold {threshold:g}: {key} {actual} != {expected[key]}"
                )

        for key, actual in [
            ("spot_percent", spot_percent),
            ("overall_percent", overall_percent),
            ("conditional_percent", conditional_percent),
        ]:
            if not rounded_matches(actual, expected[key]):
                failures.append(
                    f"threshold {threshold:g}: {key} {actual:.6f} does not round "
                    f"to {expected[key]}"
                )

    if failures:
        raise SystemExit("REGRESSION FAILED\n" + "\n".join(failures))
    print(f"PASS: {args.profile} Mastodon metrics match the thesis regression targets.")


if __name__ == "__main__":
    main()
