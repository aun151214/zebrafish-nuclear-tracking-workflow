#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from zebrafish_tracking.analysis.full_movie_tracking import (
    parent_link_gap_counts,
    summarize_full_movie_tracking,
    tracklet_length_counts,
    tracklet_rows,
    tracklet_survival,
)
from zebrafish_tracking.io.tracking_csv import read_tracking_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize detections, parent-link frame gaps and continuous "
            "one-to-one tracklets from an iTEC tracking_result.csv."
        )
    )
    parser.add_argument("--tracking-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frame-min", type=int)
    parser.add_argument("--frame-max", type=int)
    return parser.parse_args()


def save_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    detections = read_tracking_csv(
        args.tracking_csv,
        frame_min=args.frame_min,
        frame_max=args.frame_max,
    )

    summary, frame_counts, links, tracklets = summarize_full_movie_tracking(
        detections,
        frame_min=args.frame_min,
        frame_max=args.frame_max,
    )

    frame_min = int(summary["frame_min"])
    frame_max = int(summary["frame_max"])

    summary_rows = [
        {"metric": metric, "value": value}
        for metric, value in summary.items()
    ]
    save_rows(args.output_dir / "tracking_summary.csv", summary_rows)
    save_rows(args.output_dir / "detections_per_frame.csv", frame_counts)
    save_rows(
        args.output_dir / "parent_link_gap_counts.csv",
        parent_link_gap_counts(links),
    )
    save_rows(
        args.output_dir / "continuous_one_to_one_tracklets.csv",
        tracklet_rows(
            tracklets,
            frame_min=frame_min,
            frame_max=frame_max,
        ),
    )
    save_rows(
        args.output_dir / "tracklet_length_counts.csv",
        tracklet_length_counts(tracklets),
    )
    save_rows(
        args.output_dir / "tracklet_survival.csv",
        tracklet_survival(
            tracklets,
            maximum_length=frame_max - frame_min + 1,
        ),
    )

    detections_df = pd.DataFrame(frame_counts)
    gap_df = pd.DataFrame(parent_link_gap_counts(links))
    length_df = pd.DataFrame(tracklet_length_counts(tracklets))
    survival_df = pd.DataFrame(
        tracklet_survival(
            tracklets,
            maximum_length=frame_max - frame_min + 1,
        )
    )

    fig, axis = plt.subplots(figsize=(10, 5.5))
    axis.plot(
        detections_df["frame"],
        detections_df["detections"],
        marker="o",
        markersize=3,
        linewidth=1,
        label="Per-frame detections",
    )
    axis.plot(
        detections_df["frame"],
        detections_df["detections"].rolling(
            window=5,
            center=True,
            min_periods=1,
        ).mean(),
        linewidth=2,
        label="5-frame moving average",
    )
    axis.set_xlabel("Frame")
    axis.set_ylabel("Detections")
    axis.set_title("iTEC detections per frame")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "01_detections_per_frame.png", dpi=220)
    fig.savefig(args.output_dir / "01_detections_per_frame.pdf")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7.5, 5))
    axis.bar(gap_df["frame_gap"].astype(str), gap_df["links"])
    axis.set_xlabel("Child frame - parent frame")
    axis.set_ylabel("Links")
    axis.set_title("Parent-child frame-gap distribution")
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.output_dir / "02_parent_link_frame_gaps.png", dpi=220)
    fig.savefig(args.output_dir / "02_parent_link_frame_gaps.pdf")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 5.5))
    axis.bar(length_df["length_frames"], length_df["tracklets"], width=0.9)
    axis.set_xlabel("Continuous one-to-one tracklet length (frames)")
    axis.set_ylabel("Tracklets")
    axis.set_title("Continuous tracklet-length distribution")
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.output_dir / "03_tracklet_length_distribution.png", dpi=220)
    fig.savefig(args.output_dir / "03_tracklet_length_distribution.pdf")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 5.5))
    axis.plot(
        survival_df["minimum_length_frames"],
        survival_df["percent"],
        linewidth=2,
    )
    axis.set_xlabel("Minimum tracklet length (frames)")
    axis.set_ylabel("Tracklets at least this long (%)")
    axis.set_title("Continuous tracklet survival")
    axis.set_ylim(0, 100)
    axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.output_dir / "04_tracklet_survival.png", dpi=220)
    fig.savefig(args.output_dir / "04_tracklet_survival.pdf")
    plt.close(fig)

    print("Full-movie tracking summary")
    print("==========================")
    for metric, value in summary.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.6f}")
        else:
            print(f"{metric}: {value}")
    print()
    print(f"Saved: {args.output_dir / 'tracking_summary.csv'}")


if __name__ == "__main__":
    main()
