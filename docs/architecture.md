# Architecture

This document shows the boundary between external image-processing software and the reusable analysis modules contained in this repository.

## Scientific workflow and repository boundary

```text
Raw 3D microscopy volumes
            |
            v
Registration and cropping
   [external preprocessing]
            |
            v
Dark sectioning
   [external implementation]
            |
            v
iTEC segmentation and tracking
   [external implementation]
            |
            +-------------------------------+
            |                               |
            v                               v
Predicted instance labels           tracking_result.csv
            |                               |
            v                               +----------------------+
Instance-segmentation validation                           |
            ^                                              v
            |                                  Full-movie tracking QC
Reference instance masks                                and tracklets
                                                           |
Mastodon spot and link exports ----------------------------+
            |                                              |
            +--> Mastodon spot/link validation             |
            +--> reviewed-component continuity             |
                                                           |
Raw and Dark-sectioned volumes                             |
            |                                              |
            +--> temporal histogram generation             |
                                                           |
            +----------------------+-----------------------+
                                   |
                                   v
                         CSV summaries and plots
```

## Included reusable modules

- temporal intensity histogram generation;
- object-level instance-segmentation validation;
- Mastodon spot and adjacent-link validation;
- reviewed-component continuity analysis;
- full-movie detection and temporal-gap analysis;
- continuous one-to-one tracklet reconstruction;
- CSV summary and scientific plot generation.

## Thesis analyses not included as reusable modules

The following analyses were used during the thesis but are not currently included as verified reusable repository modules:

- post-correction nuclear-volume analysis;
- thesis-specific trajectory visualisation;
- exploratory Channel 1 intensity sampling;
- the complete Dark-sectioning implementation;
- the complete iTEC segmentation and tracking implementation.

## Code policy

- Reusable calculations belong under `src/zebrafish_tracking/`.
- Command-line entry points belong under `scripts/`.
- Dataset-specific values belong in YAML configuration files.
- Laboratory data, local paths, credentials and large experiment outputs are excluded.
- Historical, presentation-only and obsolete scripts are not part of the clean reusable package.
