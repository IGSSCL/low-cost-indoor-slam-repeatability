# Container images

Each algorithm ran in its own container on Ubuntu 24.04 with ROS 2 Jazzy, **CPU only**.
No GPU is used at any stage, so the evaluation host needs nothing beyond Docker.

## Why digests and not tags

An image tag is mutable: `latest`, or even a version tag, can be repointed at a different
image after publication, and a reader who pulls it a year from now may get something that
is not what produced these results. The `sha256` digest is immutable and is what the
table below must record.

Pull by digest, not by tag:

```bash
docker pull <repository>@sha256:<digest>
```

## Images used

> **To be completed before deposit.** Run `record-digests.sh` on the machine where the
> images live and paste its output here. The digests are not recoverable afterwards if
> the images are deleted, so this is the one item in the repository that must be filled
> in from the original environment.

| Algorithm | Image | Tag | Digest (`sha256:`) |
|---|---|---|---|
| FAST-LIO2 | | | |
| POINT-LIO | | | |
| D-LIO | | | |
| HDMapping-LIO | | | |
| LIO-LIVOX | | | |
| KISS-ICP | | | |

## Host

| | |
|---|---|
| Operating system | Ubuntu 24.04 LTS |
| Middleware | ROS 2 Jazzy |
| Container runtime | Docker |
| Compute | CPU only, no GPU |
| Sensor | Livox Mid-360 with its internal IMU, on a handheld tripod tilted forward |

Wall-clock time, CPU core-seconds and peak resident memory per algorithm are in
`data/runwise/computational.csv`.
