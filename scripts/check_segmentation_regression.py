#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


EXPECTED = {
    "amin200": {
        "frames_evaluated": 10,
        "iou_threshold": 0.10,
        "mean_n_pred": 4577.8,
        "mean_n_gt": 3642.2,
        "total_tp": 34524,
        "total_fp": 11254,
        "total_fn": 1898,
        "mean_precision": 0.7539481810843981,
        "mean_recall": 0.9479953069834037,
        "mean_f1": 0.8397007528285018,
        "mean_matched_iou": 0.5138008467494878,
    },
    "amin1000": {
        "frames_evaluated": 10,
        "iou_threshold": 0.10,
        "mean_n_pred": 3937.4,
        "mean_n_gt": 3642.2,
        "total_tp": 33490,
        "total_fp": 5884,
        "total_fn": 2932,
        "mean_precision": 0.8508183518434883,
        "mean_recall": 0.9201791120030078,
        "mean_f1": 0.8839827629218917,
        "mean_matched_iou": 0.5186769841062594,
    },
}

EXACT_PER_FRAME_COLUMNS = [
    "frame",
    "n_pred",
    "n_gt",
    "tp",
    "fp",
    "fn",
]

FLOAT_PER_FRAME_COLUMNS = [
    "precision",
    "recall",
    "f1",
    "mean_matched_iou",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=sorted(EXPECTED),
        required=True,
    )
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--per-frame", type=Path)
    parser.add_argument("--reference-per-frame", type=Path)
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-12,
    )
    return parser.parse_args()


def read_single_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one summary row in {path}, got {len(rows)}"
        )
    return rows[0]


def read_rows_by_frame(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    return {
        int(float(row["frame"])): row
        for row in rows
    }


def compare_per_frame(
    actual_path: Path,
    reference_path: Path,
    tolerance: float,
) -> list[str]:
    actual = read_rows_by_frame(actual_path)
    reference = read_rows_by_frame(reference_path)
    failures: list[str] = []

    if set(actual) != set(reference):
        return [
            "Per-frame frame sets differ: "
            f"actual={sorted(actual)}, reference={sorted(reference)}"
        ]

    for frame in sorted(actual):
        for column in EXACT_PER_FRAME_COLUMNS:
            observed = int(round(float(actual[frame][column])))
            expected = int(round(float(reference[frame][column])))
            if observed != expected:
                failures.append(
                    f"Frame {frame} {column}: "
                    f"actual={observed}, reference={expected}"
                )

        for column in FLOAT_PER_FRAME_COLUMNS:
            observed = float(actual[frame][column])
            expected = float(reference[frame][column])
            if not math.isclose(
                observed,
                expected,
                rel_tol=0.0,
                abs_tol=tolerance,
            ):
                failures.append(
                    f"Frame {frame} {column}: "
                    f"actual={observed}, reference={expected}"
                )

    return failures


def main() -> None:
    args = parse_args()
    row = read_single_row(args.summary)
    expected = EXPECTED[args.profile]
    failures: list[str] = []

    for metric, expected_value in expected.items():
        if metric not in row:
            failures.append(f"Missing summary metric: {metric}")
            continue

        observed = float(row[metric])
        print(
            f"{metric}: actual={observed}, expected={expected_value}"
        )

        if not math.isclose(
            observed,
            float(expected_value),
            rel_tol=0.0,
            abs_tol=args.tolerance,
        ):
            failures.append(
                f"{metric}: actual={observed}, expected={expected_value}"
            )

    if (args.per_frame is None) != (
        args.reference_per_frame is None
    ):
        failures.append(
            "--per-frame and --reference-per-frame must be supplied together"
        )
    elif (
        args.per_frame is not None
        and args.reference_per_frame is not None
    ):
        failures.extend(
            compare_per_frame(
                args.per_frame,
                args.reference_per_frame,
                args.tolerance,
            )
        )

    if failures:
        raise SystemExit(
            "FAIL: segmentation regression mismatch:\n- "
            + "\n- ".join(failures)
        )

    print(
        f"PASS: {args.profile} object-level segmentation metrics "
        "match the thesis regression targets."
    )


if __name__ == "__main__":
    main()
