from zebrafish_tracking.io.mastodon_csv import MastodonSpot
from zebrafish_tracking.io.tracking_csv import Detection
from zebrafish_tracking.validation.component_continuity import analyse_track_components


def spot(spot_id, frame, track):
    return MastodonSpot(
        spot_id=spot_id,
        frame=frame + 1,
        x=0.0,
        y=0.0,
        z=0.0,
        track_id=track,
        mastodon_frame=frame,
    )


def test_component_statuses_and_longest_segment():
    spots = [spot(1, 0, 10), spot(2, 1, 10), spot(3, 2, 10), spot(4, 0, 20)]
    matches = [
        {"mastodon_spot_id": 1, "itec_id": 101, "distance_itec_units": 1.0},
        {"mastodon_spot_id": 2, "itec_id": 102, "distance_itec_units": 1.0},
        {"mastodon_spot_id": 3, "itec_id": 103, "distance_itec_units": 1.0},
    ]
    links = [
        {
            "source_mastodon_spot_id": 1,
            "target_mastodon_spot_id": 2,
            "source_itec_id": 101,
            "target_itec_id": 102,
            "recovered_link": 1,
            "status": "recovered",
        },
        {
            "source_mastodon_spot_id": 2,
            "target_mastodon_spot_id": 3,
            "source_itec_id": 102,
            "target_itec_id": 103,
            "recovered_link": 0,
            "status": "spots_matched_but_link_not_recovered",
        },
    ]
    detections = {
        101: Detection(101, 1, 0, 0, 0, ()),
        102: Detection(102, 2, 0, 0, 0, (101,)),
        103: Detection(103, 3, 0, 0, 0, ()),
    }
    rows, _, aggregate = analyse_track_components(
        spots=spots,
        match_rows=matches,
        link_rows=links,
        detections=detections,
        cross_track_mode="exclude",
    )
    by_id = {row["mastodon_track_id"]: row for row in rows}
    assert by_id[10]["status"] == "all spots matched but link break present"
    assert by_id[10]["longest_recovered_segment_spots"] == 2
    assert by_id[10]["distinct_itec_tracklets_assigned"] == 2
    assert by_id[20]["status"] == "not recovered"
    assert aggregate["components"] == 2
