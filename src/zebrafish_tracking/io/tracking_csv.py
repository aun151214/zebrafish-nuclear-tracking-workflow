from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    detection_id: int
    frame: int
    x: float
    y: float
    z: float
    parents: tuple[int, ...]
    incoming_links: int | None = None
    outgoing_links: int | None = None


def safe_int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none"}:
            return None
        return int(round(float(text)))
    except (TypeError, ValueError):
        return None


def safe_float(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none"}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_parent_ids(value: object) -> tuple[int, ...]:
    if value is None:
        return ()

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "[]", "0", "0.0"}:
        return ()

    parent_ids = {
        int(round(float(match)))
        for match in re.findall(r"-?\d+(?:\.\d+)?", text)
        if float(match) > 0
    }
    return tuple(sorted(parent_ids))


def read_tracking_csv(
    path: str | Path,
    *,
    frame_min: int | None = None,
    frame_max: int | None = None,
) -> dict[int, Detection]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"ID", "frames", "xCoord", "yCoord", "zCoord", "parents"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing tracking columns: " + ", ".join(sorted(missing)))

        detections: dict[int, Detection] = {}
        for row in reader:
            detection_id = safe_int(row.get("ID"))
            frame = safe_int(row.get("frames"))
            x = safe_float(row.get("xCoord"))
            y = safe_float(row.get("yCoord"))
            z = safe_float(row.get("zCoord"))

            if None in {detection_id, frame, x, y, z}:
                continue
            assert detection_id is not None and frame is not None
            assert x is not None and y is not None and z is not None

            if frame_min is not None and frame < frame_min:
                continue
            if frame_max is not None and frame > frame_max:
                continue
            if detection_id in detections:
                raise ValueError(f"Duplicate detection ID: {detection_id}")

            detections[detection_id] = Detection(
                detection_id=detection_id,
                frame=frame,
                x=x,
                y=y,
                z=z,
                parents=parse_parent_ids(row.get("parents")),
                incoming_links=safe_int(row.get("incoming links")),
                outgoing_links=safe_int(row.get("outgoing links")),
            )

    if not detections:
        raise ValueError(f"No valid detections found in: {csv_path}")
    return detections
