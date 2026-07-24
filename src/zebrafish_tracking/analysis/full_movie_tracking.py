from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean, median
from typing import Mapping

from zebrafish_tracking.analysis.tracklets import Tracklet, reconstruct_one_to_one_tracklets
from zebrafish_tracking.io.tracking_csv import Detection


@dataclass(frozen=True)
class ParentLink:
    parent_id: int
    child_id: int
    parent_frame: int
    child_frame: int

    @property
    def frame_gap(self) -> int:
        return self.child_frame - self.parent_frame


def reconstruct_parent_links(
    detections: Mapping[int, Detection],
) -> list[ParentLink]:
    """Return every valid parent-child reference in the tracking table.

    A row with multiple valid parent IDs contributes one link per parent.
    Unknown parent IDs raise an error because they indicate an incomplete
    or inconsistent tracking table.
    """
    links: list[ParentLink] = []

    for child in detections.values():
        for parent_id in child.parents:
            if parent_id not in detections:
                raise ValueError(
                    f"Detection {child.detection_id} references unknown "
                    f"parent ID {parent_id}."
                )

            parent = detections[parent_id]
            gap = child.frame - parent.frame
            if gap <= 0:
                raise ValueError(
                    f"Non-positive parent-child frame gap: "
                    f"parent={parent_id} frame={parent.frame}, "
                    f"child={child.detection_id} frame={child.frame}."
                )

            links.append(
                ParentLink(
                    parent_id=parent_id,
                    child_id=child.detection_id,
                    parent_frame=parent.frame,
                    child_frame=child.frame,
                )
            )

    return sorted(
        links,
        key=lambda link: (
            link.child_frame,
            link.child_id,
            link.parent_id,
        ),
    )


def detection_counts_by_frame(
    detections: Mapping[int, Detection],
    *,
    frame_min: int | None = None,
    frame_max: int | None = None,
) -> list[dict[str, int]]:
    if not detections:
        return []

    if frame_min is None:
        frame_min = min(detection.frame for detection in detections.values())
    if frame_max is None:
        frame_max = max(detection.frame for detection in detections.values())

    counts = Counter(detection.frame for detection in detections.values())
    return [
        {
            "frame": frame,
            "detections": int(counts.get(frame, 0)),
        }
        for frame in range(frame_min, frame_max + 1)
    ]


def parent_link_gap_counts(
    links: list[ParentLink],
) -> list[dict[str, float | int]]:
    counts = Counter(link.frame_gap for link in links)
    total = len(links)

    return [
        {
            "frame_gap": int(gap),
            "links": int(count),
            "fraction": count / total if total else 0.0,
            "percent": 100.0 * count / total if total else 0.0,
        }
        for gap, count in sorted(counts.items())
    ]


def tracklet_rows(
    tracklets: list[Tracklet],
    *,
    frame_min: int,
    frame_max: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for tracklet in tracklets:
        rows.append(
            {
                "tracklet_id": tracklet.tracklet_id,
                "start_detection_id": tracklet.detection_ids[0],
                "end_detection_id": tracklet.detection_ids[-1],
                "start_frame": tracklet.frames[0],
                "end_frame": tracklet.frames[-1],
                "length_frames": tracklet.length,
                "is_consecutive": int(tracklet.is_consecutive),
                "covers_full_window": int(
                    tracklet.is_consecutive
                    and tracklet.frames[0] == frame_min
                    and tracklet.frames[-1] == frame_max
                    and tracklet.length == frame_max - frame_min + 1
                ),
                "start_reason": tracklet.start_reason,
            }
        )

    return rows


def tracklet_length_counts(
    tracklets: list[Tracklet],
) -> list[dict[str, float | int]]:
    counts = Counter(tracklet.length for tracklet in tracklets)
    total = len(tracklets)

    return [
        {
            "length_frames": int(length),
            "tracklets": int(count),
            "fraction": count / total if total else 0.0,
            "percent": 100.0 * count / total if total else 0.0,
        }
        for length, count in sorted(counts.items())
    ]


def tracklet_survival(
    tracklets: list[Tracklet],
    *,
    maximum_length: int,
) -> list[dict[str, float | int]]:
    total = len(tracklets)
    lengths = [tracklet.length for tracklet in tracklets]

    return [
        {
            "minimum_length_frames": threshold,
            "tracklets_at_least_this_long": int(
                sum(length >= threshold for length in lengths)
            ),
            "fraction": (
                sum(length >= threshold for length in lengths) / total
                if total else 0.0
            ),
            "percent": (
                100.0 * sum(length >= threshold for length in lengths) / total
                if total else 0.0
            ),
        }
        for threshold in range(1, maximum_length + 1)
    ]


def summarize_full_movie_tracking(
    detections: Mapping[int, Detection],
    *,
    frame_min: int | None = None,
    frame_max: int | None = None,
) -> tuple[
    dict[str, float | int],
    list[dict[str, int]],
    list[ParentLink],
    list[Tracklet],
]:
    if not detections:
        raise ValueError("No detections supplied.")

    if frame_min is None:
        frame_min = min(detection.frame for detection in detections.values())
    if frame_max is None:
        frame_max = max(detection.frame for detection in detections.values())

    frame_counts = detection_counts_by_frame(
        detections,
        frame_min=frame_min,
        frame_max=frame_max,
    )
    links = reconstruct_parent_links(detections)
    tracklets = reconstruct_one_to_one_tracklets(detections)

    detection_values = [row["detections"] for row in frame_counts]
    tracklet_lengths = [tracklet.length for tracklet in tracklets]
    gap_counts = Counter(link.frame_gap for link in links)

    children: dict[int, list[int]] = defaultdict(list)
    for link in links:
        children[link.parent_id].append(link.child_id)

    outdegree_mismatches = 0
    for detection in detections.values():
        if detection.outgoing_links is None:
            continue
        if detection.outgoing_links != len(children.get(detection.detection_id, [])):
            outdegree_mismatches += 1

    full_window_length = frame_max - frame_min + 1
    full_window_tracklets = sum(
        tracklet.is_consecutive
        and tracklet.frames[0] == frame_min
        and tracklet.frames[-1] == frame_max
        and tracklet.length == full_window_length
        for tracklet in tracklets
    )

    summary: dict[str, float | int] = {
        "frames": full_window_length,
        "frame_min": frame_min,
        "frame_max": frame_max,
        "total_detections": len(detections),
        "mean_detections_per_frame": mean(detection_values),
        "median_detections_per_frame": median(detection_values),
        "minimum_detections_per_frame": min(detection_values),
        "maximum_detections_per_frame": max(detection_values),
        "parent_child_links": len(links),
        "adjacent_frame_links": gap_counts.get(1, 0),
        "adjacent_frame_links_percent": (
            100.0 * gap_counts.get(1, 0) / len(links) if links else 0.0
        ),
        "two_frame_gap_links": gap_counts.get(2, 0),
        "three_frame_gap_links": gap_counts.get(3, 0),
        "root_detections": sum(not detection.parents for detection in detections.values()),
        "reconstructed_branching_parents": sum(
            len(child_ids) > 1 for child_ids in children.values()
        ),
        "outdegree_qc_mismatches": outdegree_mismatches,
        "continuous_tracklets": len(tracklets),
        "mean_tracklet_length_frames": mean(tracklet_lengths),
        "median_tracklet_length_frames": median(tracklet_lengths),
        "minimum_tracklet_length_frames": min(tracklet_lengths),
        "maximum_tracklet_length_frames": max(tracklet_lengths),
        "single_frame_tracklets": sum(length == 1 for length in tracklet_lengths),
        "tracklets_at_least_5_frames": sum(
            length >= 5 for length in tracklet_lengths
        ),
        "tracklets_at_least_10_frames": sum(
            length >= 10 for length in tracklet_lengths
        ),
        "tracklets_at_least_10_frames_percent": (
            100.0
            * sum(length >= 10 for length in tracklet_lengths)
            / len(tracklets)
        ),
        "tracklets_at_least_25_frames": sum(
            length >= 25 for length in tracklet_lengths
        ),
        "tracklets_at_least_50_frames": sum(
            length >= 50 for length in tracklet_lengths
        ),
        "tracklets_covering_full_window": int(full_window_tracklets),
    }

    return summary, frame_counts, links, tracklets
