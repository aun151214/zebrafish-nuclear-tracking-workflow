#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


EXPECTED = {
    "frames": 75,
    "total_detections": 269330,
    "parent_child_links": 260002,
    "adjacent_frame_links": 251342,
    "two_frame_gap_links": 5756,
    "three_frame_gap_links": 2904,
    "continuous_tracklets": 31125,
    "median_tracklet_length_frames": 4.0,
    "maximum_tracklet_length_frames": 75,
    "tracklets_at_least_10_frames": 8554,
    "tracklets_covering_full_window": 147,
}

APPROXIMATE = {
    "mean_tracklet_length_frames": (8.653172690763052, 1e-9),
    "adjacent_frame_links_percent": (96.66925639033546, 1e-9),
    "tracklets_at_least_10_frames_percent": (27.48273092369478, 1e-9),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def read_summary(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows or set(rows[0]) != {"metric", "value"}:
        raise ValueError(
            "Expected a two-column summary CSV with headers metric,value."
        )

    return {
        row["metric"]: float(row["value"])
        for row in rows
    }


def main() -> None:
    args = parse_args()
    actual = read_summary(args.summary)
    failures: list[str] = []

    for metric, expected in EXPECTED.items():
        observed = actual.get(metric)
        print(f"{metric}: actual={observed}, expected={expected}")
        if observed is None or not math.isclose(
            observed,
            float(expected),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            failures.append(
                f"{metric}: actual={observed}, expected={expected}"
            )

    for metric, (expected, tolerance) in APPROXIMATE.items():
        observed = actual.get(metric)
        print(
            f"{metric}: actual={observed}, "
            f"expected≈{expected}"
        )
        if observed is None or not math.isclose(
            observed,
            expected,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            failures.append(
                f"{metric}: actual={observed}, expected≈{expected}"
            )

    if failures:
        raise SystemExit(
            "FAIL: full-movie tracking regression mismatch:\n- "
            + "\n- ".join(failures)
        )

    print(
        "PASS: full75 detection, link-gap and tracklet metrics "
        "match the thesis targets."
    )


if __name__ == "__main__":
    main()
