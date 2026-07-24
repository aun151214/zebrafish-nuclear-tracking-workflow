#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from zebrafish_tracking.figures.histograms import create_time_coloured_histograms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--dark-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--first-frame", type=int, default=1)
    parser.add_argument("--last-frame", type=int, default=10)
    parser.add_argument(
        "--filename-template",
        default="t{frame:04d}_Channel 2.tif",
    )
    parser.add_argument("--low-range-max", type=int, default=12000)
    args = parser.parse_args()

    if args.last_frame < args.first_frame:
        parser.error("--last-frame must be >= --first-frame")

    frames = list(range(args.first_frame, args.last_frame + 1))
    raw_files = [
        args.raw_dir / args.filename_template.format(frame=frame)
        for frame in frames
    ]
    dark_files = [
        args.dark_dir / args.filename_template.format(frame=frame)
        for frame in frames
    ]

    missing = [path for path in raw_files + dark_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing input files:\n" + "\n".join(str(path) for path in missing)
        )

    create_time_coloured_histograms(
        raw_files,
        dark_files,
        args.output_dir,
        frame_numbers=frames,
        low_range_max=args.low_range_max,
    )


if __name__ == "__main__":
    main()
