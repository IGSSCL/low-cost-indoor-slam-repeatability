# Container image

Of the six algorithms, only **LIO-LIVOX** runs in a Docker container; the other five
(FAST-LIO2, POINT-LIO, KISS-ICP, D-LIO, HDMapping-LIO) run natively in the ROS 2 Jazzy
workspace described in `algorithm-parameters.md`. An earlier draft of this file assumed
every algorithm ran in its own container; that was corrected on 2 September 2026
(ICT44/ICT45) after auditing the actual processing script (`procesar_mapa.sh`) against a
fully documented, previously processed run.

LIO-LIVOX's reference implementation targets ROS 1, which is why it alone runs isolated
from the native ROS 2 Jazzy environment, in a Docker image built on Ubuntu with
ROS 1 Noetic.

## Why a digest and not a tag

An image tag is mutable: `latest`, or even a version tag, can be repointed at a different
image after publication, and a reader who pulls it a year from now may get something that
is not what produced these results. The `sha256` digest is immutable and is what matters
for reproducibility.

The `slam-liolivox:noetic` image used here was built locally and was never pushed to a
registry, so it does not expose a registry `RepoDigest` — the value below is the local
Docker image ID (`docker inspect --format='{{.Id}}'`), not a pullable registry digest.
Anyone reproducing this pipeline from scratch should expect to rebuild the image from
`github.com/Livox-SDK/LIO-Livox` at the commit below rather than pull it.

## Image used

| Algorithm | Image | Local image ID (`sha256:`) | Registry digest |
|---|---|---|---|
| LIO-LIVOX | `slam-liolivox:noetic` | `b5e5ccad0d5ed92c56c178fc5f73af00a76c7d81d48754f311d227db1596d8a2` | Not published; local build only |

Repository and commit used inside this image are recorded in `algorithm-parameters.md`.
Its configuration files are `algorithm-configs/lio-livox_runtime_script.sh` (launch and
capture orchestration) and `docker-image-configs/lio-livox_mid360_image.yaml` (LIO-LIVOX
algorithm parameters).

## Docker images present but not used

Three further local images existed on the processing machine at audit time —
`slam-fastlio:noetic`, `slam-pointlio:noetic` and `slam-dlio:noetic` — built at some
earlier point while evaluating a Docker-based approach for those algorithms. They are
**not invoked** by the current `procesar_mapa.sh` and did not produce any of the results
reported in the article; they are listed here only so a reader auditing the machine does
not mistake them for part of the pipeline.

| Image | Local image ID (`sha256:`) |
|---|---|
| `slam-fastlio:noetic` | `070df2095763f74221b61608e7c8e922bc5aa7dec7a84a47d17d26e0e2adc2af` |
| `slam-pointlio:noetic` | `94318dc3c306f90dcef6bb8caa3b1db2d481506d729b3142454d9d06b18bf4ea` |
| `slam-dlio:noetic` | `54b85cf50544f6173539961b5048792ed1c3403df7493252f950801df9663b32` |

No local Docker image was found for KISS-ICP or HDMapping-LIO at any point.

## Host

| | |
|---|---|
| Operating system | Ubuntu 24.04.4 LTS |
| Middleware (native algorithms) | ROS 2 Jazzy |
| Middleware (LIO-LIVOX container) | ROS 1 Noetic |
| Container runtime | Docker |
| Compute | CPU only, no GPU |
| Sensor | Livox Mid-360 with its internal IMU, on a handheld tripod tilted forward |

Wall-clock time, CPU core-seconds and peak resident memory per algorithm are in
`data/runwise/computational.csv`.
