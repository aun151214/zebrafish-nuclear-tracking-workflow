# Repository scope

This document explains the boundary between the complete scientific workflow and the reusable analysis components included in this repository.

## Complete scientific workflow

```text
Raw 3D microscopy images
            |
            v
Registration and cropping
            |
            v
Dark sectioning
   [external implementation]
            |
            v
iTEC segmentation and tracking
   [external implementation]
            |
            +-----------------------------+
            |                             |
            v                             v
Predicted instance labels         tracking_result.csv
            |                             |
            +--------------+--------------+
                           |
                           v
               THIS GITHUB REPOSITORY
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
Segmentation          Mastodon            Full-movie
validation            validation          tracking QC
       |                   |                   |
       +-------------------+-------------------+
                           |
                           v
               CSV summaries and plots
```

## What is external

The following stages are not implemented by this repository:

- raw-image acquisition;
- image registration;
- the complete Dark-sectioning algorithm;
- the complete iTEC segmentation engine;
- the complete iTEC tracking and correction engine.

These stages must be completed using the appropriate external laboratory software before most repository validation and analysis commands are run.

## What is included

The repository contains reusable and tested components for:

- temporal intensity histogram generation;
- object-level segmentation validation;
- Mastodon spot and link validation;
- reviewed-component continuity analysis;
- full-movie detection and link analysis;
- temporal-gap analysis;
- continuous tracklet reconstruction;
- CSV summary generation;
- scientific plot generation;
- regression testing;
- repository cleanliness and safety testing.

## Expected inputs

Depending on the selected analysis, users provide one or more of the following:

- raw and Dark-sectioned image volumes;
- predicted instance-label volumes;
- reference instance-label volumes;
- iTEC `tracking_result.csv` files;
- Mastodon spot tables;
- Mastodon link tables;
- dataset calibration and coordinate-conversion parameters.

## Generated outputs

The workflow produces reusable outputs such as:

- frame-wise CSV tables;
- segmentation precision, recall, and F1 summaries;
- Mastodon spot- and link-recovery summaries;
- tracklet-length tables;
- temporal-gap summaries;
- detections-per-frame plots;
- tracklet-length histograms;
- temporal intensity histograms;
- percentile and zero-valued-voxel summaries.

## Central scope statement

This repository is a post-processing, validation, quality-control, and visualisation workflow for zebrafish segmentation and tracking outputs.

It is not the complete raw-image-to-segmentation-and-tracking implementation.
