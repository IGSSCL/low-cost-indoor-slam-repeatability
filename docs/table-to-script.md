# Which script produces which table

Every numbered table and figure of the article and its supplementary material, and where
it comes from. Run the analysis scripts from `src/analysis/`; outputs land in `out/`.

Three sources appear in the last column:

- **script** — regenerated from `data/` by the script named;
- **pipeline** — produced by `src/pipeline/` from the point clouds, and already recorded
  in `data/`, so the analysis does not need to re-run it;
- **manual** — assembled by the authors from the literature, a published standard, or
  supplier quotations, with no computation over the study's data.

---

## Main text

Numbering as in the submitted manuscript (13 tables, 8 figures). Analysis scripts are in
`src/analysis/`, figure scripts in `src/figures/`.

| Table | Content | Produced by |
|---|---|---|
| 1 | Related work | manual |
| 2 | Algorithms, map representation and configuration | manual — see `environment/algorithm-parameters.md` |
| 3 | Output frame and vertical range of the trajectory | `suplemento_v2.py` (section "Tables 3 and S19"); data in `data/derived/frame_levelling.json` |
| 4 | Map quality, Experiment 1, run-wise | `tablas_v2.py` (section "Tables 4 and 5") |
| 5 | Map quality, Experiment 2, run-wise | `tablas_v2.py` (section "Tables 4 and 5") |
| 6 | Dimensional error | `tablas_v2.py` (section "Table 6"); `analisis_dimensional.py` for the full report |
| 7 | Computational cost | pipeline — `data/runwise/computational.csv` |
| 8 | Multicriteria subindices and aggregate score | `apendiceA.py` |
| 9 | Performance profiles | manual — synthesis of Tables 3–8 |
| 10 | USIBD Level of Accuracy bands | manual — USIBD C120 v2.0 |
| 11 | Selection guide by dominant constraint | manual |
| 12 | Equipment cost | manual — public list prices, see Supplementary Section S11 |
| 13 | Field acquisition effort | manual — field records; SLAM capture durations from `dur_s` in `data/runwise/trajectories.jsonl` |

| Figure | Content | Produced by |
|---|---|---|
| 1 | Methodological workflow and acquisition platform | image composed by the authors |
| 2 | Processing and evaluation pipeline | image composed by the authors |
| 3 | Trajectory repeatability, levelled vertical range and success rate | `fig03_trajectory_repeatability.py` |
| 4, 5 | Representative map overviews, Experiments 1 and 2 | `vista.py` / `vista_fig.py` — need the registered clouds |
| 6 | Acceptance curves | `fig_acceptance_curves.py` |
| 7 | Map/reference/error views, LIO-LIVOX, Experiment 2 | pipeline — rendered from the registered clouds |
| 8 | Quality against CPU cost, with Pareto front | `fig_quality_cost.py` |

The figure scripts write to the directory named by `SLAM_FIGDIR` (default: the current
one) and read the run-wise medians through `src/figures/datos_v2.py`.

---

## Supplementary material

| Table | Content | Produced by |
|---|---|---|
| S1 | Fraction removed by each preprocessing step | `suplemento_v2.py` |
| S2, S3 | Trajectory repeatability, both scenarios | `suplemento_v2.py`; `analisis_trayectorias.py` for the effect of resampling to 10 Hz |
| S4 | Success rates and failure modes | `fase0.py` → `0d_umbral.md` |
| S5 | Weighted sum, TOPSIS and VIKOR | `suplemento_v2.py`, or `apendiceA.py` |
| S6 | Local roughness of the dominant slabs | `data/derived/roughness_exp*.json` — `src/scan2bim/agrega.py`, updated by `scan2bim_v2.py` |
| S7 | Wall verticality | `src/scan2bim/medir.py` → `data/derived/plumb_exp1.json` |
| S8 | Dimensional error by axis | `src/tools/export_tables.py` → `data/derived/dimensional_by_axis.json` |
| S9 | Reconstructed slab separation | `data/derived/slab_separation.json` — `src/scan2bim/alturas.py`, updated by `scan2bim_v2.py` |
| S10 | Sensitivity of the roughness figures | `src/scan2bim/sensib_rugosidad.py` |
| S11 | Weighting scenarios | manual |
| S12 | Scores and ranks under each weighting scenario | `suplemento_v2.py`, or `apendiceA.py` |
| S13 | Admissible set by success threshold | `fase0.py` → `0d_umbral.md` |
| S14, S15 | Representative-run map quality | `suplemento_v2.py` |
| S16 | Skillings–Mack statistics | `suplemento_v2.py`, or `analisis.py` |
| S17 | Pairwise Wilcoxon with Holm correction | `suplemento_v2.py` (summary), `pareadas.py` (full) |
| S18 | Spatial hold-out of the registration | `suplemento_v2.py`; data from `src/pipeline/holdout.py` in `data/registration/holdout.jsonl` |
| S19 | Output-frame tilt and vertical range | `suplemento_v2.py` |
| S20, S21 | Walking speed against $D_{bi}$ and $P95_{acc}$ | `fase0.py` → `0f_velocidad.md` |

Section S7 also reports a reduced $Q_a$, a leave-one-out check and the correlations
between the $Q_a$ metrics: `sensibilidad_qa.py`.

| Figure | Content | Produced by |
|---|---|---|
| S1, S2 | Visual summary of the map–TLS comparison | pipeline — rendered from the registered clouds |

---

## The registration (version 1.1.0)

Version 1.1.0 levels every map before registering it. The pipeline scripts that produced
the published tables need the point clouds and the TLS references, placed in a folder
named by `SLAM_DATA` (`EXP 1/Nubes de puntos`, `EXP 2/Nubes de punto`, `tls_e1.npy`,
`tls_e2.npy`):

```bash
export SLAM_DATA=/path/to/clouds
cd src/pipeline
python reg_v2.py todo        # levelling + registration + metrics -> out/map_quality_v2.jsonl
python dim_v2.py auto        # dimensional verification            -> out/dimensional_v2.jsonl
python holdout.py todo       # spatial hold-out                    -> out/holdout_v2.jsonl
cd ../scan2bim
python scan2bim_v2.py        # roughness and slab separation for the pairs whose registration changed
```

`reg_v2.py` and `holdout.py` are resumable (`auto [seconds]` advances in steps). Their
outputs are what `data/runwise/map_quality.jsonl`, `data/runwise/dimensional.jsonl` and
`data/registration/holdout.jsonl` contain; `python src/tools/export_tables.py` then
regenerates the CSV views. `motion_profile.py` computes the motion descriptors used to
select the representative repetition.

---

## The element-level scripts

The scripts in `src/scan2bim/` read the reconstructions at native resolution, so they
need the point clouds. They run in two steps, because a full-resolution read of the
larger reconstructions does not fit in a short-lived process:

```bash
export SLAM_DATA=/path/to/folder/containing/"EXP 1"/and/"EXP 2"
cd src/scan2bim
python corre.py  <algorithm> <run>   # Experiment 1: caches the band around each slab
python corre2.py <algorithm> <run>   # Experiment 2: same
python agrega.py                     # Table S6, roughness
python alturas.py                    # Table S9, slab separation
python sensib_rugosidad.py           # Table S10, sensitivity
python medir.py EXP1 8               # Table S7, wall plumb
```

The band caches are written next to the scripts as `band_<run>_<algorithm>.npy` and
`e2band_<run>_<algorithm>.npy`. The published tables use runs 1, 8 and 13 of
Experiment 1 and runs 3, 9 and 11 of Experiment 2.

---

## Recomputations

`fase0.py` produces one report per topic in `out/recalculos/`, and a `RESUMEN.md` that
collects them:

| File | Content |
|---|---|
| `0a_runwise.md` | Run-wise map quality — Tables 4, 5, S14 and S15 |
| `0b_dimensional.md` | Dimensional verification over the full batch |
| `0c_filtrado.md` | Effect of the declared filtering on every metric |
| `0d_umbral.md` | Success thresholds, Wilson intervals and the admissible set |
| `0e_leaveoneout.md` | Stability of the ranking when each alternative is removed |
| `0f_velocidad.md` | Walking speed against map quality, with Holm correction |
| `0g_deltaz.md` | Vertical range against the measured storey height |
| `0h_pareadas.md` | Pairwise comparisons — Table S17 |

`0e_leaveoneout.md` keeps the index formulation of version 1.0. The multicriteria index,
the leave-one-out check and the reduced $Q_a$ reported in the article are those of
`apendiceA.py` and `sensibilidad_qa.py`.
