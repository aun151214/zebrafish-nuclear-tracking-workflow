# External dependencies

## iTEC

The repository does not redistribute iTEC. A local installation must be
provided through the private path configuration. The exact iTEC version,
commit or archive checksum must be recorded before release.

Expected outputs used by this workflow include:

- `tracking_result.csv`
- `movieInfo.mat`
- instance-segmentation TIFF or MATLAB outputs

## Dark sectioning

The repository does not redistribute the Dark-sectioning implementation.
A local MATLAB installation and the approved Dark-sectioning source are
required. The current legacy wrapper copies one frame at a time into the
external tool's input directory and then crops its padded output. This
wrapper must be redesigned before shared multi-user use.

## MATLAB

Some historical preprocessing and pilot scripts require MATLAB. The Python
analysis package does not run iTEC itself.
