# Methodological choices

This document separates measurements calculated directly from the supplied files from methodological choices used in the thesis workflow.

## Data-derived measurements

The following values are calculated directly from prediction, tracking, image, and reference files:

- detections;
- parent-child links;
- temporal link gaps;
- tracklet lengths;
- true positives;
- false positives;
- false negatives;
- precision;
- recall;
- F1 score;
- matched-object IoU;
- Mastodon spot recovery;
- Mastodon link recovery;
- intensity histograms;
- intensity percentiles;
- zero-valued voxel fractions.

## Object-level segmentation matching

Reference and predicted objects are compared using intersection over union:

`IoU = intersection volume / union volume`

Candidate pairs must satisfy:

`IoU >= 0.10`

Candidate pairs are processed in descending IoU order. Each reference object and predicted object can be matched only once.

This greedy one-to-one procedure is retained because it reproduces the thesis validation workflow.

## Segmentation metrics

`Precision = TP / (TP + FP)`

`Recall = TP / (TP + FN)`

`F1 = 2 x Precision x Recall / (Precision + Recall)`

Reported precision, recall, and F1 values are macro-averaged across the ten evaluated frames. Total TP, FP, and FN values are also reported separately.

## Mastodon distance thresholds

The principal conservative matching threshold is:

`6 internal iTEC coordinate units`

Thresholds of 8 and 10 units are retained as sensitivity analyses.

These thresholds are methodological tolerances and should not be interpreted as universal biological distances.

## Tracking measurements

A continuous one-to-one tracklet continues only when:

1. the next detection occurs in the immediately following frame;
2. the parent has exactly one reconstructed child;
3. the child has an unambiguous parent relationship.

A tracklet ends at:

- a temporal gap;
- a branch;
- a terminal detection;
- the end of the analysed movie.

All reconstructed children, including non-adjacent gap children, are counted when determining whether a parent branches. This reproduces the historical thesis definition.

## Nuclear-volume conversion

For the mosaic experiment:

`Volume = internal voxel count x 4 x 0.347 x 0.347 x 0.700 cubic micrometres`

The factor four is used because x and y were each downsampled by two, while z was not downsampled.

This conversion must be changed for datasets using different calibration or downsampling.

## Important scientific boundaries

- Sparse Mastodon recovery is not global segmentation recall.
- Full-length tracklets are not automatically verified biological identities.
- `A_min1000` was strongest among the tested settings, not universally optimal.
- The 100-frame experiment is a scaling diagnostic, not a continuous 100-frame identity reconstruction.
- Channel 1 measurements are exploratory and are not validated biological oscillations.
