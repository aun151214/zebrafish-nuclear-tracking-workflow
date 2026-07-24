#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_one(path: str | Path) -> dict[str, str]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError(f"Expected one summary row in {path}, found {len(rows)}")
    return rows[0]


def close(value: float, expected: float, tolerance: float = 0.0006) -> bool:
    return abs(value - expected) <= tolerance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["tenframe", "full75"], required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    row = read_one(args.summary)

    exact = {
        "tenframe": {
            "components": 46,
            "fully_recovered": 29,
            "all_spots_matched_link_break": 6,
            "partially_recovered": 8,
            "not_recovered": 3,
            "components_mapped_to_one_itec_tracklet": 28,
            "components_mapped_to_multiple_itec_tracklets": 15,
        },
        "full75": {
            "components": 46,
            "fully_recovered": 7,
            "all_spots_matched_link_break": 12,
            "partially_recovered": 27,
            "not_recovered": 0,
        },
    }[args.profile]

    errors: list[str] = []
    for field, expected in exact.items():
        actual = int(round(float(row[field])))
        print(f"{field}: actual={actual}, expected={expected}")
        if actual != expected:
            errors.append(f"{field}: {actual} != {expected}")

    rounded = {
        "tenframe": {
            "mean_component_spot_recovery": 0.8785,
            "mean_component_overall_link_recovery": 0.8004,
            "mean_longest_recovered_segment_fraction": 0.7405,
        },
        "full75": {
            "mean_component_spot_recovery": 0.9004,
            "median_component_spot_recovery": 0.9724,
            "mean_component_overall_link_recovery": 0.8051,
            "median_component_overall_link_recovery": 0.8749,
            "mean_component_conditional_link_recovery": 0.9237,
            "median_component_conditional_link_recovery": 0.9344,
        },
    }[args.profile]

    for field, expected in rounded.items():
        actual = float(row[field])
        print(f"{field}: actual={actual:.6f}, expected≈{expected:.4f}")
        if not close(actual, expected):
            errors.append(f"{field}: {actual:.6f} not within tolerance of {expected:.4f}")

    if errors:
        raise SystemExit("FAIL:\n- " + "\n- ".join(errors))
    print(f"PASS: {args.profile} component continuity matches thesis targets.")


if __name__ == "__main__":
    main()
