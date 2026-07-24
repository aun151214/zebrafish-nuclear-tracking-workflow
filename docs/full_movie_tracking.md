# Full-movie tracking summary

The reusable full-movie analysis reports:

- detections per frame;
- valid parent-child links;
- adjacent, two-frame-gap and three-frame-gap links;
- continuous one-to-one tracklets;
- tracklet-length counts and survival;
- full-window tracklets.

## Tracklet definition

A detection inherits the previous detection's tracklet only when:

1. it has exactly one valid parent in the immediately preceding frame;
2. the parent has exactly one valid child in the current frame; and
3. the relationship is therefore an unambiguous consecutive continuation.

Roots, temporal gaps, divisions, merges and ambiguous relationships start
new tracklets. This reproduces the definition used for the thesis analysis.

## Example

```bash
PYTHONPATH=src python scripts/analyse_full_movie_tracking.py \
  --tracking-csv /path/to/tracking_result.csv \
  --output-dir output/full_movie \
  --frame-min 1 \
  --frame-max 75
```

The regression checker verifies the known 75-frame A_min1000 results.
