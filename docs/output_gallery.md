# Representative outputs

This document summarises the main tables and figures produced by the reusable analysis workflow.

Raw microscopy data and complete experiment outputs are not distributed in this repository.

## Temporal intensity analysis

The histogram workflow can produce:

- raw-versus-Dark-sectioned temporal intensity histograms;
- frame-wise intensity-percentile tables;
- zero-valued-voxel fraction summaries;
- PNG or PDF figures showing intensity changes through time.

## Segmentation validation

The object-level validation workflow can produce:

- frame-wise true-positive, false-positive, and false-negative counts;
- precision, recall, and F1 summaries;
- matched-object IoU results;
- predicted-versus-reference object-count comparisons;
- CSV tables and metric plots.

## Mastodon validation

The Mastodon validation workflow can produce:

- reviewed-spot recovery at selected distance thresholds;
- overall adjacent-link recovery;
- conditional link recovery when both endpoints are matched;
- component-level continuity classifications;
- frame-wise and component-wise CSV summaries;
- recovery plots.

## Full-movie tracking analysis

The tracking-quality-control workflow can produce:

- detections per frame;
- total reconstructed links;
- adjacent-frame and temporal-gap link counts;
- continuous one-to-one tracklet reconstruction;
- tracklet-length tables;
- tracklet-length histograms;
- long-track and full-duration tracklet summaries.

## Current gallery status

The repository documents the available outputs, but it does not currently include a complete visual gallery generated from laboratory microscopy data.

A future gallery should use either synthetic examples or laboratory-approved derived figures.

No raw images or confidential laboratory datasets should be added without approval.


## Important interpretation

The repository generates the principal reusable validation and quality-control plots.

It does not automatically reproduce every microscopy overlay, trajectory montage, or presentation figure included in the thesis.
