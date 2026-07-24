#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from zebrafish_tracking.validation.instance_segmentation import (
    validate_instance_segmentation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate 3D instance-segmentation labels against a labelled "
            "ground-truth TIFF using greedy one-to-one IoU matching."
        )
    )
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--ground-truth-mask", type=Path, required=True)
    parser.add_argument("--prediction-dir", type=Path, required=True)
    parser.add_argument(
        "--prediction-pattern",
        default="t{frame:04d}_Channel 2.mat",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--first-frame", type=int, default=1)
    parser.add_argument("--last-frame", type=int, default=10)
    parser.add_argument("--iou-threshold", type=float, default=0.10)
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows available for {path}")

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.last_frame < args.first_frame:
        raise ValueError("--last-frame must be >= --first-frame")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    frames = range(args.first_frame, args.last_frame + 1)

    frame_results, summary = validate_instance_segmentation(
        run_name=args.run_name,
        ground_truth_mask_path=args.ground_truth_mask,
        prediction_dir=args.prediction_dir,
        frames=frames,
        prediction_pattern=args.prediction_pattern,
        iou_threshold=args.iou_threshold,
    )

    per_frame_path = (
        args.output_dir / "segmentation_per_frame.csv"
    )
    summary_path = (
        args.output_dir / "segmentation_summary.csv"
    )

    write_csv(
        per_frame_path,
        [result.as_dict() for result in frame_results],
    )
    write_csv(summary_path, [summary])

    frame_df = pd.DataFrame(
        [result.as_dict() for result in frame_results]
    )

    figure, axes = plt.subplots(
        2,
        1,
        figsize=(9, 8),
        sharex=True,
    )

    axes[0].plot(
        frame_df["frame"],
        frame_df["precision"],
        marker="o",
        label="Precision",
    )
    axes[0].plot(
        frame_df["frame"],
        frame_df["recall"],
        marker="o",
        label="Recall",
    )
    axes[0].plot(
        frame_df["frame"],
        frame_df["f1"],
        marker="o",
        label="F1",
    )
    axes[0].set_ylabel("Object-level metric")
    axes[0].set_ylim(0, 1.02)
    axes[0].grid(alpha=0.25)
    axes[0].legend(ncol=3)

    axes[1].plot(
        frame_df["frame"],
        frame_df["n_pred"],
        marker="o",
        label="Predicted objects",
    )
    axes[1].plot(
        frame_df["frame"],
        frame_df["n_gt"],
        marker="o",
        label="Ground-truth objects",
    )
    axes[1].set_xlabel("Frame")
    axes[1].set_ylabel("Objects")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    figure.suptitle(
        f"{args.run_name}: object-level segmentation validation"
    )
    figure.tight_layout()
    figure.savefig(
        args.output_dir / "segmentation_validation.png",
        dpi=220,
        bbox_inches="tight",
    )
    figure.savefig(
        args.output_dir / "segmentation_validation.pdf",
        bbox_inches="tight",
    )
    plt.close(figure)

    for result in frame_results:
        print(
            f"frame {result.frame}: "
            f"pred={result.n_pred} gt={result.n_gt} "
            f"TP={result.tp} FP={result.fp} FN={result.fn} "
            f"P={result.precision:.3f} "
            f"R={result.recall:.3f} "
            f"F1={result.f1:.3f} "
            f"IoU={result.mean_matched_iou:.3f}"
        )

    print()
    print("Summary")
    print("=======")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.12f}")
        else:
            print(f"{key}: {value}")
    print()
    print(f"Saved: {per_frame_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
