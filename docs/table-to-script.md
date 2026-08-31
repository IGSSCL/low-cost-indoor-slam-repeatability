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

| Table | Content | Produced by |
|---|---|---|
| 1 | Related work | manual |
| 2 | Algorithms, map representation and configuration | manual — see `environment/algorithm-parameters.md` |
| 3 | Map quality, Experiment 1, run-wise | `fase0.py` → `out/recalculos/0a_runwise.md` |
| 4 | Map quality, Experiment 2, run-wise | `fase0.py` → `out/recalculos/0a_runwise.md` |
| 5 | Dimensional error | `analisis_dimensional.py` |
| 6 | Computational cost | pipeline — `data/runwise/computational.csv` |
| 7 | Multicriteria scores by scenario and aggregate | `apendiceA.py` |
| 8 | Admissible set by success threshold | `apendiceA.py`, Wilson intervals in `fase0.py` → `0d_umbral.md` |
| 9 | USIBD Level of Accuracy bands | manual — USIBD C120 v2.0 |
| 10 | Equipment cost | manual — distributor price levels, early 2026 |
| 11 | Acquisition effort | manual — field records |
| 12 | Selection guide | manual |

| Figure | Content | Produced by |
|---|---|---|
| 1 | Methodology pipeline | `src/figures/fig01_pipeline.py` |
| 2 | Platform and runtime | `src/figures/fig02_platform.py` |
| 3 | Trajectory repeatability, four panels | `src/figures/fig03_trajectory_repeatability.py` |
| 4, 7 | Map overviews | pipeline — rendered from the registered clouds |
| 5, 8 | Tripartite map/reference/error views | pipeline — rendered from the registered clouds |
| 6 | Acceptance curves | `src/figures/fig_acceptance_curves.py` |
| 9 | Quality against CPU cost | `src/figures/` — see the script header |

Set `SLAM_FIGDIR` to choose where the figure scripts write; the default is the current
directory.

---

## Supplementary material

| Table | Content | Produced by |
|---|---|---|
| S1 | Fraction removed by each preprocessing step | `analisis_filtrado.py` |
| S2, S3 | Trajectory repeatability, both scenarios | `analisis_trayectorias.py` |
| S4 | Success rates and failure modes | `fase0.py` → `0d_umbral.md` |
| S5 | Weighted sum, TOPSIS and VIKOR | `apendiceA.py` |
| S6 | Local roughness of the dominant slabs | `src/scan2bim/agrega.py` |
| S7 | Wall verticality | `src/scan2bim/medir.py` |
| S8 | Dimensional error by axis | `analisis_dimensional.py`; the split is in `data/derived/dimensional_by_axis.json` |
| S9 | Reconstructed slab separation | `src/scan2bim/alturas.py` |
| S10 | Sensitivity of the roughness figures | `src/scan2bim/sensib_rugosidad.py` |
| S11, S12 | Weighting scenarios and resulting ranks | `apendiceA.py` |
| S13, S14 | Representative-run map quality | `fase0.py` → `0a_runwise.md` |
| S15 | Skillings–Mack statistics | `analisis.py` |
| S16 | Pairwise Wilcoxon with Holm correction | `pareadas.py` |

| Figure | Content | Produced by |
|---|---|---|
| S1, S2 | Visual summary of the map–TLS comparison | pipeline — rendered from the registered clouds |

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
| `0a_runwise.md` | Run-wise map quality — Tables 3, 4, S13 and S14 |
| `0b_dimensional.md` | Dimensional verification over the full batch |
| `0c_filtrado.md` | Effect of the declared filtering on every metric |
| `0d_umbral.md` | Success thresholds, Wilson intervals and the admissible set |
| `0e_leaveoneout.md` | Stability of the ranking when each alternative is removed |
| `0f_velocidad.md` | Walking speed against map quality, with Holm correction |
| `0g_deltaz.md` | Vertical range against the measured storey height |
| `0h_pareadas.md` | Pairwise comparisons — Table S16 |
