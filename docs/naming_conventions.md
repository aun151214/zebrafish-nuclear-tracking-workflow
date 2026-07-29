# Naming conventions

This repository preserves historical experiment identifiers used during the thesis.
They remain unchanged so that outputs stay traceable to the thesis, validation files,
and regression targets.

## Segmentation configurations

| Historical identifier | Meaning |
|---|---|
| `A_min200` | Minimum accepted object size of 200 original-grid-equivalent voxels |
| `A_min1000` | Minimum accepted object size of 1,000 original-grid-equivalent voxels |

The letter `A` is retained as part of the historical run identifier.
No additional meaning is assigned unless defined in the original experiment record.

Because iTEC used twofold downsampling in both lateral dimensions:

- `A_min200` corresponds to 50 voxels on the internal processing grid.
- `A_min1000` corresponds to 250 voxels on the internal processing grid.

The conversion is:

`internal minimum size = original-grid-equivalent minimum size / (2 x 2)`

## Dataset identifiers

| Identifier | Meaning |
|---|---|
| `tenframe` | Reviewed ten-frame validation interval |
| `full75` | Complete 75-frame mosaic experiment |
| `benchmark_50frame` | Fifty-frame LoG v2 versus iTEC pilot |
| `benchmark_100frame` | One-hundred-frame scaling diagnostic |
| `terminator003_chunkB` | Terminator003 original frames 308-329 |

## Frame numbering

Mastodon uses zero-based frame numbering: `0-74`.
The corresponding iTEC output uses frame numbering: `1-75`.

`iTEC frame = Mastodon frame + 1`

## Coordinate units

Mastodon positions are stored in calibrated physical coordinates.
iTEC coordinates are represented on the internal processing grid.

For the mosaic dataset:

- lateral pixel size: 0.347 micrometres;
- axial spacing: 0.700 micrometres;
- lateral downsampling factor: 2.

## Future naming

New experiments should use descriptive identifiers such as:

`min-size-1000_bg-50_clip-0_no-motion`

Historical identifiers should remain unchanged when reproducing thesis results.
