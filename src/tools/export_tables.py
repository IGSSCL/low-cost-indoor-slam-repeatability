# -*- coding: utf-8 -*-
"""Regenerate the CSV views of data/ from the JSON-lines tables written by the pipeline.

    python src/tools/export_tables.py

Writes, from data/runwise/*.jsonl:
  data/runwise/map_quality.csv              (filtered metrics used in the article)
  data/runwise/trajectories.csv
  data/runwise/dimensional_measurements.csv (one row per recovered reference dimension)
  data/registration/transforms.csv          (rigid transformation of every pair)
  data/derived/dimensional_by_axis.json     (horizontal / vertical split, Table S-by-axis)
The CSV files are convenience views; the .jsonl files are the source of truth.
"""
import csv, json, os
import numpy as np

REPO = os.environ.get('SLAM_REPO') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = lambda *p: os.path.join(REPO, 'data', *p)
EXP = {'EXP1': 'Exp 1', 'EXP2': 'Exp 2'}
NAME = lambda a: a.replace('_Denso', '')
ORDER = ['D-LIO', 'FAST-LIO2', 'HDMapping-LIO', 'KISS-ICP', 'LIO-LIVOX', 'POINT-LIO']
key = lambda r: (r['exp'], int(r['run']), NAME(r['algoritmo']))
rd = lambda p: sorted((json.loads(l) for l in open(p, encoding='utf-8')), key=key)


def write(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(header); w.writerows(rows)


def main():
    mq = rd(D('runwise', 'map_quality.jsonl'))
    write(D('runwise', 'map_quality.csv'),
          ['experiment', 'run', 'algorithm', 'converged', 'chamfer_m', 'median_m', 'p95_accuracy_m', 'p99_m',
           'coverage_2cm', 'coverage_5cm', 'registration_rms_m', 'inlier_fraction', 'frac_removed_ror',
           'frac_outside_observed_region'],
          [[EXP[r['exp']], r['run'], NAME(r['algoritmo']), int(r['registro_inliers'] >= 0.05)]
           + [r.get(k, '') for k in ('lim_chamfer_mean_m', 'lim_mediana_m', 'lim_p95_exactitud_m', 'lim_p99_m',
                                     'lim_coverage@0.02', 'lim_coverage@0.05', 'registro_rms_m', 'registro_inliers',
                                     'lim_frac_eliminada_ror', 'lim_frac_fuera_region_observada')]
           for r in mq])
    write(D('registration', 'transforms.csv'),
          ['experiment', 'run', 'algorithm', 'rms_m', 'inlier_fraction', 'converged', 'n_slam_points_voxelised',
           'n_tls_points', 'voxel_m'] + [f'T{i}{j}' for i in range(4) for j in range(4)],
          [[EXP[r['exp']], r['run'], NAME(r['algoritmo']), r['registro_rms_m'], r['registro_inliers'],
            int(r['registro_inliers'] >= 0.05), r.get('n_voxel', ''), r.get('n_gt', ''), r['voxel_m']]
           + [(int(v) if float(v).is_integer() and abs(v) <= 1 and (i == 3) else v)
              for i, row in enumerate(r['T']) for v in row] for r in mq])
    tr = rd(D('runwise', 'trajectories.jsonl'))
    cols = ['L_10hz_m', 'L_cruda_m', 'L_puerta2cm_m', 'cierre_m', 'dZ_m', 'dur_s', 'hz', 'n',
            'v_media_ms', 'v_p95_ms', 'v_sd_ms']
    write(D('runwise', 'trajectories.csv'), ['experiment', 'run', 'algorithm'] + cols,
          [[EXP[r['exp']], r['run'], NAME(r['algoritmo'])] + [r[c] for c in cols] for r in tr])
    dm = rd(D('runwise', 'dimensional.jsonl'))
    write(D('runwise', 'dimensional_measurements.csv'),
          ['experiment', 'run', 'algorithm', 'axis', 'reference_m', 'map_m', 'error_m', 'relative_error'],
          [[EXP[r['exp']], r['run'], NAME(r['algoritmo']), d['eje'], d['dim_TLS_m'], d['dim_SLAM_m'],
            d['error_m'], d['error_rel']] for r in dm for d in r['dimensiones']])
    # horizontal / vertical split. n = recovered measurements; pct = n over the measurements
    # attempted (valid runs x reference dimensions on that axis); med = median over runs of the
    # per-run median absolute error (mm); p95 = pooled 95th percentile (mm)
    NDIM = {'EXP1': {'H': 13, 'V': 1}, 'EXP2': {'H': 10, 'V': 2}}
    out = {}
    for e in ('EXP1', 'EXP2'):
        for a in ORDER:
            rs = [r for r in dm if r['exp'] == e and NAME(r['algoritmo']) == a]
            out[f'{e}|{a}'] = {}
            for g, ejes in (('H', 'XY'), ('V', 'Z')):
                per = [[abs(d['error_m']) * 1000 for d in r['dimensiones'] if d['eje'] in ejes] for r in rs]
                v = [x for p in per for x in p]
                med = [float(np.median(p)) for p in per if p]
                out[f'{e}|{a}'][g] = ({'n': len(v), 'pct': round(100 * len(v) / (len(rs) * NDIM[e][g])),
                                       'med': round(float(np.median(med)), 1),
                                       'p95': round(float(np.percentile(v, 95)), 1)} if v else
                                      {'n': 0, 'pct': 0, 'med': None, 'p95': None})
    json.dump(out, open(D('derived', 'dimensional_by_axis.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
