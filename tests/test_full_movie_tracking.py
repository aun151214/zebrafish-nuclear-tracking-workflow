from zebrafish_tracking.analysis.full_movie_tracking import (
    parent_link_gap_counts,
    reconstruct_parent_links,
    summarize_full_movie_tracking,
)
from zebrafish_tracking.io.tracking_csv import Detection


def synthetic_detections():
    return {
        1: Detection(1, 1, 0, 0, 0, (), outgoing_links=1),
        2: Detection(2, 2, 0, 0, 0, (1,), outgoing_links=2),
        3: Detection(3, 3, 0, 0, 0, (2,), outgoing_links=0),
        4: Detection(4, 3, 1, 0, 0, (2,), outgoing_links=0),
        5: Detection(5, 4, 2, 0, 0, (), outgoing_links=1),
        6: Detection(6, 6, 2, 0, 0, (5,), outgoing_links=0),
    }


def test_parent_link_gap_counts():
    links = reconstruct_parent_links(synthetic_detections())
    rows = parent_link_gap_counts(links)
    assert [(row["frame_gap"], row["links"]) for row in rows] == [
        (1, 3),
        (2, 1),
    ]


def test_full_movie_summary_and_tracklets():
    summary, frame_counts, links, tracklets = summarize_full_movie_tracking(
        synthetic_detections(),
        frame_min=1,
        frame_max=6,
    )

    assert summary["frames"] == 6
    assert summary["total_detections"] == 6
    assert summary["parent_child_links"] == 4
    assert summary["adjacent_frame_links"] == 3
    assert summary["two_frame_gap_links"] == 1
    assert summary["continuous_tracklets"] == 5
    assert summary["maximum_tracklet_length_frames"] == 2
    assert [row["detections"] for row in frame_counts] == [1, 1, 2, 1, 0, 1]
    assert len(links) == 4
    assert sorted(tracklet.length for tracklet in tracklets) == [1, 1, 1, 1, 2]
