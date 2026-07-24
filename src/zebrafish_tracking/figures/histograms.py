from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import tifffile
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize


TIME_CMAP = LinearSegmentedColormap.from_list(
    "early_to_late",
    ["#ff1f1f", "#c0005a", "#7030a0", "#243cff", "#001cff"],
    N=256,
)
UINT16_VALUES = np.arange(65536)


def exact_uint16_histogram(path: str | Path) -> tuple[np.ndarray, int]:
    counts = np.zeros(65536, dtype=np.uint64)
    total = 0

    with tifffile.TiffFile(path) as tif:
        for page in tif.pages:
            values = page.asarray().astype(np.int64, copy=False).ravel()
            if values.size == 0:
                continue
            if values.min() < 0 or values.max() > 65535:
                raise ValueError(f"Values outside uint16 range in: {path}")
            counts += np.bincount(values, minlength=65536).astype(np.uint64)
            total += values.size

    if total == 0:
        raise ValueError(f"No voxels read from: {path}")
    return counts, total


def aggregate_percent(
    counts: np.ndarray,
    edges: np.ndarray,
    *,
    exclude_zero: bool,
) -> np.ndarray:
    work = counts.copy()
    if exclude_zero:
        work[0] = 0

    denominator = float(work.sum())
    if denominator <= 0:
        raise ValueError("Histogram contains no selected voxels")

    aggregated, _ = np.histogram(
        UINT16_VALUES,
        bins=edges,
        weights=work.astype(float),
    )
    return 100.0 * aggregated / denominator


def create_time_coloured_histograms(
    raw_files: Iterable[str | Path],
    dark_files: Iterable[str | Path],
    output_dir: str | Path,
    *,
    frame_numbers: Iterable[int],
    low_range_max: int = 12000,
    bins: int = 300,
) -> None:
    raw_paths = [Path(path) for path in raw_files]
    dark_paths = [Path(path) for path in dark_files]
    frames = list(frame_numbers)

    if not (len(raw_paths) == len(dark_paths) == len(frames)):
        raise ValueError("raw, dark and frame lists must have equal length")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    edges = np.linspace(1, low_range_max, bins + 1)
    centres = (edges[:-1] + edges[1:]) / 2
    normalizer = Normalize(vmin=min(frames), vmax=max(frames))

    records = []
    raw_curves = []
    dark_curves = []

    for frame, raw_path, dark_path in zip(frames, raw_paths, dark_paths):
        raw_counts, raw_total = exact_uint16_histogram(raw_path)
        dark_counts, dark_total = exact_uint16_histogram(dark_path)
        if raw_total != dark_total:
            raise ValueError(
                f"Voxel-count mismatch at frame {frame}: "
                f"raw={raw_total}, dark={dark_total}"
            )

        raw_curves.append(
            aggregate_percent(raw_counts, edges, exclude_zero=True)
        )
        dark_curves.append(
            aggregate_percent(dark_counts, edges, exclude_zero=True)
        )
        records.append(
            {
                "frame": frame,
                "raw_total_voxels": raw_total,
                "dark_total_voxels": dark_total,
                "raw_zero_percent": 100.0 * raw_counts[0] / raw_total,
                "dark_zero_percent": 100.0 * dark_counts[0] / dark_total,
            }
        )

    fig, axes = plt.subplots(
        2, 1, figsize=(8.5, 9), sharex=True, sharey=True,
        constrained_layout=True,
    )
    for frame, raw_curve, dark_curve in zip(frames, raw_curves, dark_curves):
        color = TIME_CMAP(normalizer(frame))
        axes[0].plot(centres, raw_curve, color=color, linewidth=1.7)
        axes[1].plot(centres, dark_curve, color=color, linewidth=1.7)

    axes[0].set_title("A. Raw volumes")
    axes[1].set_title("B. Dark-sectioned volumes")
    for axis in axes:
        axis.set_ylabel("Positive voxels per bin (%)")
        axis.set_yscale("log")
        axis.set_xlim(1, low_range_max)
        axis.grid(True, linewidth=0.35, alpha=0.35)
    axes[1].set_xlabel("Intensity (grey value)")
    fig.suptitle(
        f"Intensity distributions across frames {min(frames)}–{max(frames)}\n"
        "Positive voxels from complete 3D volumes",
        fontsize=13,
    )

    scalar_mappable = ScalarMappable(norm=normalizer, cmap=TIME_CMAP)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(
        scalar_mappable,
        ax=axes,
        fraction=0.025,
        pad=0.025,
        ticks=frames,
    )
    colorbar.set_label("Frame")

    fig.savefig(output / "time_coloured_histograms.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "time_coloured_histograms.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    axis.plot(
        frames,
        [record["raw_zero_percent"] for record in records],
        marker="o",
        label="Raw",
    )
    axis.plot(
        frames,
        [record["dark_zero_percent"] for record in records],
        marker="o",
        label="Dark-sectioned",
    )
    axis.set_xlabel("Frame")
    axis.set_ylabel("Zero-valued voxels (%)")
    axis.set_xticks(frames)
    axis.grid(True, linewidth=0.35, alpha=0.35)
    axis.legend()
    axis.set_title(
        f"Fraction of zero-valued voxels across frames "
        f"{min(frames)}–{max(frames)}"
    )
    fig.savefig(output / "zero_valued_voxel_fraction.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "zero_valued_voxel_fraction.pdf", bbox_inches="tight")
    plt.close(fig)

    with (output / "histogram_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
