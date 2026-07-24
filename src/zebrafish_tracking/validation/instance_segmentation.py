from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import tifffile
from scipy.io import loadmat


@dataclass(frozen=True)
class FrameSegmentationResult:
    run: str
    frame: int
    loaded_key: str
    orientation_overlap_score: int
    n_pred: int
    n_gt: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    mean_matched_iou: float

    def as_dict(self) -> dict[str, object]:
        return {
            "run": self.run,
            "frame": self.frame,
            "loaded_key": self.loaded_key,
            "orientation_overlap_score": self.orientation_overlap_score,
            "n_pred": self.n_pred,
            "n_gt": self.n_gt,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "mean_matched_iou": self.mean_matched_iou,
        }


def load_mat_label(path: str | Path) -> tuple[np.ndarray, str]:
    """Load a 3D label array from a MATLAB v5/v7 or v7.3 file.

    Candidate selection intentionally reproduces the thesis validation script:
    preferred names are refine_res, threshold_res, res and label; otherwise the
    largest 3D array is selected.
    """
    label_path = Path(path)
    if not label_path.is_file():
        raise FileNotFoundError(label_path)

    candidates: list[tuple[str, np.ndarray]] = []

    try:
        data = loadmat(label_path)
        for key, value in data.items():
            if key.startswith("__"):
                continue
            array = np.asarray(value)
            if array.ndim == 3 and array.size > 1000:
                candidates.append((key, array))
    except Exception:
        # MATLAB v7.3 files are HDF5 and are handled below.
        pass

    if not candidates:
        try:
            with h5py.File(label_path, "r") as handle:
                def visit(name: str, obj: object) -> None:
                    if not hasattr(obj, "shape"):
                        return
                    try:
                        array = np.asarray(obj)
                    except Exception:
                        return
                    if array.ndim == 3 and array.size > 1000:
                        candidates.append((name, array))

                handle.visititems(visit)
        except Exception as error:
            raise RuntimeError(
                f"Could not load 3D label data from {label_path}: {error}"
            ) from error

    if not candidates:
        raise RuntimeError(f"No 3D label array found in {label_path}")

    for preferred_name in ("refine_res", "threshold_res", "res", "label"):
        for name, array in candidates:
            if preferred_name.lower() in name.lower():
                return array, name

    candidates.sort(key=lambda item: item[1].size, reverse=True)
    return candidates[0][1], candidates[0][0]


def prepare_ground_truth_frame(
    mask_tzyx: np.ndarray,
    frame_index_1based: int,
) -> np.ndarray:
    ground_truth = np.asarray(mask_tzyx[frame_index_1based - 1])
    ground_truth = np.squeeze(ground_truth)

    if ground_truth.ndim != 3:
        raise RuntimeError(
            f"Expected a 3D ground-truth frame, got {ground_truth.shape}"
        )

    return ground_truth.astype(np.int64, copy=False)


def orient_prediction_to_ground_truth(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Orient a prediction to the ground-truth array.

    This preserves the exact candidate order and foreground-overlap criterion
    used by the thesis script so the historical results remain reproducible.
    """
    prediction = np.squeeze(prediction)

    if prediction.ndim != 3:
        raise RuntimeError(
            "Prediction is not 3D after squeeze: "
            f"shape={prediction.shape}"
        )

    target_shape = ground_truth.shape
    candidates: list[np.ndarray] = []

    for permutation in itertools.permutations(range(3)):
        candidate = np.transpose(prediction, permutation)
        if candidate.shape == target_shape:
            candidates.append(candidate)

    expanded: list[np.ndarray] = []
    for candidate in candidates:
        expanded.append(candidate)
        expanded.append(candidate[:, :, ::-1])
        expanded.append(candidate[:, ::-1, :])
        expanded.append(np.swapaxes(candidate, 1, 2))
    candidates = expanded

    if not candidates:
        raise RuntimeError(
            f"Cannot orient prediction shape {prediction.shape} "
            f"to ground-truth shape {target_shape}"
        )

    ground_truth_foreground = ground_truth > 0
    best: np.ndarray | None = None
    best_score = -1

    for candidate in candidates:
        if candidate.shape != target_shape:
            continue
        score = int(
            np.logical_and(
                candidate > 0,
                ground_truth_foreground,
            ).sum()
        )
        if score > best_score:
            best_score = score
            best = candidate

    if best is None:
        raise RuntimeError(
            f"No valid orientation found for prediction shape {prediction.shape}"
        )

    return best.astype(np.int64, copy=False), best_score


def compute_object_metrics(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    *,
    iou_threshold: float = 0.10,
) -> dict[str, float | int]:
    """Compute one-to-one object metrics using greedy descending IoU.

    Candidate predicted/ground-truth pairs are retained when IoU is greater
    than or equal to ``iou_threshold``. Pairs are sorted by descending IoU and
    accepted greedily while enforcing one predicted object and one
    ground-truth object per match. This is the thesis replication mode.
    """
    prediction = prediction.astype(np.int64, copy=False)
    ground_truth = ground_truth.astype(np.int64, copy=False)

    predicted_ids = np.unique(prediction)
    predicted_ids = predicted_ids[predicted_ids != 0]

    ground_truth_ids = np.unique(ground_truth)
    ground_truth_ids = ground_truth_ids[ground_truth_ids != 0]

    n_pred = len(predicted_ids)
    n_gt = len(ground_truth_ids)

    if n_pred == 0:
        return {
            "n_pred": 0,
            "n_gt": n_gt,
            "tp": 0,
            "fp": 0,
            "fn": n_gt,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "mean_matched_iou": 0.0,
        }

    predicted_sizes = np.bincount(
        prediction.ravel(),
        minlength=int(prediction.max()) + 1,
    )
    ground_truth_sizes = np.bincount(
        ground_truth.ravel(),
        minlength=int(ground_truth.max()) + 1,
    )

    overlap = (prediction > 0) & (ground_truth > 0)
    predicted_overlap = prediction[overlap].ravel()
    ground_truth_overlap = ground_truth[overlap].ravel()

    candidate_pairs: dict[tuple[int, int], float] = {}

    if len(predicted_overlap) > 0:
        pairs = np.stack(
            [predicted_overlap, ground_truth_overlap],
            axis=1,
        )
        unique_pairs, intersections = np.unique(
            pairs,
            axis=0,
            return_counts=True,
        )

        for (predicted_id, ground_truth_id), intersection in zip(
            unique_pairs,
            intersections,
        ):
            predicted_id = int(predicted_id)
            ground_truth_id = int(ground_truth_id)
            union = int(
                predicted_sizes[predicted_id]
                + ground_truth_sizes[ground_truth_id]
                - intersection
            )

            if union <= 0:
                continue

            iou = float(intersection) / float(union)
            if iou >= iou_threshold:
                candidate_pairs[(predicted_id, ground_truth_id)] = iou

    sorted_pairs = sorted(
        candidate_pairs.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    used_predicted: set[int] = set()
    used_ground_truth: set[int] = set()
    matched_ious: list[float] = []

    for (predicted_id, ground_truth_id), iou in sorted_pairs:
        if (
            predicted_id in used_predicted
            or ground_truth_id in used_ground_truth
        ):
            continue
        used_predicted.add(predicted_id)
        used_ground_truth.add(ground_truth_id)
        matched_ious.append(iou)

    tp = len(matched_ious)
    fp = n_pred - tp
    fn = n_gt - tp

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "n_pred": n_pred,
        "n_gt": n_gt,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_matched_iou": (
            float(np.mean(matched_ious))
            if matched_ious
            else 0.0
        ),
    }


def summarize_frame_results(
    run_name: str,
    frame_results: Iterable[FrameSegmentationResult],
    *,
    iou_threshold: float,
) -> dict[str, float | int | str]:
    rows = list(frame_results)
    if not rows:
        raise ValueError("No frame results supplied.")

    return {
        "run": run_name,
        "frames_evaluated": len(rows),
        "iou_threshold": iou_threshold,
        "mean_n_pred": float(np.mean([row.n_pred for row in rows])),
        "mean_n_gt": float(np.mean([row.n_gt for row in rows])),
        "total_tp": int(sum(row.tp for row in rows)),
        "total_fp": int(sum(row.fp for row in rows)),
        "total_fn": int(sum(row.fn for row in rows)),
        "mean_precision": float(
            np.mean([row.precision for row in rows])
        ),
        "mean_recall": float(
            np.mean([row.recall for row in rows])
        ),
        "mean_f1": float(
            np.mean([row.f1 for row in rows])
        ),
        "mean_matched_iou": float(
            np.mean([row.mean_matched_iou for row in rows])
        ),
    }


def validate_instance_segmentation(
    *,
    run_name: str,
    ground_truth_mask_path: str | Path,
    prediction_dir: str | Path,
    frames: Iterable[int],
    prediction_pattern: str = "t{frame:04d}_Channel 2.mat",
    iou_threshold: float = 0.10,
) -> tuple[
    list[FrameSegmentationResult],
    dict[str, float | int | str],
]:
    ground_truth_path = Path(ground_truth_mask_path)
    prediction_root = Path(prediction_dir)

    if not ground_truth_path.is_file():
        raise FileNotFoundError(ground_truth_path)
    if not prediction_root.is_dir():
        raise NotADirectoryError(prediction_root)

    mask = tifffile.memmap(str(ground_truth_path), mode="r")
    results: list[FrameSegmentationResult] = []

    try:
        for frame in frames:
            prediction_path = prediction_root / prediction_pattern.format(
                frame=frame
            )
            if not prediction_path.is_file():
                raise FileNotFoundError(prediction_path)

            ground_truth = prepare_ground_truth_frame(mask, frame)
            raw_prediction, loaded_key = load_mat_label(prediction_path)
            prediction, orientation_score = (
                orient_prediction_to_ground_truth(
                    raw_prediction,
                    ground_truth,
                )
            )
            metrics = compute_object_metrics(
                prediction,
                ground_truth,
                iou_threshold=iou_threshold,
            )

            results.append(
                FrameSegmentationResult(
                    run=run_name,
                    frame=frame,
                    loaded_key=loaded_key,
                    orientation_overlap_score=orientation_score,
                    n_pred=int(metrics["n_pred"]),
                    n_gt=int(metrics["n_gt"]),
                    tp=int(metrics["tp"]),
                    fp=int(metrics["fp"]),
                    fn=int(metrics["fn"]),
                    precision=float(metrics["precision"]),
                    recall=float(metrics["recall"]),
                    f1=float(metrics["f1"]),
                    mean_matched_iou=float(
                        metrics["mean_matched_iou"]
                    ),
                )
            )
    finally:
        del mask

    summary = summarize_frame_results(
        run_name,
        results,
        iou_threshold=iou_threshold,
    )
    return results, summary
