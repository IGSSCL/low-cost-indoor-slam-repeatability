# Data dictionary

Every file here is either a direct output of the evaluation pipeline or a quantity
derived from the point clouds. Nothing was edited by hand.

Six algorithms × 25 captures = 150 map–reference pairs. Three executions diverged and
are excluded from the statistics, leaving **147 valid pairs**; the diverged rows are kept
so the failures remain visible. In the tables the diverging algorithm is
`FAST-LIO2_Denso` in the `.jsonl` files and `FAST-LIO2` in the `.csv` files — the same
algorithm under the name its container exported.

Distances are in metres unless a column name says otherwise. `Exp 1` is the single-floor
scenario (297 m², 13 repetitions); `Exp 2` is the multi-level one (160 + 180 m² over two
storeys, 12 repetitions).

---

## `runwise/` — one row per map–reference pair

### `map_quality.csv` / `map_quality.jsonl`

The metrics behind Tables 3 and 4. The `.jsonl` carries every field the pipeline wrote;
the `.csv` is the subset used in the article.

| Column | Meaning |
|---|---|
| `converged` | 1 if the pair is one of the 147 valid ones. A pair is invalid when the inlier fraction of the rigid registration falls below 0.05, meaning no rigid transformation brings map and reference into correspondence |
| `chamfer_m` | Mean of the two directional mean distances. Not the symmetric set-to-set distance of the conventional definition: the two directions are evaluated against different versions of the cloud (see below) |
| `median_m`, `p95_accuracy_m`, `p99_m` | Percentiles of the map-to-reference distance |
| `coverage_2cm`, `coverage_5cm` | Fraction of reference points with a map point within that tolerance |
| `registration_rms_m` | RMS of the final ICP alignment, over correspondences inside the 15 cm gate on the unfiltered cloud. **Not comparable term by term** with the error columns, which come from the filtered and masked cloud |
| `inlier_fraction` | Fraction of points inside that gate |
| `frac_removed_ror` | Fraction removed by the grid radius-outlier filter |
| `frac_outside_observed_region` | Fraction excluded by the observed-region mask |

Fields prefixed `lim_` in the `.jsonl` are the filtered versions; the unprefixed ones are
computed before filtering. **The article uses the filtered ones.**

The filtering is asymmetric by design: the accuracy direction (map → reference) is
evaluated on the filtered and masked cloud, and the completeness direction
(reference → map) against the unfiltered cloud. Section 3.4 of the article explains why,
and states that the choice is not neutral.

### `dimensional.jsonl` / `dimensional_measurements.csv`

1235 measurements of 26 distinct reference dimensions — 14 in Experiment 1, 12 in
Experiment 2 — each recovered independently in every run of every algorithm. A dimension
is the distance between two parallel dominant planes at least 1 m apart, which is
invariant under the rigid registration and therefore does not inherit its error.

`axis` is `X`, `Y` or `Z`. Thirteen of the fourteen dimensions of Experiment 1 are
horizontal and one is a clear height; ten of the twelve of Experiment 2 are horizontal
and two are clear heights.

**The matching is censored.** A reference plane whose counterpart in the map is displaced
by more than the 12 cm tolerance produces no pairing and no row. Absence of a row is a
failure of recovery, not a small error, and recovery ranges from 50 % to 74 % across
algorithms. Any statistic computed here describes the geometry an algorithm recovered.

### `trajectories.csv` / `trajectories.jsonl`

| Column | Meaning |
|---|---|
| `L_cruda_m` | Trajectory length as exported |
| `L_10hz_m` | Length after resampling every trajectory to 10 Hz — **the comparable one**, since D-LIO exports at about 101 Hz and the rest at 10 Hz |
| `L_puerta2cm_m` | Length after additionally gating displacements below 2 cm, which removes tremor |
| `dZ_m` | Vertical range of the trajectory. In Experiment 1 the route has no level change, so its expected value is the vertical excursion of a handheld sensor, about 0.25 m. In Experiment 2 the reference is the storey height measured on the TLS, 3.15 m |
| `cierre_m` | Distance between the first and last pose |
| `v_media_ms`, `v_p95_ms`, `v_sd_ms` | Walking speed |
| `dur_s`, `hz`, `n` | Duration, export rate, number of poses |

### `computational.csv`

Wall-clock time, accumulated CPU cost in core-seconds (duration × mean load, so that
algorithms with different degrees of parallelisation are comparable) and peak resident
memory, measured by each algorithm's container. Median over the repetitions. Behind
Table 6 and the $C_a$ subindex.

---

## `registration/transforms.csv`

The 4×4 rigid transformation that places each SLAM reconstruction in the reference frame,
with the RMS and inlier fraction of its alignment. Row-major: `T00 … T33`.

This is what lets a reader who obtains the point clouds place any reconstruction in the
reference frame without re-running the registration, and reproduce or contest any
measurement. Applying it is `Q = P @ T[:3,:3].T + T[:3,3]`.

Coarse alignment combined centroid matching with a sweep over 24 yaw hypotheses; fine
alignment used point-to-point ICP over correspondence distances of 3.0, 1.0, 0.4 and
0.15 m, at most 30 iterations per scale, convergence at an RMS change below 1e-5 m.
Random subsampling used fixed seeds, so the same inputs give the same transformation.

---

## `derived/` — element-level measurements

Computed on the reconstructions at native resolution, over three repetitions per
algorithm and scenario: runs 1, 8 and 13 of Experiment 1 and runs 3, 9 and 11 of
Experiment 2.

| File | Content |
|---|---|
| `roughness_exp1.json`, `roughness_exp2.json` | Local roughness of the dominant horizontal slabs, in millimetres: within a 5 cm band around each slab the cloud is divided into 0.5 m cells and the height residual in each cell is summarised by 1.4826·MAD; the value reported is the median over cells. `celdas` is how many cells met the minimum of 40 points, and it differs by an order of magnitude between algorithms |
| `roughness_sensitivity.json` | The same quantity for band widths of 3, 5 and 8 cm and cell sizes of 0.25, 0.5 and 1.0 m |
| `plumb_exp1.json` | Inclination of each wall face from the vertical, by principal components over a 2.2 m height band, against the inclination measured on the reference |
| `slab_separation.json` | Separation between the two dominant horizontal slabs of each reconstruction, against 4.270 m in Experiment 1 and 3.150 m in Experiment 2 |
| `dimensional_by_axis.json` | The dimensional error of Table 5 split into horizontal and vertical dimensions |
| `multicriteria_full.json` | Subindices, weighted sum, TOPSIS, VIKOR and the sensitivity scenarios |

**Roughness has no baseline, and cannot have one here.** The TLS reference is delivered
resampled onto a 1 cm grid — within a 10 cm band around the floor of Experiment 1 its
319,897 points take only ten distinct height values — so applying the same procedure to
the reference returns 0.00 mm. The absolute values therefore confound the fidelity of a
reconstruction with whatever internal smoothing each implementation applies to its map,
and the leading values lie below the 2 cm range precision the sensor is specified at.
They support a comparison between reconstructions of the same surface, not a distance
from a true surface.

---

## `reference/` — scenario geometry measured on the TLS

| File | Content |
|---|---|
| `scenario_geometry_exp1.json`, `scenario_geometry_exp2.json` | Bounding box of the evaluated region and the height of the dominant floor and ceiling planes |
| `wall_faces_exp1.json` | The twenty wall faces of Experiment 1 with their position, true inclination and fit residual |

---

## What is not here

The raw MCAP/ROS 2 recordings and the full-resolution SLAM and TLS point clouds are
tens to hundreds of gigabytes and are available from the corresponding author on
reasonable request, subject to file-size and licence constraints. Everything the article
reports is derived from the tables above.
