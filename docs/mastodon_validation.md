# Mastodon validation

The reusable validator preserves the thesis method:

1. Convert reviewed Mastodon coordinates into the internal iTEC coordinate system.
2. Shift Mastodon frame `0` to iTEC frame `1`.
3. Within each frame, enumerate pairs within the selected distance threshold.
4. Sort candidate pairs by distance and accept the shortest unused spot–detection pair.
5. Evaluate direct parent recovery only for reviewed links joining adjacent frames.
6. Report spot recovery, overall adjacent-link recovery and conditional link recovery.

The short-window reference uses full-resolution pixel/slice coordinates. The full-duration
reference uses physical micrometre coordinates and `reviewed == 1` filters.
