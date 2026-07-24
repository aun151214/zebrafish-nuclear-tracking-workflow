# Data formats

## Image volumes

The workflow expects one 3D TIFF stack per frame for most processing stages.
The filename template is configurable, for example:

```text
t0001_Channel 2.tif
t0002_Channel 2.tif
```

## iTEC tracking CSV

Required columns used by the clean utilities:

- `ID`
- `frames`
- `xCoord`
- `yCoord`
- `zCoord`
- `parents`

Optional columns:

- `incoming links`
- `outgoing links`

Parent values may be empty, `NaN`, a scalar ID, or a textual list.

## Mastodon tables

The thesis validation uses cleaned spot and link CSV tables. Coordinate
calibration, frame offset and iTEC lateral downsampling must be defined in
the dataset configuration.

## Frame numbering

Mastodon frames in the mosaic reference are 0-based. iTEC tracking frames
are 1-based. The default mapping for that dataset is therefore:

```text
itec_frame = mastodon_frame + 1
```
