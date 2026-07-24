from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from zebrafish_tracking.io.tracking_csv import safe_float, safe_int
from zebrafish_tracking.validation.matching import ReferenceSpot


CoordinateMode = Literal["pixels", "micrometres"]


@dataclass(frozen=True)
class MastodonSpot(ReferenceSpot):
    """Reference spot converted into the internal iTEC coordinate system."""

    mastodon_frame: int = 0
    source_x: float = 0.0
    source_y: float = 0.0
    source_z: float = 0.0


@dataclass(frozen=True)
class MastodonLink:
    source_spot_id: int
    target_spot_id: int
    displacement_um: float | None = None
    delta_t: float | None = None


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_mastodon_spots(
    path: str | Path,
    *,
    coordinate_mode: CoordinateMode,
    frame_offset: int,
    first_mastodon_frame: int,
    last_mastodon_frame: int,
    xy_downsample: float,
    xy_pixel_size_um: float = 0.347,
    z_spacing_um: float = 0.700,
    reviewed_only: bool = False,
) -> list[MastodonSpot]:
    if xy_downsample <= 0:
        raise ValueError("xy_downsample must be positive")
    if coordinate_mode == "micrometres":
        if xy_pixel_size_um <= 0 or z_spacing_um <= 0:
            raise ValueError("physical calibration values must be positive")

    spots: list[MastodonSpot] = []
    for row in _read_rows(path):
        if reviewed_only and safe_int(row.get("reviewed")) != 1:
            continue

        spot_id = safe_int(row.get("spot_id"))
        mastodon_frame = safe_int(row.get("frame"))
        track_id = safe_int(row.get("track_id"))
        if spot_id is None or mastodon_frame is None:
            continue
        if not first_mastodon_frame <= mastodon_frame <= last_mastodon_frame:
            continue

        if coordinate_mode == "pixels":
            source_x = safe_float(row.get("x_px"))
            source_y = safe_float(row.get("y_px"))
            source_z = safe_float(row.get("z_slice"))
            if None in {source_x, source_y, source_z}:
                continue
            assert source_x is not None and source_y is not None and source_z is not None
            x = source_x / xy_downsample
            y = source_y / xy_downsample
            z = source_z
        elif coordinate_mode == "micrometres":
            source_x = safe_float(row.get("x_um"))
            source_y = safe_float(row.get("y_um"))
            source_z = safe_float(row.get("z_um"))
            if None in {source_x, source_y, source_z}:
                continue
            assert source_x is not None and source_y is not None and source_z is not None
            x = source_x / xy_pixel_size_um / xy_downsample
            y = source_y / xy_pixel_size_um / xy_downsample
            z = source_z / z_spacing_um
        else:
            raise ValueError(f"Unsupported coordinate mode: {coordinate_mode}")

        spots.append(
            MastodonSpot(
                spot_id=spot_id,
                frame=mastodon_frame + frame_offset,
                x=x,
                y=y,
                z=z,
                track_id=track_id,
                mastodon_frame=mastodon_frame,
                source_x=source_x,
                source_y=source_y,
                source_z=source_z,
            )
        )

    if not spots:
        raise ValueError(f"No valid Mastodon spots found in: {path}")
    return spots


def read_mastodon_links(
    path: str | Path,
    *,
    reviewed_only: bool = False,
) -> list[MastodonLink]:
    links: list[MastodonLink] = []
    for row in _read_rows(path):
        if reviewed_only and safe_int(row.get("reviewed")) != 1:
            continue
        source = safe_int(row.get("source_spot_id"))
        target = safe_int(row.get("target_spot_id"))
        if source is None or target is None:
            continue
        links.append(
            MastodonLink(
                source_spot_id=source,
                target_spot_id=target,
                displacement_um=safe_float(row.get("displacement_um")),
                delta_t=safe_float(row.get("delta_t")),
            )
        )
    if not links:
        raise ValueError(f"No valid Mastodon links found in: {path}")
    return links
