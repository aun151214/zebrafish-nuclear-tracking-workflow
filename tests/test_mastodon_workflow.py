from pathlib import Path

from zebrafish_tracking.io.mastodon_csv import MastodonLink, MastodonSpot
from zebrafish_tracking.io.tracking_csv import Detection
from zebrafish_tracking.validation.mastodon_workflow import run_mastodon_validation


def test_end_to_end_mastodon_summary(tmp_path: Path):
    spots = [
        MastodonSpot(1, 1, 0, 0, 0, 1, 0, 0, 0, 0),
        MastodonSpot(2, 2, 1, 0, 0, 1, 1, 1, 0, 0),
    ]
    links = [MastodonLink(1, 2)]
    detections = {
        10: Detection(10, 1, 0, 0, 0, ()),
        11: Detection(11, 2, 1, 0, 0, (10,)),
    }
    summary = run_mastodon_validation(
        dataset_name="synthetic",
        spots=spots,
        links=links,
        detections=detections,
        thresholds=[0.1],
        output_dir=tmp_path,
    )[0]
    assert summary["matched_manual_spots"] == 2
    assert summary["recovered_adjacent_links"] == 1
    assert summary["conditional_link_recovery"] == 1
    assert (tmp_path / "validation_summary.csv").exists()
