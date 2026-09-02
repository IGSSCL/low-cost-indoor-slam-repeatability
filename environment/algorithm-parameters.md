# Algorithms and processing parameters

The six implementations evaluated, and every parameter of the evaluation that is a
choice rather than a measurement. Values stated here are those used for the published
results; the article's Table 2 summarises the same information for the reader.

Audit performed 1 September 2026 on the processing machine, cross-checked 2 September
2026 against a fully documented representative run (see below). It resolved an open
question in `REGISTRO_DE_CAMBIOS.md` (ICT44/ICT45): only one of the six implementations,
LIO-LIVOX, actually runs in Docker; the other five run natively.

## Execution model

`procesar_mapa.sh` is the main processing script
(SHA256 `1d54453e8151ddd4f7f2d3e6ae746c2fb320760ce91118dde2c08d678162e516`). Five
algorithms run natively in a ROS 2 Jazzy workspace; only LIO-LIVOX, whose reference
implementation targets ROS 1, runs in an isolated Docker container.

| Algorithm | Execution mode | Launch command family |
|---|---|---|
| FAST-LIO2 | Native ROS 2 Jazzy | `ros2 launch fast_lio mapping.launch.py` |
| POINT-LIO | Native ROS 2 Jazzy | `ros2 launch point_lio_ros2 mapping.launch.py` |
| KISS-ICP | Native ROS 2 Jazzy | `ros2 launch kiss_icp odometry.launch.py` |
| D-LIO | Native ROS 2 Jazzy | `ros2 run direct_lidar_inertial_odometry dlio_odom_node` / `dlio_map_node` |
| HDMapping-LIO | Native ROS 2 Jazzy | `ros2 launch hdmapping_lio hdmapping_lio.launch.py` |
| LIO-LIVOX | Docker, ROS 1 Noetic | `docker run ... slam-liolivox:noetic bash /run_lio_livox.sh` |

Host environment for the five native algorithms:

| Component | Value |
|---|---|
| Operating system | Ubuntu 24.04.4 LTS, noble |
| Kernel | Linux 6.17.0-35-generic x86_64 |
| ROS distribution | Jazzy |
| `ros-jazzy-desktop` | `0.11.0-1noble.20260616.084553` |
| `ros-jazzy-ros-base` | `0.11.0-1noble.20260616.084325` |
| `ros-jazzy-rclcpp` | `28.1.21-1noble.20260615.133124` |
| `ros-jazzy-rosbag2` | `0.26.11-1noble.20260616.084050` |

## Implementations

Each is the public implementation released by its authors (or, where noted, an actively
maintained ROS 2 port of it), run unmodified; only the sensor topic, the extrinsics and
the export settings were configured.

| Algorithm | Type | Repository | Commit | Config file | Notes |
|---|---|---|---|---|---|
| FAST-LIO2 | LiDAR–inertial, ikd-Tree map | `github.com/Ericsii/FAST_LIO` | `2fffc570a25d0df172720bac034fbdb6a13d2162` | `algorithm-configs/fast-lio2_mid360_runtime.yaml` | ROS 2 port of the original `hku-mars/FAST_LIO` (cited in the article for the method); required for the native ROS 2 Jazzy workspace |
| POINT-LIO | LiDAR–inertial, point-wise update | `github.com/alvgaona/point_lio_ros2` | `a9527fe7b3122ae0195cb7192ff9fbb2b2e08338` | `algorithm-configs/point-lio_mid360_source.yaml` | ROS 2 port of the original `hku-mars/Point-LIO` (cited in the article for the method); uncommitted local changes present at audit time, see source snapshot hash below |
| D-LIO | LiDAR–inertial, direct scan-to-map GICP, keyframe submap | `github.com/vectr-ucla/direct_lidar_inertial_odometry` | `c8acc37100e349d70a9d8432d656cbce7e5072cd` | `algorithm-configs/d-lio_mid360_runtime.yaml` | This is VECTR/UCLA's *Direct LiDAR-Inertial Odometry* (Chen, Nemiroff & Lopez, ICRA 2023). An earlier version of this file pointed to a different, unrelated algorithm that shares the same "D-LIO" name (Universidad Pablo de Olavide's truncated-distance-field method); corrected 2 September 2026 (ICT45) after auditing the actual source tree. Exports trajectories at ≈101 Hz against 10 Hz for the rest, which is why all lengths are compared after resampling to 10 Hz |
| HDMapping-LIO | LiDAR–inertial | `github.com/MapsHD/HDMapping-LIO` | `0198b8ef0351cd5845900b8e12882034332c52c1` | `algorithm-configs/hdmapping-lio_mid360_runtime.yaml` | Highest CPU cost of the set, ≈752 core-seconds |
| LIO-LIVOX | LiDAR–inertial, tuned for Livox sensors | `github.com/Livox-SDK/LIO-Livox` | `2296e4bea59bcfec09624a6f052fd6bfbe2b1e6a` | `algorithm-configs/lio-livox_runtime_script.sh`, `docker-image-configs/lio-livox_mid360_image.yaml` | The only algorithm run in Docker (image `slam-liolivox:noetic`, ROS 1 Noetic); see `docker-images.md`. Largest exported maps |
| KISS-ICP | LiDAR only, no IMU | `github.com/PRBonn/kiss-icp` | `3f08908f45e85c02c98c66d7dc0d45184352d319` | `algorithm-configs/kiss-icp_mid360_runtime.yaml` | Baseline. The only algorithm tuned to reduce drift and the only one with deskewing explicitly confirmed, so its trajectory metrics are obtained under conditions favourable to it |

Uncommitted local changes were present in the native source trees for POINT-LIO (3),
KISS-ICP (2), D-LIO (1) and HDMapping-LIO (4) at audit time. For those, a SHA256 of the
local source snapshot (tree without `.git`) is a more faithful identifier than the
commit alone:

| Algorithm | Source snapshot SHA256 |
|---|---|
| FAST-LIO2 | `1eb7efda6a422e8bd3962927f1df8ffc58cc7daf966195f71fa7bffc88ad1d0e` |
| POINT-LIO | `9acfa2eed5576d736688b06187e6ff650174bbbad5a6723edcbee34574d31d4f` |
| KISS-ICP | `d6f8f2007bb8414088e02ac69c4cafb440cda41398bbfbb028cde3ad7038dad0` |
| D-LIO | `5a488f5e4374eb86486e427f9333a6c36f5fdee8bfd1c06a46b4a669988496ec` |
| HDMapping-LIO | `19c2f8c81ce1b6011eab874a2d87ca50cffc6c3e959e6c90aaeb5d48d346b01a` |

## Configuration files

Two sets of runtime configuration files are kept, both copied verbatim from the
processing machine and hash-verified against `SHA256SUMS.txt`:

- `algorithm-configs/` — the configuration found for each algorithm during the 1
  September 2026 audit, taken from a processed run or, absent that, from the local
  source tree.
- `runtime-configs-representative/` — the configuration tied to one specific, fully
  documented representative run (dataset `medicion_20260618_151921`, processed
  2026-06-27, folder `Oficinas_Final/1`), kept separately because for three algorithms
  (FAST-LIO2, HDMapping-LIO, KISS-ICP) it differs from the file above — parameters were
  not necessarily identical across the 25 runs of the study.

Additionally, `docker-image-configs/lio-livox_mid360_image.yaml` is LIO-LIVOX's own
algorithm-parameter file (distinct from `lio-livox_runtime_script.sh`, which is the
container's launch/capture orchestration script).

Local Docker images `slam-fastlio:noetic`, `slam-pointlio:noetic` and `slam-dlio:noetic`
were also present on the processing machine, with their own bundled configuration files,
but confirmed **not invoked** by `procesar_mapa.sh` — they are not part of the
reproducible pipeline and their configs are not included here. No local Docker image was
found for KISS-ICP or HDMapping-LIO.

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
