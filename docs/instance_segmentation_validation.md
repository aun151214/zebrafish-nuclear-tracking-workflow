# Object-level instance-segmentation validation

This module reproduces the 10-frame thesis validation of iTEC instance
segmentation against a manually labelled 3D mask movie.

## Method

For each frame:

1. load the prediction label volume from a MATLAB file;
2. orient it to the ground-truth `(z, y, x)` frame by maximizing foreground
   overlap among the same orientation candidates used by the legacy script;
3. compute pairwise object IoU values;
4. retain candidate pairs with IoU >= 0.10;
5. sort candidates by descending IoU;
6. greedily enforce one predicted object and one ground-truth object per match;
7. report TP, FP, FN, precision, recall, F1 and mean matched IoU.

The greedy assignment and the 0.10 IoU threshold are explicit thesis
replication settings. They must not be silently replaced when reproducing
published thesis values.

## Outputs

- `segmentation_per_frame.csv`
- `segmentation_summary.csv`
- `segmentation_validation.png`
- `segmentation_validation.pdf`

## Example

```bash
PYTHONPATH=src python scripts/validate_instance_segmentation.py \
  --run-name example \
  --ground-truth-mask /path/to/ground_truth_masks.tif \
  --prediction-dir /path/to/InstanceSeg_res \
  --output-dir output/example \
  --first-frame 1 \
  --last-frame 10 \
  --iou-threshold 0.10
```
