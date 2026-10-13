# -*- coding: utf-8 -*-
"""Sensitivity of the multicriteria ranking reported in Supplementary Section S7.

  1. Reduced Q_a: four metrics instead of five (median error, P95_acc, coverage at 2 cm,
     median dimensional error), one per aspect: central tendency, tail, completeness and
     dimensional fidelity. R_a and C_a unchanged; base weights 0.30/0.50/0.20.
  2. Leave-one-out: each algorithm removed in turn and the index recomputed from scratch,
     since min-max normalisation depends on which alternatives are present.
  3. Redundancy inside Q_a: Spearman correlations between its metrics over the twelve
     algorithm-scenario medians.

    python -W ignore sensibilidad_qa.py
"""
import numpy as np
from scipy.stats import spearmanr
import apendiceA as A

W = np.array([0.30, 0.50, 0.20])


def nrm(c, mm):
    c = np.array(c, float); lo, hi = np.nanmin(c), np.nanmax(c)
    return np.ones_like(c) * 0.5 if hi - lo < 1e-15 else ((c - lo) / (hi - lo) if mm else (hi - c) / (hi - lo))


def indice(alg, q_metricas):
    """Aggregate score over the two scenarios for the alternatives in `alg`."""
    def sub(cols):
        return dict(zip(alg, np.mean(cols, axis=0)))
    S = {a: 0.0 for a in alg}
    for e in ('EXP1', 'EXP2'):
        Q = sub([nrm([A.med(e, a, k, s) for a in alg], up) for k, s, up in q_metricas])
        R = sub([nrm([A.cvL(e, a) for a in alg], False),
                 nrm([A.med(e, a, 'cierre_m', 'T') for a in alg], False),
                 nrm([abs(A.med(e, a, 'dZ_m', 'T') - (A.EP if e == 'EXP2' else A.DELTA)) for a in alg], False)])
        C = sub([nrm([A.EFF[e][a][i] for a in alg], False) for i in range(3)])
        for a in alg:
            S[a] += 0.5 * (W[0] * R[a] + W[1] * Q[a] + W[2] * C[a])
    return S


Q5 = [('lim_chamfer_mean_m', 'M', False), ('lim_p95_exactitud_m', 'M', False), ('lim_p99_m', 'M', False),
      ('lim_coverage@0.02', 'M', True), ('error_abs_mediano_m', 'D', False)]
Q4 = [('lim_mediana_m', 'M', False), ('lim_p95_exactitud_m', 'M', False),
      ('lim_coverage@0.02', 'M', True), ('error_abs_mediano_m', 'D', False)]


def fmt(S):
    return ', '.join(f'{a} {S[a]:.3f}' for a in sorted(S, key=lambda a: -S[a]))


if __name__ == '__main__':
    print('Base index (five-metric Q_a):  ', fmt(indice(A.ALG, Q5)))
    print('Reduced Q_a (four metrics):    ', fmt(indice(A.ALG, Q4)))
    print('\nLeave-one-out (five-metric Q_a):')
    base = sorted(A.ALG, key=lambda a: -indice(A.ALG, Q5)[a])
    for x in A.ALG:
        alg = [a for a in A.ALG if a != x]
        S = indice(alg, Q5)
        orden = sorted(alg, key=lambda a: -S[a])
        igual = orden == [a for a in base if a != x]
        print(f'  without {x:14s} {"same order " if igual else "ORDER CHANGES"}  {fmt(S)}')
    print('\nSpearman correlations between Q_a metrics (12 algorithm-scenario medians):')
    v = {k: [A.med(e, a, k, s) for e in ('EXP1', 'EXP2') for a in A.ALG] for k, s, _ in Q5}
    for x, y in [('lim_chamfer_mean_m', 'lim_p99_m'), ('lim_chamfer_mean_m', 'lim_coverage@0.02'),
                 ('lim_p95_exactitud_m', 'lim_p99_m')]:
        print(f'  {x} vs {y}: rho = {spearmanr(v[x], v[y])[0]:+.2f}')
