from __future__ import annotations

import csv
import math
import statistics
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from zebrafish_tracking.io.mastodon_csv import MastodonLink, MastodonSpot
from zebrafish_tracking.io.tracking_csv import Detection
from zebrafish_tracking.validation.matching import SpotMatch, greedy_one_to_one_matches


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def _threshold_tag(threshold: float) -> str:
    return str(float(threshold)).replace(".", "p")


def _legacy_median(values: list[float]) -> float:
    """Preserve the upper-middle convention used in the legacy matching script."""
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def evaluate_links_detailed(
    links: Iterable[MastodonLink],
    spots_by_id: dict[int, MastodonSpot],
    matches: Iterable[SpotMatch],
    detections: dict[int, Detection],
) -> tuple[dict[str, int | float], list[dict]]:
    match_by_spot = {match.spot_id: match for match in matches}
    evaluated = 0
    both_matched = 0
    recovered = 0
    rows: list[dict] = []

    for link in links:
        source_spot = spots_by_id.get(link.source_spot_id)
        target_spot = spots_by_id.get(link.target_spot_id)
        if source_spot is None or target_spot is None:
            continue
        if target_spot.frame - source_spot.frame != 1:
            continue

        evaluated += 1
        source_match = match_by_spot.get(link.source_spot_id)
        target_match = match_by_spot.get(link.target_spot_id)
        status = "not_both_spots_matched"
        source_detection_id: int | str = ""
        target_detection_id: int | str = ""
        target_parents = ""
        recovered_link = 0

        if source_match is not None:
            source_detection_id = source_match.detection_id
        if target_match is not None:
            target_detection_id = target_match.detection_id

        if source_match is not None and target_match is not None:
            both_matched += 1
            target_detection = detections[target_match.detection_id]
            target_parents = ";".join(str(value) for value in target_detection.parents)
            if source_match.detection_id in target_detection.parents:
                recovered += 1
                recovered_link = 1
                status = "recovered"
            else:
                status = "spots_matched_but_link_not_recovered"

        rows.append(
            {
                "source_mastodon_spot_id": link.source_spot_id,
                "target_mastodon_spot_id": link.target_spot_id,
                "source_mastodon_frame": source_spot.mastodon_frame,
                "target_mastodon_frame": target_spot.mastodon_frame,
                "source_itec_frame": source_spot.frame,
                "target_itec_frame": target_spot.frame,
                "source_itec_id": source_detection_id,
                "target_itec_id": target_detection_id,
                "target_itec_parents": target_parents,
                "delta_t": "" if link.delta_t is None else link.delta_t,
                "mastodon_link_displacement_um": (
                    "" if link.displacement_um is None else link.displacement_um
                ),
                "recovered_link": recovered_link,
                "status": status,
            }
        )

    metrics: dict[str, int | float] = {
        "evaluated_adjacent_links": evaluated,
        "links_with_both_endpoints_matched": both_matched,
        "recovered_adjacent_links": recovered,
        "overall_link_recovery": recovered / evaluated if evaluated else math.nan,
        "conditional_link_recovery": (
            recovered / both_matched if both_matched else math.nan
        ),
    }
    return metrics, rows


def run_mastodon_validation(
    *,
    dataset_name: str,
    spots: list[MastodonSpot],
    links: list[MastodonLink],
    detections: dict[int, Detection],
    thresholds: list[float],
    output_dir: str | Path,
) -> list[dict]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    spots_by_id = {spot.spot_id: spot for spot in spots}
    summaries: list[dict] = []

    for threshold in thresholds:
        matches, unmatched = greedy_one_to_one_matches(
            spots,
            detections,
            threshold=threshold,
        )
        link_metrics, link_rows = evaluate_links_detailed(
            links,
            spots_by_id,
            matches,
            detections,
        )
        distances = [match.distance for match in matches]

        summary = {
            "dataset": dataset_name,
            "threshold_itec_units": float(threshold),
            "manual_spots_evaluated": len(spots),
            "matched_manual_spots": len(matches),
            "unmatched_manual_spots": len(unmatched),
            "spot_recovery": len(matches) / len(spots) if spots else math.nan,
            "mean_match_distance": statistics.mean(distances) if distances else math.nan,
            "median_match_distance": _legacy_median(distances) if distances else math.nan,
            "max_match_distance": max(distances) if distances else math.nan,
            **link_metrics,
        }
        summaries.append(summary)

        tag = _threshold_tag(threshold)
        match_rows = []
        match_by_id = {match.spot_id: match for match in matches}
        for spot in spots:
            match = match_by_id.get(spot.spot_id)
            if match is None:
                continue
            detection = detections[match.detection_id]
            match_rows.append(
                {
                    "mastodon_spot_id": spot.spot_id,
                    "mastodon_frame": spot.mastodon_frame,
                    "itec_frame": spot.frame,
                    "mastodon_track_id": "" if spot.track_id is None else spot.track_id,
                    "itec_id": match.detection_id,
                    "distance_itec_units": match.distance,
                    "mastodon_x_itec": spot.x,
                    "mastodon_y_itec": spot.y,
                    "mastodon_z_itec": spot.z,
                    "itec_x": detection.x,
                    "itec_y": detection.y,
                    "itec_z": detection.z,
                }
            )

        unmatched_rows = [
            {
                "mastodon_spot_id": spot.spot_id,
                "mastodon_frame": spot.mastodon_frame,
                "itec_frame": spot.frame,
                "mastodon_track_id": "" if spot.track_id is None else spot.track_id,
                "mastodon_x_itec": spot.x,
                "mastodon_y_itec": spot.y,
                "mastodon_z_itec": spot.z,
                "source_x": spot.source_x,
                "source_y": spot.source_y,
                "source_z": spot.source_z,
            }
            for spot in unmatched
        ]

        _write_csv(output / f"threshold{tag}_spot_matches.csv", match_rows)
        _write_csv(output / f"threshold{tag}_unmatched_spots.csv", unmatched_rows)
        _write_csv(output / f"threshold{tag}_link_validation.csv", link_rows)

    _write_csv(output / "validation_summary.csv", summaries)
    return summaries
