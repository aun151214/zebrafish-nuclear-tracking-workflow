from zebrafish_tracking.analysis.tracklets import reconstruct_one_to_one_tracklets
from zebrafish_tracking.io.tracking_csv import Detection


def test_tracklet_stops_at_division():
    detections = {
        1: Detection(1, 1, 0, 0, 0, ()),
        2: Detection(2, 2, 0, 0, 0, (1,)),
        3: Detection(3, 3, 0, 0, 0, (2,)),
        4: Detection(4, 3, 1, 0, 0, (2,)),
    }
    tracklets = reconstruct_one_to_one_tracklets(detections)
    lengths = sorted(tracklet.length for tracklet in tracklets)
    assert lengths == [1, 1, 2]
