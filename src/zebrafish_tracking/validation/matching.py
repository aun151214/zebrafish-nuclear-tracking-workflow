from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

from zebrafish_tracking.io.tracking_csv import Detection


@dataclass(frozen=True)
class ReferenceSpot:
    spot_id: int
    frame: int
    x: float
    y: float
    z: float
    track_id: int | None = None


@dataclass(frozen=True)
class SpotMatch:
    spot_id: int
    detection_id: int
    frame: int
    distance: float


def euclidean_distance(a: ReferenceSpot, b: Detection) -> float:
    return math.sqrt(
        (a.x - b.x) ** 2
        + (a.y - b.y) ** 2
        + (a.z - b.z) ** 2
    )


def greedy_one_to_one_matches(
    reference_spots: Iterable[ReferenceSpot],
    detections: Mapping[int, Detection],
    *,
    threshold: float,
) -> tuple[list[SpotMatch], list[ReferenceSpot]]:
    """Replicate the thesis framewise greedy one-to-one assignment.

    Candidate pairs within each frame are sorted by increasing distance.
    The shortest currently unused pair is accepted first. This preserves
    the method used for the reported thesis values. It is not equivalent
    to a globally optimal Hungarian assignment.
    """
    if threshold <= 0:
        raise ValueError("threshold must be positive")

    refs_by_frame: dict[int, list[ReferenceSpot]] = defaultdict(list)
    dets_by_frame: dict[int, list[Detection]] = defaultdict(list)

    for spot in reference_spots:
        refs_by_frame[spot.frame].append(spot)
    for detection in detections.values():
        dets_by_frame[detection.frame].append(detection)

    matches: list[SpotMatch] = []
    unmatched: list[ReferenceSpot] = []

    for frame, refs in sorted(refs_by_frame.items()):
        candidates = dets_by_frame.get(frame, [])
        pairs: list[tuple[float, ReferenceSpot, Detection]] = []

        for ref in refs:
            for detection in candidates:
                distance = euclidean_distance(ref, detection)
                if distance <= threshold:
                    pairs.append((distance, ref, detection))

        pairs.sort(key=lambda item: item[0])
        used_ref: set[int] = set()
        used_detection: set[int] = set()

        for distance, ref, detection in pairs:
            if ref.spot_id in used_ref or detection.detection_id in used_detection:
                continue
            matches.append(
                SpotMatch(
                    spot_id=ref.spot_id,
                    detection_id=detection.detection_id,
                    frame=frame,
                    distance=distance,
                )
            )
            used_ref.add(ref.spot_id)
            used_detection.add(detection.detection_id)

        unmatched.extend(ref for ref in refs if ref.spot_id not in used_ref)

    return matches, unmatched


def evaluate_adjacent_links(
    links: Iterable[tuple[int, int]],
    reference_spots: Mapping[int, ReferenceSpot],
    matches: Iterable[SpotMatch],
    detections: Mapping[int, Detection],
) -> dict[str, int | float]:
    match_by_spot = {match.spot_id: match for match in matches}

    evaluated = 0
    both_endpoints_matched = 0
    recovered = 0

    for source_spot_id, target_spot_id in links:
        source = reference_spots.get(source_spot_id)
        target = reference_spots.get(target_spot_id)
        if source is None or target is None:
            continue
        if target.frame - source.frame != 1:
            continue

        evaluated += 1
        source_match = match_by_spot.get(source_spot_id)
        target_match = match_by_spot.get(target_spot_id)
        if source_match is None or target_match is None:
            continue

        both_endpoints_matched += 1
        target_detection = detections[target_match.detection_id]
        if source_match.detection_id in target_detection.parents:
            recovered += 1

    return {
        "evaluated_links": evaluated,
        "both_endpoints_matched": both_endpoints_matched,
        "recovered_links": recovered,
        "overall_recovery": recovered / evaluated if evaluated else math.nan,
        "conditional_recovery": (
            recovered / both_endpoints_matched
            if both_endpoints_matched
            else math.nan
        ),
    }
