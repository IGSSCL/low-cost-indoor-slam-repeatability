# Repeatability of Low-Cost Indoor 3D Mapping

Code and data for the article *Repeatability of Low-Cost Indoor 3D Mapping: A TLS-Referenced Evaluation of Six LiDAR Odometry and Mapping Algorithms in Single- and Multi-Level Environments*, submitted to the *Journal of Building
Engineering*.

Six open LiDAR–inertial SLAM algorithms — FAST-LIO2, POINT-LIO, D-LIO, HDMapping-LIO,
LIO-LIVOX and the LiDAR-only baseline KISS-ICP — were run on 25 repeated handheld
captures of two indoor scenarios, and every reconstruction was compared against a
terrestrial laser scanning (TLS) reference. This repository contains the evaluation
pipeline, the analysis scripts, and the run-wise results behind every table, figure and
statistical test in the article and its supplementary material.

**Everything in the article can be regenerated from what is here**, without access to the
raw recordings: the point clouds enter the analysis only through the per-run metric
tables in `data/`, which are included in full.

---

## Quick start

```bash
git clone https://github.com/IGSSCL/low-cost-indoor-slam-repeatability.git
cd low-cost-indoor-slam-repeatability
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd src/analysis
python -W ignore analisis_filtrado.py       # map quality, Tables 3 and 4
python -W ignore analisis_dimensional.py    # dimensional verification, Table 5
python -W ignore analisis_trayectorias.py   # trajectories, Tables S2 and S3
python -W ignore apendiceA.py               # multicriteria index, Tables 7, S11, S12
python -W ignore pareadas.py                # pairwise comparisons, Table S16
python -W ignore fase0.py                   # all recomputations, one report per topic
```

Outputs are written to `out/`, which is not tracked. Nothing else is needed: the scripts
read the tables in `data/` and take a few seconds each, except `fase0.py`, which takes
about a minute.

Reproducing the pipeline **from the point clouds** additionally requires the raw
reconstructions and the TLS references, which are not in this repository — see
*What is not here* below.

---

## Layout

```
data/
  runwise/         one row per map–reference pair: 150 pairs, 147 of them valid
  registration/    the rigid transformation of every pair, with RMS and inlier fraction
  derived/         quantities computed on the clouds: roughness, plumb, slab separation
  reference/       geometry of each scenario measured on the TLS
src/
  pipeline/        registration, filtering and measurement — reads point clouds
  analysis/        statistics, indices and report generation — reads only data/
  scan2bim/        element-level measurements of Section 4.5 and Supplementary S6
  figures/         figure generation
environment/       algorithm parameters and the container images used
docs/              which script produces which table
```

`docs/table-to-script.md` maps every numbered table and figure of the article to the
script that produces it. `data/README.md` is the data dictionary.

---

## Two stages

**The pipeline** (`src/pipeline/`) reads point clouds and writes one JSON line per
map–reference pair. It registers each SLAM cloud to the TLS reference — centroid
matching plus a sweep over 24 yaw hypotheses, then multiscale point-to-point ICP at
correspondence distances of 3.0, 1.0, 0.4 and 0.15 m — voxel-downsamples both clouds to
1 cm, applies the declared filters, and measures accuracy, completeness and coverage at
eight tolerances. Random subsampling uses fixed seeds, so the same inputs give the same
transformation. It is resumable: interrupt it and relaunch, and it continues where it
stopped.

**The analysis** (`src/analysis/`) reads only the tables in `data/` and produces the
article's numbers. It needs no point clouds and runs in seconds.

The separation matters for reproducibility: the expensive, hardware-dependent half is
isolated from the half that produces the published figures, and the interface between
them is a plain text file anyone can inspect.

---

## What is not here

| | Why | How to obtain it |
|---|---|---|
| Raw MCAP/ROS 2 recordings | Hundreds of gigabytes | From the corresponding author, subject to file-size and licence constraints |
| SLAM reconstructions and TLS references (`.pcd`) | Tens of gigabytes | Same |
| Third-party evaluation tools | Each carries its own licence | Cited in `environment/algorithm-parameters.md` |

The per-pair transformations in `data/registration/transforms.csv` are included precisely
so that a reader who obtains the clouds can place any reconstruction in the reference
frame without re-running the registration, and reproduce or contest any measurement
directly.

---

## Software environment

Ubuntu 24.04, ROS 2 Jazzy and Docker, on CPU only — no GPU is used at any stage. Each
algorithm runs in its own container, so the evaluation host needs nothing beyond Docker.
The analysis scripts need only Python and the packages in `requirements.txt`.

`environment/docker-images.md` lists the image of every algorithm. Image tags are
mutable, so that file also records the `sha256` digest of each image, which is not;
`environment/record-digests.sh` regenerates the table on the machine where the images
live.

---

## Citation

If you use this material, please cite the article and the archived record. The exact
fields are in `CITATION.cff`; GitHub and Zenodo both read that file.

## Licence

Code under the MIT licence (`LICENSE`). Data and derived tables under CC BY 4.0
(`LICENSE-DATA.md`). Third-party tools keep their own licences and are not redistributed
here.
