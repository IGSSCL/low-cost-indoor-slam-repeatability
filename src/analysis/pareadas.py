# -*- coding: utf-8 -*-
"""Comparaciones pareadas de Wilcoxon con correccion de Holm y p ajustados exactos.
Produce la Tabla B.24 del manuscrito. Uso: python pareadas.py (desde reproceso_geometrico)."""
import json, os, itertools
import numpy as np
from scipy import stats

from paths import raiz
AQUI = raiz()
os.makedirs(os.path.join(AQUI,'recalculos'), exist_ok=True)
ALG  = ['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS = {'EXP1':[str(i) for i in range(1,14)], 'EXP2':[str(i) for i in range(1,13)]}
MET  = [('lim_chamfer_mean_m','Chamfer'), ('lim_p95_exactitud_m','P95acc'),
        ('lim_coverage@0.02','Cov@2cm')]

M = {}
for l in open(os.path.join(AQUI,'resultados_con_filtrado.jsonl'), encoding='utf-8'):
    r = json.loads(l)
    M[(r['exp'], r['run'], r['algoritmo'].replace('_Denso',''))] = r

def ok(e, r, a):
    x = M.get((e,r,a))
    return x is not None and x.get('registro_inliers',0) >= 0.05 and 'lim_mediana_m' in x

def holm(ps):
    ps = np.asarray(ps,float); n = len(ps); idx = np.argsort(ps)
    adj = np.empty(n); run = 0.0
    for i,j in enumerate(idx):
        run = max(run, (n-i)*ps[j]); adj[j] = min(1.0, run)
    return adj

L = ["# Comparaciones pareadas — Wilcoxon signed-rank + Holm", ""]
for e in ('EXP1','EXP2'):
    for k, tit in MET:
        filas, ps = [], []
        for a,b in itertools.combinations(ALG,2):
            rr = [r for r in RUNS[e] if ok(e,r,a) and ok(e,r,b)]
            x = np.array([M[(e,r,a)][k] for r in rr])
            y = np.array([M[(e,r,b)][k] for r in rr])
            d = x - y
            if np.all(d == 0):
                p, rb = 1.0, 0.0
            else:
                p = stats.wilcoxon(x, y, zero_method='wilcox').pvalue
                nz = d[d != 0]; rk = stats.rankdata(np.abs(nz))
                rb = (rk[nz>0].sum() - rk[nz<0].sum()) / rk.sum()   # rank-biserial pareado
            filas.append((a,b,len(rr),p,rb)); ps.append(p)
        adj = holm(ps)
        sig = int(sum(1 for q in adj if q < 0.05))
        L += ["", f"## {e} — {tit}: {sig}/15 significativos",
              f"p ajustado minimo alcanzable: {min(adj):.2e}", "",
              "| Par | n | rho rank-biserial | p crudo | p ajustado | Separa |",
              "|---|---|---|---|---|---|"]
        for (a,b,n,p,rb), q in sorted(zip(filas,adj), key=lambda t: t[1]):
            L.append(f"| {a}–{b} | {n} | {rb:+.2f} | {p:.4f} | {q:.3f} | "
                     f"{'si' if q<0.05 else '**no**'} |")
out = os.path.join(AQUI,'recalculos','0h_pareadas.md')
open(out,'w',encoding='utf-8').write("\n".join(L)+"\n")
print("escrito", out)
