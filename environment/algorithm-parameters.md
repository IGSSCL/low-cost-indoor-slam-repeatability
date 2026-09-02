# Algorithms and processing parameters

The six implementations evaluated, and every parameter of the evaluation that is a
choice rather than a measurement. Values stated here are those used for the published
results; the article's Table 2 summarises the same information for the reader.

## Implementations

Five LiDAR–inertial algorithms and one LiDAR-only baseline. Each is the public
implementation released by its authors, run unmodified in its own container; only the
sensor topic, the extrinsics and the export settings were configured.

| Algorithm | Type | Repository | Commit / release | Config file | Notes |
|---|---|---|---|---|---|
| FAST-LIO2 | LiDAR–inertial, ikd-Tree map | `github.com/hku-mars/FAST_LIO` | *pending* | *pending* | |
| POINT-LIO | LiDAR–inertial, point-wise update | `github.com/hku-mars/Point-LIO` | *pending* | *pending* | |
| D-LIO | LiDAR–inertial, truncated distance field | `github.com/robotics-upo/D-LIO` | *pending* | *pending* | Exports trajectories at ≈101 Hz against 10 Hz for the rest, which is why all lengths are compared after resampling to 10 Hz |
| HDMapping-LIO | LiDAR–inertial | `github.com/MapsHD/HDMapping-LIO` | *pending* | *pending* | Highest CPU cost of the set, ≈752 core-seconds |
| LIO-LIVOX | LiDAR–inertial, tuned for Livox sensors | `github.com/Livox-SDK/LIO-Livox` | *pending* | *pending* | Largest exported maps |
| KISS-ICP | LiDAR only, no IMU | `github.com/PRBonn/kiss-icp` | *pending* | *pending* | Baseline. The only algorithm tuned to reduce drift and the only one with deskewing explicitly confirmed, so its trajectory metrics are obtained under conditions favourable to it |

> **To be completed before deposit.** The six repository URLs are filled in (added
> 1 September 2026, cross-checked against `references.bib`). Still missing, per
> algorithm: the exact commit or release evaluated, and the configuration file used —
> both need to be read off the actual container image or local clone, so they wait on
> access to the machine where the Docker images live (see `docker-images.md`, same
> blocker as the digests). The container digests go in `docker-images.md`.

## Sensor and capture

| | |
|---|---|
| Sensor | Livox Mid-360, internal IMU |
| Field of view | 360° × 59° |
| Mounting | Handheld tripod, tilted forward |
| Mass | 265 g |
| Route protocol | Walked manually, no instrumental speed control, equivalent path and movement pattern across repetitions |
| Capture duration | About 3 minutes per route |
| Repetitions | 13 in Experiment 1, 12 in Experiment 2 |

## Registration to the reference

| Parameter | Value |
|---|---|
| Coarse alignment | Centroid matching plus an exhaustive sweep over 24 yaw hypotheses |
| Points sampled, coarse | 60,000 per cloud |
| Coarse criterion | Lowest mean nearest-neighbour distance, truncated at 3 m |
| Fine alignment | Point-to-point ICP, multiscale |
| Correspondence distances | 3.0, 1.0, 0.4, 0.15 m |
| Iterations per scale | 30 maximum |
| Convergence | RMS change below 1e-5 m |
| Points sampled, fine | 120,000 at the two coarse scales, 300,000 at the two fine ones |
| Random seeds | Fixed |
| Applied to | The voxel-downsampled clouds, before any filtering |
| Crop after registration | Bounding box of the reference plus a 1 m margin |
| Failure criterion | Inlier fraction below 0.05 |

## Preprocessing and filtering

| Parameter | Value |
|---|---|
| Common voxel resolution | 1 cm, both clouds |
| Radius outlier removal | Grid-based: discard points with fewer than 3 occupied cells in their 3×3×3 neighbourhood at 10 cm resolution |
| Observed-region mask | Built from the reference occupancy grid at 25 cm, dilated by one voxel |
| Applied to | The SLAM cloud only |
| Direction | Asymmetric — accuracy on the filtered and masked cloud, completeness against the unfiltered cloud |

The asymmetry is deliberate and is not neutral; Section 3.4 of the article states why and
what it costs.

## Dimensional verification

| Parameter | Value |
|---|---|
| Plane detection | Histogram peaks of the coordinate along each axis, 2000 bins |
| Minimum separation between planes | 0.30 m |
| Maximum planes per axis | 6 |
| Minimum dimension | 1.0 m |
| Matching tolerance | 12 cm |

The tolerance is deliberately narrow. With a wide one the matching can pair a different
physical plane, which produces errors of about 300 mm identical across all algorithms —
the unmistakable signature of a matching failure rather than a reconstruction error.

## Element-level measurements

| Parameter | Value |
|---|---|
| Roughness band around each slab | 5 cm |
| Roughness cell | 0.5 m |
| Minimum points per cell | 40 |
| Roughness statistic | 1.4826 · MAD of the height residual, median over cells |
| Wall plumb | Principal components over a 2.2 m height band, inclination of the resulting normal |
| Slab separation | Modal height within a 35 cm band around each reference plane, refined by the centroid of points within 2 cm of the mode |
| Repetitions | Runs 1, 8, 13 of Experiment 1; runs 3, 9, 11 of Experiment 2 |

## Multicriteria synthesis

| Parameter | Value |
|---|---|
| Normalisation | Min–max over the evaluated set |
| Weights | $w_R = 0.30$, $w_Q = 0.50$, $w_C = 0.20$ |
| $R_a$ | CV of trajectory length, closure, speed dispersion, and — multi-level only — departure of the vertical range from the measured storey height |
| $Q_a$ | Chamfer, $P95$ accuracy, $P99$, coverage at 2 cm, median dimensional error |
| $C_a$ | Wall-clock time, CPU core-seconds, peak resident memory |
| Cross-checks | TOPSIS and VIKOR on the same subindex matrix |
| Sensitivity | Alternative weightings and leave-one-out over the alternatives |

The weights are an assumption of this study and not the output of an elicitation
procedure. The article says so, and reports the ranking's sensitivity to them.

## Statistics

| | |
|---|---|
| Omnibus | Skillings–Mack, runs as blocks |
| Pairwise | Wilcoxon signed-rank on paired runs |
| Multiplicity | Holm correction over the 15 pairs of each metric |
| Proportions | Wilson 95 % intervals; Fisher's exact test |
| Correlations | Spearman and Pearson, Holm-corrected over the declared family |
