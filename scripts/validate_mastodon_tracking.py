#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from zebrafish_tracking.io.mastodon_csv import read_mastodon_links, read_mastodon_spots
from zebrafish_tracking.io.tracking_csv import read_tracking_csv
from zebrafish_tracking.validation.mastodon_workflow import run_mastodon_validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate iTEC detections and adjacent links against Mastodon CSV exports."
    )
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--spots-csv", required=True, type=Path)
    parser.add_argument("--links-csv", required=True, type=Path)
    parser.add_argument("--tracking-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--coordinate-mode",
        required=True,
        choices=["pixels", "micrometres"],
    )
    parser.add_argument("--first-mastodon-frame", required=True, type=int)
    parser.add_argument("--last-mastodon-frame", required=True, type=int)
    parser.add_argument("--frame-offset", type=int, default=1)
    parser.add_argument("--xy-downsample", type=float, default=2.0)
    parser.add_argument("--xy-pixel-size-um", type=float, default=0.347)
    parser.add_argument("--z-spacing-um", type=float, default=0.700)
    parser.add_argument("--thresholds", nargs="+", type=float, required=True)
    parser.add_argument("--reviewed-only-spots", action="store_true")
    parser.add_argument("--reviewed-only-links", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    first_itec_frame = args.first_mastodon_frame + args.frame_offset
    last_itec_frame = args.last_mastodon_frame + args.frame_offset

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
    links = read_mastodon_links(
        args.links_csv,
        reviewed_only=args.reviewed_only_links,
    )
    detections = read_tracking_csv(
        args.tracking_csv,
        frame_min=first_itec_frame,
        frame_max=last_itec_frame,
    )

    summaries = run_mastodon_validation(
        dataset_name=args.dataset_name,
        spots=spots,
        links=links,
        detections=detections,
        thresholds=args.thresholds,
        output_dir=args.output_dir,
    )

    print(f"Mastodon spots: {len(spots)}")
    print(f"Mastodon links loaded: {len(links)}")
    print(f"iTEC detections: {len(detections)}")
    print()
    for row in summaries:
        print(
            f"threshold={row['threshold_itec_units']:g} | "
            f"spots={row['matched_manual_spots']}/{row['manual_spots_evaluated']} "
            f"({100 * row['spot_recovery']:.2f}%) | "
            f"links={row['recovered_adjacent_links']}/{row['evaluated_adjacent_links']} "
            f"({100 * row['overall_link_recovery']:.2f}%) | "
            f"conditional={row['recovered_adjacent_links']}/"
            f"{row['links_with_both_endpoints_matched']} "
            f"({100 * row['conditional_link_recovery']:.2f}%)"
        )
    print(f"\nSaved: {args.output_dir / 'validation_summary.csv'}")


if __name__ == "__main__":
    main()
