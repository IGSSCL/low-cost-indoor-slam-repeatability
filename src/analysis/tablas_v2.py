#!/usr/bin/env python3
"""Main-text tables with registration v2, as LaTeX rows: map quality (Tables 3 and 4),
dimensional error, trajectory and vertical-range summaries.
Usage (from src/analysis): python -W ignore tablas_v2.py > ../../out/tablas_v2.txt"""
import os, sys, json, itertools
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from paths import repo   # noqa: E402
import apendiceA as A    # noqa: E402  (DELTA = 0.13, levelled frame)
RUNWISE = os.path.join(repo(), "data", "runwise")

V = [json.loads(l) for l in open(os.path.join(RUNWISE, "map_quality.jsonl"))]
D = [json.loads(l) for l in open(os.path.join(RUNWISE, "dimensional.jsonl"))]
ok = [r for r in V if r["registro_inliers"] >= 0.05]
NOM = {"FAST-LIO2_Denso": "FAST-LIO2"}
ORD = ["HDMapping-LIO", "POINT-LIO", "LIO-LIVOX", "FAST-LIO2_Denso", "D-LIO", "KISS-ICP"]


def q(v, d=2):
    a = np.percentile(v, [25, 50, 75]); f = f"{{:.{d}f}}"
    return f"{f.format(a[1])} [{f.format(a[0])},{f.format(a[2])}]"


print("=== Tables 4 and 5 - map quality (ordered by D_bi)")
for e in ("EXP1", "EXP2"):
    filas = []
    for a in ORD:
        rs = [r for r in ok if r["exp"] == e and r["algoritmo"] == a]
        filas.append((np.median([r["lim_chamfer_mean_m"] for r in rs]), a, rs))
    for _, a, rs in sorted(filas):
        c = lambda k, m=100, d=2: q([r[k] * m for r in rs], d)
        print(f"{NOM.get(a, a)} & {len(rs)} & {c('lim_chamfer_mean_m')} & {c('lim_mediana_m')} & "
              f"{c('lim_p95_exactitud_m')} & {c('lim_p99_m', 100, 1)} & {c('lim_coverage@0.02', 1)} & "
              f"{c('lim_coverage@0.05', 1)} & {np.median([r['registro_rms_m'] for r in rs])*100:.2f}\\\\")
    print()

print("=== Table 6 - dimensional error")
for e, nref in (("EXP1", 14), ("EXP2", 12)):
    filas = []
    for a in ORD:
        rs = [r for r in D if r["exp"] == e and r["algoritmo"] == a and "dimensiones" in r]
        err = np.array([abs(x["error_m"]) for r in rs for x in r["dimensiones"]]) * 1000
        med = [r["error_abs_mediano_m"] * 1000 for r in rs if r.get("n_dimensiones", 0) > 0]
        filas.append((np.median(med), a, rs, err, med))
    for _, a, rs, err, med in sorted(filas, key=lambda x: x[0]):
        print(f"{e[-1]} & {NOM.get(a, a)} & {len(err)} & {len(err)/(nref*len(rs))*100:.0f} & {q(med, 1)} & "
              f"{np.percentile(err, 95):.1f} & {np.mean(err <= 15)*100:.0f} & {np.mean(err <= 50)*100:.0f}\\\\")
    print()

print("=== Ranges quoted in the text")
for e in ("EXP1", "EXP2"):
    m = [np.median([r["lim_mediana_m"] for r in ok if r["exp"] == e and r["algoritmo"] == a]) for a in ORD]
    c5 = [np.median([r["lim_coverage@0.05"] for r in ok if r["exp"] == e and r["algoritmo"] == a]) for a in ORD]
    p = [np.median([r["lim_p95_exactitud_m"] for r in ok if r["exp"] == e and r["algoritmo"] == a]) for a in ORD]
    print(e, "mediana %.2f-%.2f cm" % (min(m) * 100, max(m) * 100), "cov5 %.2f-%.2f" % (min(c5), max(c5)),
          "P95acc %.2f-%.2f cm" % (min(p) * 100, max(p) * 100))
for a in ORD:
    for e in ("EXP1", "EXP2"):
        v = sorted(r["lim_p95_exactitud_m"] * 100 for r in ok if r["exp"] == e and r["algoritmo"] == a)
        print(e, a, "P95acc min-max %.1f-%.1f" % (v[0], v[-1]))

print("\n=== Multicriterio (apendiceA con v2)")
out = {e: dict(R=A.R(e), Q=A.Q(e), C=A.C(e)) for e in ("EXP1", "EXP2")}
w = np.array([0.30, 0.50, 0.20])
for a in A.ALG:
    s = []
    for e in ("EXP1", "EXP2"):
        r, qq, c = out[e]["R"][a], out[e]["Q"][a], out[e]["C"][a]
        s += [r, qq, c, 0.3 * r + 0.5 * qq + 0.2 * c]
    print(f"{a} & " + " & ".join(f"{x:.3f}" for x in s) + f" & {(s[3]+s[7])/2:.3f}\\\\")


def indice(algs, ww=(0.30, 0.50, 0.20)):
    keep = A.ALG
    A.ALG = algs
    try:
        o = {e: dict(R=A.R(e), Q=A.Q(e), C=A.C(e)) for e in ("EXP1", "EXP2")}
    finally:
        A.ALG = keep
    return {a: np.mean([ww[0] * o[e]["R"][a] + ww[1] * o[e]["Q"][a] + ww[2] * o[e]["C"][a] for e in o]) for a in algs}


print("\n=== Escenarios de pesos (agregado)")
for n, ww in {"Base": (.30, .50, .20), "Uniform": (1/3, 1/3, 1/3), "Balanced": (.40, .40, .20), "Efficiency": (.30, .30, .40)}.items():
    s = indice(A.ALG, ww)
    print(n, " > ".join(f"{a} {s[a]:.3f}" for a in sorted(s, key=lambda a: -s[a])))
print("\n=== Quitar una alternativa (orden)")
base = indice(A.ALG)
print("ninguna", " > ".join(sorted(base, key=lambda a: -base[a])))
for x in A.ALG:
    s = indice([a for a in A.ALG if a != x])
    print("sin", x, " > ".join(f"{a} {s[a]:.3f}" for a in sorted(s, key=lambda a: -s[a])))
