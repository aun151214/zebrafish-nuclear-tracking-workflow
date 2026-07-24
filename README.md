# Zebrafish Nuclear Tracking Workflow

> **Status:** private, pre-release research software.  
> Redistribution and public release remain subject to Oates Lab / EPFL
> approval. No public licence has been assigned.

This repository contains the reusable analysis and validation components
developed for the thesis:

**Multiscale Temporal Tracking of Zebrafish Embryo Development in
Multidimensional Images**

## Scope

The workflow supports:

1. reading iTEC detection and parent-link tables;
2. generating full-volume temporal intensity histograms;
3. validating 3D instance segmentation against labelled reference masks;
4. validating detections and adjacent links against reviewed Mastodon exports;
5. measuring reviewed-track/component continuity;
6. summarising full-movie detections, temporal link gaps and continuous
   one-to-one tracklets.

The repository does **not** include the complete iTEC implementation,
Dark-sectioning implementation, microscopy datasets, large MATLAB outputs,
private credentials or lab-specific path configuration.

## Verified regression components

The following components have been reproduced against the thesis outputs:

| Component | Verified result |
|---|---|
| Temporal histogram generation | Exact frame-wise histogram and zero-fraction regression |
| Mastodon spot/link validation | Ten-frame and full-75 threshold results reproduced |
| Component continuity | Ten-frame and full-duration component summaries reproduced |
| Full-movie tracking summary | 269,330 detections, 260,002 links and 31,125 tracklets reproduced |
| Instance-segmentation validation | A_min200 and A_min1000 aggregate and per-frame metrics reproduced |

The verified values and the scientific interpretation remain tied to the
specific datasets, preprocessing and parameter settings documented in the
thesis. They are regression targets, not universal performance guarantees.

## Installation

Using Conda:

```bash
conda env create -f environment.yml
conda activate zebrafish-tracking-workflow
python -m pip install -e ".[test]"
python -m pytest tests -q
```

Using an existing Python environment:

```bash
python -m pip install -e ".[test]"
python -m pytest tests -q
```

## Local paths

Copy the path template:

```bash
cp configs/paths.example.yaml configs/paths.yaml
```

Edit `configs/paths.yaml` for the local machine. It is excluded from version
control.

## Main commands

### Temporal histograms

```bash
python scripts/make_time_coloured_histograms.py \
  --raw-dir /path/to/raw_frames \
  --dark-dir /path/to/dark_frames \
  --output-dir outputs/histograms \
  --first-frame 1 \
  --last-frame 10
```

### Instance-segmentation validation

```bash
python scripts/validate_instance_segmentation.py \
  --run-name example_run \
  --ground-truth-mask /path/to/labelled_masks.tif \
  --prediction-dir /path/to/InstanceSeg_res \
  --output-dir outputs/segmentation_validation \
  --first-frame 1 \
  --last-frame 10 \
  --iou-threshold 0.10
```

### Mastodon validation

```bash
python scripts/validate_mastodon_tracking.py \
  --dataset-name example_dataset \
  --spots-csv /path/to/mastodon_spots.csv \
  --links-csv /path/to/mastodon_links.csv \
  --tracking-csv /path/to/tracking_result.csv \
  --output-dir outputs/mastodon_validation \
  --coordinate-mode pixels \
  --first-mastodon-frame 0 \
  --last-mastodon-frame 9 \
  --frame-offset 1 \
  --xy-downsample 2 \
  --thresholds 6 8 10
```

### Full-movie tracking summary

```bash
python scripts/analyse_full_movie_tracking.py \
  --tracking-csv /path/to/tracking_result.csv \
  --output-dir outputs/full_movie_tracking \
  --frame-min 1 \
  --frame-max 75
```

## Repository cleanliness check

Before creating a commit or archive:

```bash
python scripts/check_repository_cleanliness.py --root .
```

This checks for caches, large binary data, local absolute paths, internal
staging folders and likely credential material.

## Documentation

- `docs/architecture.md`
- `docs/data_formats.md`
- `docs/external_dependencies.md`
- `docs/mastodon_validation.md`
- `docs/component_continuity.md`
- `docs/full_movie_tracking.md`
- `docs/instance_segmentation_validation.md`
- `docs/reproducibility_status.md`
- `docs/release_checklist.md`

## Scientific boundaries

- The 50-frame comparison is a pilot benchmark rather than dense
  ground-truth validation.
- The 100-frame experiment is a scaling and failure-mode diagnostic.
- The ten-frame experiment provides the primary dense segmentation and sparse
  tracking validation.
- The 75-frame experiment provides scalability and sparse full-duration
  validation, not dense global precision.
- Sparse Mastodon recovery must not be described as global segmentation
  recall.
- Full-length reconstructed tracklets are not automatically verified
  biological identities.

## Licence and external software

See `LICENSE_PENDING.md` and `docs/external_dependencies.md`.

Until ownership and redistribution terms are confirmed, keep the repository
private and do not redistribute third-party implementations or microscopy
data.
