from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Literal, Mapping

from zebrafish_tracking.analysis.tracklets import reconstruct_one_to_one_tracklets
from zebrafish_tracking.io.mastodon_csv import MastodonSpot
from zebrafish_tracking.io.tracking_csv import Detection, safe_float, safe_int

CrossTrackMode = Literal["exclude", "source"]


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else math.nan


def _longest_recovered_segment(
    spots: list[MastodonSpot],
    matched_spot_ids: set[int],
    recovered_links: list[tuple[int, int]],
) -> int:
    incoming: dict[int, list[int]] = defaultdict(list)
    for source_id, target_id in recovered_links:
        if source_id in matched_spot_ids and target_id in matched_spot_ids:
            incoming[target_id].append(source_id)

    longest_to: dict[int, int] = {}
    for spot in sorted(spots, key=lambda item: (item.mastodon_frame, item.spot_id)):
        if spot.spot_id not in matched_spot_ids:
            longest_to[spot.spot_id] = 0
            continue
        best = 1
        for source_id in incoming.get(spot.spot_id, []):
            previous = longest_to.get(source_id, 0)
            if previous > 0:
                best = max(best, previous + 1)
        longest_to[spot.spot_id] = best
    return max(longest_to.values(), default=0)


def analyse_track_components(
    *,
    spots: list[MastodonSpot],
    match_rows: Iterable[Mapping[str, object]],
    link_rows: Iterable[Mapping[str, object]],
    detections: Mapping[int, Detection] | None = None,
    cross_track_mode: CrossTrackMode = "exclude",
) -> tuple[list[dict], list[dict], dict]:
    if cross_track_mode not in {"exclude", "source"}:
        raise ValueError("cross_track_mode must be 'exclude' or 'source'")

    spot_by_id = {spot.spot_id: spot for spot in spots}
    spots_by_track: dict[int, list[MastodonSpot]] = defaultdict(list)
    for spot in spots:
        if spot.track_id is not None:
            spots_by_track[spot.track_id].append(spot)
    if not spots_by_track:
        raise ValueError("No Mastodon track/component IDs were available")

    match_by_spot: dict[int, dict[str, int | float | None]] = {}
    for row in match_rows:
        spot_id = safe_int(row.get("mastodon_spot_id"))
        detection_id = safe_int(row.get("itec_id"))
        if spot_id is None or detection_id is None:
            continue
        match_by_spot[spot_id] = {
            "itec_id": detection_id,
            "distance": safe_float(row.get("distance_itec_units")),
        }

    detection_to_tracklet: dict[int, int] = {}
    if detections:
        for tracklet in reconstruct_one_to_one_tracklets(detections):
            for detection_id in tracklet.detection_ids:
                detection_to_tracklet[detection_id] = tracklet.tracklet_id

    links_by_track: dict[int, list[dict]] = defaultdict(list)
    for row in link_rows:
        source_id = safe_int(row.get("source_mastodon_spot_id"))
        target_id = safe_int(row.get("target_mastodon_spot_id"))
        if source_id is None or target_id is None:
            continue
        source_spot = spot_by_id.get(source_id)
        target_spot = spot_by_id.get(target_id)
        if source_spot is None or target_spot is None:
            continue
        if source_spot.track_id is None or target_spot.track_id is None:
            continue
        if cross_track_mode == "exclude" and source_spot.track_id != target_spot.track_id:
            continue

        source_itec_id = safe_int(row.get("source_itec_id"))
        target_itec_id = safe_int(row.get("target_itec_id"))
        links_by_track[source_spot.track_id].append(
            {
                "source_spot_id": source_id,
                "target_spot_id": target_id,
                "source_itec_id": source_itec_id,
                "target_itec_id": target_itec_id,
                "both_matched": str(row.get("status", "")).strip()
                != "not_both_spots_matched",
                "recovered": safe_int(row.get("recovered_link")) == 1,
                "status": str(row.get("status", "")).strip(),
            }
        )

    component_rows: list[dict] = []
    for track_id in sorted(spots_by_track):
        track_spots = sorted(
            spots_by_track[track_id],
            key=lambda spot: (spot.mastodon_frame, spot.spot_id),
        )
        track_links = links_by_track.get(track_id, [])
        manual_spot_ids = {spot.spot_id for spot in track_spots}
        matched_spot_ids = manual_spot_ids.intersection(match_by_spot)

        total_spots = len(track_spots)
        matched_spots = len(matched_spot_ids)
        total_links = len(track_links)
        both_matched_links = sum(bool(link["both_matched"]) for link in track_links)
        recovered_links = sum(bool(link["recovered"]) for link in track_links)
        recovered_pairs = [
            (int(link["source_spot_id"]), int(link["target_spot_id"]))
            for link in track_links
            if link["recovered"]
        ]

        longest_segment = _longest_recovered_segment(
            track_spots,
            matched_spot_ids,
            recovered_pairs,
        )

        matched_tracklet_ids = []
        for spot_id in matched_spot_ids:
            detection_id = match_by_spot[spot_id]["itec_id"]
            assert isinstance(detection_id, int)
            tracklet_id = detection_to_tracklet.get(detection_id)
            if tracklet_id is not None:
                matched_tracklet_ids.append(tracklet_id)

        crossing_boundaries = 0
        if detection_to_tracklet:
            for link in track_links:
                source_det = link["source_itec_id"]
                target_det = link["target_itec_id"]
                if not isinstance(source_det, int) or not isinstance(target_det, int):
                    continue
                source_tracklet = detection_to_tracklet.get(source_det)
                target_tracklet = detection_to_tracklet.get(target_det)
                if (
                    source_tracklet is not None
                    and target_tracklet is not None
                    and source_tracklet != target_tracklet
                ):
                    crossing_boundaries += 1

        if matched_spots == 0:
            status = "not recovered"
        elif matched_spots == total_spots and recovered_links == total_links:
            status = "fully recovered"
        elif matched_spots == total_spots:
            status = "all spots matched but link break present"
        else:
            status = "partially recovered"

        distances = [
            match_by_spot[spot_id]["distance"]
            for spot_id in matched_spot_ids
            if isinstance(match_by_spot[spot_id]["distance"], float)
        ]

        component_rows.append(
            {
                "mastodon_track_id": track_id,
                "first_frame": min(spot.mastodon_frame for spot in track_spots),
                "last_frame": max(spot.mastodon_frame for spot in track_spots),
                "manual_spots": total_spots,
                "matched_spots": matched_spots,
                "unmatched_spots": total_spots - matched_spots,
                "spot_recovery_fraction": _safe_ratio(matched_spots, total_spots),
                "manual_adjacent_links": total_links,
                "links_with_both_endpoints_matched": both_matched_links,
                "recovered_direct_links": recovered_links,
                "overall_link_recovery_fraction": _safe_ratio(
                    recovered_links, total_links
                ),
                "conditional_link_recovery_fraction": _safe_ratio(
                    recovered_links, both_matched_links
                ),
                "longest_recovered_segment_spots": longest_segment,
                "longest_recovered_segment_fraction": _safe_ratio(
                    longest_segment, total_spots
                ),
                "distinct_itec_tracklets_assigned": len(set(matched_tracklet_ids)),
                "manual_links_crossing_itec_tracklet_boundary": crossing_boundaries,
                "mean_match_distance": statistics.mean(distances) if distances else math.nan,
                "median_match_distance": statistics.median(distances) if distances else math.nan,
                "status": status,
            }
        )

    status_order = [
        "fully recovered",
        "all spots matched but link break present",
        "partially recovered",
        "not recovered",
    ]
    counts = Counter(str(row["status"]) for row in component_rows)
    status_rows = [
        {
            "status": status,
            "count": counts.get(status, 0),
            "fraction": counts.get(status, 0) / len(component_rows),
        }
        for status in status_order
    ]

    spot_values = [float(row["spot_recovery_fraction"]) for row in component_rows]
    link_values = [
        float(row["overall_link_recovery_fraction"])
        for row in component_rows
        if int(row["manual_adjacent_links"]) > 0
    ]
    conditional_values = [
        float(row["conditional_link_recovery_fraction"])
        for row in component_rows
        if int(row["links_with_both_endpoints_matched"]) > 0
    ]
    longest_values = [
        float(row["longest_recovered_segment_fraction"]) for row in component_rows
    ]

    aggregate = {
        "components": len(component_rows),
        "fully_recovered": counts.get("fully recovered", 0),
        "all_spots_matched_link_break": counts.get(
            "all spots matched but link break present", 0
        ),
        "partially_recovered": counts.get("partially recovered", 0),
        "not_recovered": counts.get("not recovered", 0),
        "mean_component_spot_recovery": statistics.mean(spot_values),
        "median_component_spot_recovery": statistics.median(spot_values),
        "mean_component_overall_link_recovery": statistics.mean(link_values),
        "median_component_overall_link_recovery": statistics.median(link_values),
        "mean_component_conditional_link_recovery": (
            statistics.mean(conditional_values) if conditional_values else math.nan
        ),
        "median_component_conditional_link_recovery": (
            statistics.median(conditional_values) if conditional_values else math.nan
        ),
        "mean_longest_recovered_segment_fraction": statistics.mean(longest_values),
        "components_mapped_to_zero_itec_tracklets": sum(
            int(row["distinct_itec_tracklets_assigned"]) == 0 for row in component_rows
        ),
        "components_mapped_to_one_itec_tracklet": sum(
            int(row["distinct_itec_tracklets_assigned"]) == 1 for row in component_rows
        ),
        "components_mapped_to_multiple_itec_tracklets": sum(
            int(row["distinct_itec_tracklets_assigned"]) > 1 for row in component_rows
        ),
    }
    return component_rows, status_rows, aggregate


def write_component_analysis(
    output_dir: str | Path,
    component_rows: list[dict],
    status_rows: list[dict],
    aggregate: dict,
) -> None:
    output = Path(output_dir)
    _write_csv(output / "component_summary.csv", component_rows)
    _write_csv(output / "status_summary.csv", status_rows)
    _write_csv(output / "aggregate_summary.csv", [aggregate])
