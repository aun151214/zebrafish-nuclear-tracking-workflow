# Reproducibility status

## Current status

The reusable analysis repository has completed dataset-level regression
testing for the principal thesis metrics.

Verified components:

1. **Temporal histograms**
   - full-volume raw versus Dark-sectioned histograms;
   - zero-valued voxel percentages;
   - frame-wise intensity percentiles.

2. **Mastodon detection and link validation**
   - ten-frame sparse validation;
   - full-75 reviewed-spot validation;
   - thesis greedy one-to-one matching preserved.

3. **Reviewed component continuity**
   - ten-frame reviewed track segments;
   - full-duration reviewed components;
   - spot, overall-link and conditional-link summaries.

4. **Full-movie tracking summaries**
   - detections per frame;
   - parent-child temporal gaps;
   - continuous one-to-one tracklet reconstruction;
   - tracklet-length and survival summaries.

5. **Object-level instance-segmentation validation**
   - A_min200 ten-frame results;
   - A_min1000 ten-frame results;
   - aggregate and per-frame metrics.

## Verified headline values

### A_min200 segmentation

- precision: 0.753948
- recall: 0.947995
- F1: 0.839701

### A_min1000 segmentation

- precision: 0.850818
- recall: 0.920179
- F1: 0.883983

### Full-75 tracking summary

- detections: 269,330
- parent-child links: 260,002
- adjacent links: 251,342
- continuous one-to-one tracklets: 31,125
- tracklets lasting at least 10 frames: 8,554
- full 75-frame tracklets: 147

## Important limitations

Regression agreement demonstrates that the clean implementation reproduces
the historical thesis calculations. It does not prove biological correctness
for every reconstructed identity, and it does not generalise the measured
performance to unrelated datasets.

The complete iTEC and Dark-sectioning implementations are external and are
not distributed here. Large source datasets are also excluded.

## Release status

The code is suitable for a private lab-review repository. Public release,
licensing, authorship and redistribution remain pending lab approval.
