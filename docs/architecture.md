# Architecture

## Main pipeline

```text
registered 3D volumes
        |
        v
input preparation / optional cropping
        |
        v
optional Dark sectioning
        |
        v
iTEC segmentation and tracking (external dependency)
        |
        +--> instance labels / movieInfo.mat
        |
        +--> tracking_result.csv
                    |
                    +--> segmentation validation
                    +--> Mastodon spot and link validation
                    +--> tracklet and frame-gap analysis
                    +--> post-correction volume analysis
                    +--> trajectory visualisation
                    +--> optional Channel 1 sampling
```

## Code policy

- Reusable calculations belong under `src/zebrafish_tracking/`.
- Command-line entry points belong under `scripts/`.
- Dataset-specific values belong in YAML configuration files.
- Frozen original scripts used to reproduce thesis outputs remain under
  `legacy_reference/` until each result has been reproduced by the clean code.
- Presentation-only and obsolete scripts are not part of the main pipeline.
