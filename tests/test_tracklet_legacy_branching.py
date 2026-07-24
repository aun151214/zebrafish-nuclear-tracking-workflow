from zebrafish_tracking.analysis.tracklets import (
    reconstruct_one_to_one_tracklets,
)
from zebrafish_tracking.io.tracking_csv import Detection


def test_parent_with_adjacent_and_gap_child_splits_all_children():
    """Reproduce the canonical thesis branching rule.

    Detection 1 has:
    - one adjacent child at Frame 2; and
    - one non-adjacent child at Frame 3.

    The canonical full-movie script counts both reconstructed children when
    deciding whether Detection 1 branches. Therefore Detection 2 must not
    inherit Detection 1's tracklet.
    """
    detections = {
        1: Detection(
            detection_id=1,
            frame=1,
            x=0.0,
            y=0.0,
            z=0.0,
            parents=(),
            outgoing_links=2,
        ),
        2: Detection(
            detection_id=2,
            frame=2,
            x=0.0,
            y=0.0,
            z=0.0,
            parents=(1,),
            outgoing_links=0,
        ),
        3: Detection(
            detection_id=3,
            frame=3,
            x=0.0,
            y=0.0,
            z=0.0,
            parents=(1,),
            outgoing_links=0,
        ),
    }

    tracklets = reconstruct_one_to_one_tracklets(detections)

    assert len(tracklets) == 3
    assert sorted(
        tracklet.detection_ids
        for tracklet in tracklets
    ) == [(1,), (2,), (3,)]
