from zebrafish_tracking.io.tracking_csv import Detection
from zebrafish_tracking.validation.matching import (
    ReferenceSpot,
    evaluate_adjacent_links,
    greedy_one_to_one_matches,
)


def test_greedy_matching_and_link_recovery():
    detections = {
        101: Detection(101, 1, 0.0, 0.0, 0.0, ()),
        102: Detection(102, 2, 0.2, 0.0, 0.0, (101,)),
        103: Detection(103, 1, 5.0, 0.0, 0.0, ()),
    }
    spots = [
        ReferenceSpot(1, 1, 0.1, 0.0, 0.0),
        ReferenceSpot(2, 2, 0.3, 0.0, 0.0),
    ]
    matches, unmatched = greedy_one_to_one_matches(
        spots, detections, threshold=1.0
    )
    assert len(matches) == 2
    assert unmatched == []

    metrics = evaluate_adjacent_links(
        [(1, 2)],
        {spot.spot_id: spot for spot in spots},
        matches,
        detections,
    )
    assert metrics["evaluated_links"] == 1
    assert metrics["recovered_links"] == 1
    assert metrics["conditional_recovery"] == 1.0
