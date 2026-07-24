from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping

from zebrafish_tracking.io.tracking_csv import Detection


@dataclass(frozen=True)
class Tracklet:
    tracklet_id: int
    detection_ids: tuple[int, ...]
    frames: tuple[int, ...]
    start_reason: str

    @property
    def length(self) -> int:
        return len(self.detection_ids)

    @property
    def is_consecutive(self) -> bool:
        return all(
            later == earlier + 1
            for earlier, later in zip(self.frames, self.frames[1:])
        )


def reconstruct_one_to_one_tracklets(
    detections: Mapping[int, Detection],
) -> list[Tracklet]:
    """Reconstruct the thesis continuous one-to-one tracklets.

    A detection inherits its parent's tracklet only when:

    1. it has exactly one valid parent in the immediately preceding frame; and
    2. that parent has exactly one reconstructed child in the complete graph.

    The second condition intentionally counts every child of the parent,
    including non-adjacent children. This reproduces the canonical thesis
    implementation: a parent with one adjacent child plus an additional
    gap-linked child is treated as branching and terminates the tracklet.

    Roots, temporal gaps, merges, divisions and ambiguous relationships start
    new tracklets.
    """
    if not detections:
        return []

    children: dict[int, list[int]] = defaultdict(list)
    for detection in detections.values():
        for parent_id in detection.parents:
            if parent_id in detections:
                children[parent_id].append(detection.detection_id)

    for child_ids in children.values():
        child_ids.sort(
            key=lambda child_id: (
                detections[child_id].frame,
                child_id,
            )
        )

    ordered = sorted(
        detections.values(),
        key=lambda detection: (
            detection.frame,
            detection.detection_id,
        ),
    )

    track_of: dict[int, int] = {}
    start_reason: dict[int, str] = {}
    next_tracklet = 1

    for detection in ordered:
        valid_parents = [
            parent_id
            for parent_id in detection.parents
            if parent_id in detections
            and detections[parent_id].frame == detection.frame - 1
        ]

        inherited = False
        reason = "missing_parent_or_redetection"

        if len(valid_parents) == 1:
            parent_id = valid_parents[0]

            # Important thesis-replication rule:
            # count all reconstructed children of the parent, not only children
            # in the current adjacent frame.
            reconstructed_children = [
                child_id
                for child_id in children.get(parent_id, [])
                if child_id in detections
            ]

            if (
                len(reconstructed_children) == 1
                and parent_id in track_of
            ):
                track_of[detection.detection_id] = track_of[parent_id]
                inherited = True
            elif len(reconstructed_children) > 1:
                reason = "division_or_branch"
            elif parent_id not in track_of:
                reason = "unresolved_parent"
            else:
                reason = "ambiguous_child_relation"

        elif len(valid_parents) > 1:
            reason = "merge_or_multiple_parents"
        elif detection.parents:
            reason = "invalid_or_nonconsecutive_parent"
        elif detection.frame == ordered[0].frame:
            reason = "first_frame_root"

        if not inherited:
            track_of[detection.detection_id] = next_tracklet
            start_reason[next_tracklet] = reason
            next_tracklet += 1

    nodes_by_track: dict[int, list[Detection]] = defaultdict(list)
    for detection in ordered:
        nodes_by_track[track_of[detection.detection_id]].append(detection)

    return [
        Tracklet(
            tracklet_id=tracklet_id,
            detection_ids=tuple(
                node.detection_id
                for node in nodes
            ),
            frames=tuple(
                node.frame
                for node in nodes
            ),
            start_reason=start_reason.get(
                tracklet_id,
                "unknown",
            ),
        )
        for tracklet_id, nodes in sorted(nodes_by_track.items())
    ]
