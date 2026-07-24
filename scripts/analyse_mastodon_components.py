#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from zebrafish_tracking.io.mastodon_csv import read_mastodon_spots
from zebrafish_tracking.io.tracking_csv import read_tracking_csv
from zebrafish_tracking.validation.component_continuity import (
    analyse_track_components,
    read_csv_rows,
    write_component_analysis,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse Mastodon track/component continuity from validated matches."
    )
    parser.add_argument("--profile", choices=["tenframe", "full75"], required=True)
    parser.add_argument("--spots-csv", required=True)
    parser.add_argument("--matches-csv", required=True)
    parser.add_argument("--link-validation-csv", required=True)
    parser.add_argument("--tracking-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--coordinate-mode", choices=["pixels", "micrometres"], required=True)
    parser.add_argument("--first-mastodon-frame", type=int, required=True)
    parser.add_argument("--last-mastodon-frame", type=int, required=True)
    parser.add_argument("--frame-offset", type=int, default=1)
    parser.add_argument("--xy-downsample", type=float, default=2.0)
    parser.add_argument("--xy-pixel-size-um", type=float, default=0.347)
    parser.add_argument("--z-spacing-um", type=float, default=0.700)
    parser.add_argument("--reviewed-only-spots", action="store_true")
    args = parser.parse_args()

    spots = read_mastodon_spots(
        args.spots_csv,
        coordinate_mode=args.coordinate_mode,
        frame_offset=args.frame_offset,
        first_mastodon_frame=args.first_mastodon_frame,
        last_mastodon_frame=args.last_mastodon_frame,
        xy_downsample=args.xy_downsample,
        xy_pixel_size_um=args.xy_pixel_size_um,
        z_spacing_um=args.z_spacing_um,
        reviewed_only=args.reviewed_only_spots,
    )
    detections = read_tracking_csv(
        args.tracking_csv,
        frame_min=args.first_mastodon_frame + args.frame_offset,
        frame_max=args.last_mastodon_frame + args.frame_offset,
    )
    cross_track_mode = "exclude" if args.profile == "tenframe" else "source"
    component_rows, status_rows, aggregate = analyse_track_components(
        spots=spots,
        match_rows=read_csv_rows(args.matches_csv),
        link_rows=read_csv_rows(args.link_validation_csv),
        detections=detections,
        cross_track_mode=cross_track_mode,
    )
    write_component_analysis(args.output_dir, component_rows, status_rows, aggregate)

    print(f"Components: {aggregate['components']}")
    print(
        "status="
        f"{aggregate['fully_recovered']}/"
        f"{aggregate['all_spots_matched_link_break']}/"
        f"{aggregate['partially_recovered']}/"
        f"{aggregate['not_recovered']}"
    )
    print(
        "spot mean/median="
        f"{100 * aggregate['mean_component_spot_recovery']:.2f}%/"
        f"{100 * aggregate['median_component_spot_recovery']:.2f}%"
    )
    print(
        "overall-link mean/median="
        f"{100 * aggregate['mean_component_overall_link_recovery']:.2f}%/"
        f"{100 * aggregate['median_component_overall_link_recovery']:.2f}%"
    )
    print(f"Saved: {Path(args.output_dir) / 'aggregate_summary.csv'}")


if __name__ == "__main__":
    main()
