# -*- coding: utf-8 -*-
"""Run-wise medians used by the figure scripts, read from data/ (registration v2)."""
import json, os
import numpy as np

REPO = os.environ.get('SLAM_REPO') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RUNWISE = os.path.join(REPO, 'data', 'runwise')
ALG = ['POINT-LIO', 'FAST-LIO2', 'HDMapping-LIO', 'D-LIO', 'LIO-LIVOX', 'KISS-ICP']
TAUS_MM = [10, 20, 30, 50, 75, 100, 150, 200]
NAME = lambda a: a.replace('_Denso', '')


def _load(f):
    return [json.loads(l) for l in open(os.path.join(RUNWISE, f), encoding='utf-8')]


def _valid():
    M = {(r['exp'], r['run'], NAME(r['algoritmo'])): r for r in _load('map_quality.jsonl')}
    return M, {k for k, r in M.items() if r['registro_inliers'] >= 0.05}


def trayectorias():
    """{'EXP|ALG': {cv (%), dc (m), dz (m), n valid runs, N runs}} for Figure 3."""
    M, ok = _valid()
    T = {(r['exp'], r['run'], NAME(r['algoritmo'])): r for r in _load('trajectories.jsonl')}
    D = {}
    for e in ('EXP1', 'EXP2'):
        for a in ALG:
            ks = [k for k in M if k[0] == e and k[2] == a]
            v = [k for k in ks if k in ok and k in T]
            L = [T[k]['L_10hz_m'] for k in v]
            D[f'{e}|{a}'] = dict(cv=float(np.std(L, ddof=1) / np.mean(L) * 100),
                                 dc=float(np.median([T[k]['cierre_m'] for k in v])),
                                 dz=float(np.median([T[k]['dZ_m'] for k in v])),
                                 n=len(v), N=len(ks))
    return D


def cobertura():
    """{'EXP|ALG': median coverage at each tolerance of TAUS_MM} for the acceptance curves."""
    M, ok = _valid()
    return {f'{e}|{a}': [float(np.median([M[k][f'lim_coverage@{t / 1000:g}'] for k in ok
                                          if k[0] == e and k[2] == a])) for t in TAUS_MM]
            for e in ('EXP1', 'EXP2') for a in ALG}
