import numpy as np

from zebrafish_tracking.validation.instance_segmentation import (
    FrameSegmentationResult,
    compute_object_metrics,
    orient_prediction_to_ground_truth,
    summarize_frame_results,
)


def test_perfect_object_match():
    ground_truth = np.zeros((3, 4, 5), dtype=np.int64)
    ground_truth[0, 0:2, 0:2] = 1
    ground_truth[2, 2:4, 3:5] = 2

    metrics = compute_object_metrics(
        ground_truth.copy(),
        ground_truth,
        iou_threshold=0.10,
    )

    assert metrics["n_pred"] == 2
    assert metrics["n_gt"] == 2
    assert metrics["tp"] == 2
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["mean_matched_iou"] == 1.0


def test_orientation_restores_transposed_prediction():
    ground_truth = np.zeros((2, 3, 4), dtype=np.int64)
    ground_truth[0, 1, 2] = 1
    ground_truth[1, 2, 3] = 2

    prediction = np.transpose(ground_truth, (2, 0, 1))
    oriented, score = orient_prediction_to_ground_truth(
        prediction,
        ground_truth,
    )

    assert np.array_equal(oriented, ground_truth)
    assert score == 2


def test_summary_uses_framewise_means_and_total_counts():
    rows = [
        FrameSegmentationResult(
            run="test",
            frame=1,
            loaded_key="labels",
            orientation_overlap_score=10,
            n_pred=3,
            n_gt=2,
            tp=2,
            fp=1,
            fn=0,
            precision=2 / 3,
            recall=1.0,
            f1=0.8,
            mean_matched_iou=0.6,
        ),
        FrameSegmentationResult(
            run="test",
            frame=2,
            loaded_key="labels",
            orientation_overlap_score=8,
            n_pred=1,
            n_gt=2,
            tp=1,
            fp=0,
            fn=1,
            precision=1.0,
            recall=0.5,
            f1=2 / 3,
            mean_matched_iou=0.4,
        ),
    ]

    summary = summarize_frame_results(
        "test",
        rows,
        iou_threshold=0.10,
    )

    assert summary["frames_evaluated"] == 2
    assert summary["mean_n_pred"] == 2.0
    assert summary["mean_n_gt"] == 2.0
    assert summary["total_tp"] == 3
    assert summary["total_fp"] == 1
    assert summary["total_fn"] == 1
    assert summary["mean_precision"] == (2 / 3 + 1.0) / 2
    assert summary["mean_recall"] == 0.75
    assert summary["mean_f1"] == (0.8 + 2 / 3) / 2
    assert summary["mean_matched_iou"] == 0.5
