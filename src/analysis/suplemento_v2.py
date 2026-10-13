# -*- coding: utf-8 -*-
"""Supplementary tables with registration v2, as LaTeX rows: preprocessing (S1),
TOPSIS/VIKOR, weighting scenarios, representative runs, Skillings-Mack, pairwise Wilcoxon-Holm,
output frames and the spatial hold-out of the registration.
Usage (from src/analysis): python -W ignore suplemento_v2.py > ../../out/suplemento_v2.txt"""
import os, sys, json, itertools, collections
import numpy as np
AQUI=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,AQUI)
from paths import repo
import analisis as AN
import apendiceA as A
DATA=os.path.join(repo(),'data')
V=[json.loads(l) for l in open(os.path.join(DATA,'runwise','map_quality.jsonl'))]
N=lambda a:a.replace('_Denso','')
ok=[r for r in V if r['registro_inliers']>=0.05]
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
print('=== Table S1 - preprocessing')
for e in ('EXP1','EXP2'):
    for a in ALG:
        rs=[r for r in ok if r['exp']==e and N(r['algoritmo'])==a]
        m=lambda k: np.median([r[k] for r in rs])
        print(f"{e[-1]} & {a} & {m('frac_fuera_del_TLS')*100:.2f} & {m('lim_frac_eliminada_ror')*100:.2f} & {m('lim_frac_fuera_region_observada')*100:.2f} & {m('registro_inliers'):.3f}\\\\")
print('=== Table S5 - weighted sum, TOPSIS, VIKOR')
o={e:dict(R=A.R(e),Q=A.Q(e),C=A.C(e)) for e in ('EXP1','EXP2')}
AG={k:{a:0.5*(o['EXP1'][k][a]+o['EXP2'][k][a]) for a in A.ALG} for k in 'RQC'}
Mx=np.array([[AG['R'][a],AG['Q'][a],AG['C'][a]] for a in A.ALG]); w=np.array([.3,.5,.2])
S=Mx@w; tp=A.topsis(Mx,w); vk=A.vikor(Mx,w)
rk=lambda v,up: {a:i+1 for i,a in enumerate(sorted(A.ALG,key=lambda a:-v[A.ALG.index(a)] if up else v[A.ALG.index(a)]))}
r1,r2,r3=rk(S,True),rk(tp,True),rk(vk,False)
for a in sorted(A.ALG,key=lambda a:r1[a]):
    i=A.ALG.index(a); print(f"{a} & {S[i]:.3f} & {r1[a]} & {tp[i]:.3f} & {r2[a]} & {vk[i]:.3f} & {r3[a]}\\\\")
print('=== Table S12 - weighting scenarios')
esc=[(.30,.50,.20),(1/3,1/3,1/3),(.40,.40,.20),(.30,.30,.40)]
cols=[]
for ww in esc:
    s=Mx@np.array(ww); cols.append((s,{a:i+1 for i,a in enumerate(sorted(A.ALG,key=lambda a:-s[A.ALG.index(a)]))}))
for a in sorted(A.ALG,key=lambda a:cols[0][1][a]):
    i=A.ALG.index(a); print(f"{a} & "+" & ".join(f"{s[i]:.3f} & {r[a]}" for s,r in cols)+"\\\\")
print('=== Tables S14/S15 - representative runs')
for e,run in (('EXP1','8'),('EXP2','9')):
    for r in sorted([r for r in ok if r['exp']==e and r['run']==run],key=lambda r:r['lim_chamfer_mean_m']):
        print(f"{N(r['algoritmo'])} & {r['lim_chamfer_mean_m']*100:.2f} & {r['lim_mediana_m']*100:.2f} & {r['lim_p95_exactitud_m']*100:.2f} & {r['lim_p99_m']*100:.1f} & {r['lim_coverage@0.02']:.3f} & {r['lim_coverage@0.05']:.3f} & {r['registro_rms_m']*100:.2f}\\\\")
print('=== Table S16 - Skillings-Mack')
for e in ('EXP1','EXP2'):
    for k,n in (('lim_chamfer_mean_m','D_bi'),('lim_mediana_m','Median'),('lim_p95_exactitud_m','P95acc'),('lim_p99_m','P99'),('lim_coverage@0.02','Cov2'),('lim_coverage@0.05','Cov5')):
        T,df,p=AN.skillings_mack(e,k); print(e,n,f"{T:.2f} & {df} & {p:.2e}")
print('=== Table S17 - pairwise Wilcoxon-Holm (summary)')
from scipy import stats
def holm(ps):
    ps=np.asarray(ps,float); n=len(ps); idx=np.argsort(ps); adj=np.empty(n); run=0.0
    for i,j in enumerate(idx): run=max(run,(n-i)*ps[j]); adj[j]=min(1.0,run)
    return adj
M={(r['exp'],r['run'],N(r['algoritmo'])):r for r in ok}
for e in ('EXP1','EXP2'):
    for k,n in (('lim_chamfer_mean_m','D_bi'),('lim_p95_exactitud_m','P95acc'),('lim_coverage@0.02','Cov2')):
        fil=[];ps=[]
        for a,b in itertools.combinations(ALG,2):
            rr=[r for r in AN.RUNS[e] if (e,r,a) in M and (e,r,b) in M]
            x=np.array([M[(e,r,a)][k] for r in rr]); y=np.array([M[(e,r,b)][k] for r in rr])
            p=1.0 if np.all(x==y) else stats.wilcoxon(x,y).pvalue
            fil.append((a,b)); ps.append(p)
        adj=holm(ps)
        ns=[f"{a}--{b} ({q:.3f})" for (a,b),q in sorted(zip(fil,adj),key=lambda t:t[1]) if q>=0.05]
        print(e,n,f"{sum(adj<0.05)}/15",'; '.join(ns) or '---')
print('=== Tables 3 and S19 - output frame and vertical range')
dz={(r['exp'],r['run'],N(r['algoritmo'])):r for r in json.load(open(os.path.join(DATA,'derived','frame_levelling.json')))}
for e in ('EXP1','EXP2'):
    for a in ALG:
        rs=[r for r in ok if r['exp']==e and N(r['algoritmo'])==a]
        t=[r['nivel_incl_deg'] for r in rs]
        z=[dz[(e,r['run'],a)]['dZ_bruto_m'] for r in rs]; zl=[dz[(e,r['run'],a)]['dZ_nivelado_m'] for r in rs]
        print(f"{e[-1]} & {a} & {np.median(t):.1f} & {min(t):.1f}--{max(t):.1f} & {np.median(z):.2f} & {np.median(zl):.2f} & {min(zl):.2f}--{max(zl):.2f}\\\\")
print('=== Table S18 - spatial hold-out of the registration')
H=[json.loads(l) for l in open(os.path.join(DATA,'registration','holdout.jsonl'))]
for e in ('EXP1','EXP2'):
    for a in ALG:
        hs=[h for h in H if h['exp']==e and N(h['algoritmo'])==a]
        conv=[h for h in hs if not (h['dT_rot_deg']>1 or h['dT_tras_cm']>5)]
        d=lambda k,m: np.median([(h['hold'][k]-h['full'][k])*m for h in conv]) if conv else float('nan')
        mx=max(abs(h['hold']['p95_exactitud_m']-h['full']['p95_exactitud_m'])*100 for h in hs)
        print(f"{e[-1]} & {a} & {len(hs)} & {len(conv)} & {np.median([h['dT_tras_cm'] for h in hs]):.2f} & {np.median([h['dT_rot_deg'] for h in hs]):.3f} & {d('p95_exactitud_m',100):+.3f} & {d('dbi_m',100):+.3f} & {d('cov@0.02',100):+.2f} & {mx:.2f}\\\\")
# ---------------------------------------------------------------------------------------
# Table 3 (pooled over both scenarios) and Tables S2/S3 (trajectory repeatability)
T={(r['exp'],r['run'],N(r['algoritmo'])):r for r in map(json.loads,open(os.path.join(DATA,'runwise','trajectories.jsonl')))}
print('=== Table 3 - tilt of the output frame, median (range) over both scenarios')
for a in ALG:
    t=[r['nivel_incl_deg'] for r in ok if N(r['algoritmo'])==a]
    print(f"{a} & {np.median(t):.1f} ({min(t):.1f}--{max(t):.1f})")
print('=== Tables S2 and S3 - trajectory repeatability')
DELTA_HAND=A.DELTA; EP=A.EP
for e in ('EXP1','EXP2'):
    for a in ALG:
        todos=[k for k in T if k[0]==e and k[2]==a]
        v=[T[(e,r['run'],a)] for r in ok if r['exp']==e and N(r['algoritmo'])==a]
        L=np.array([x['L_10hz_m'] for x in v]); cv=np.std(L,ddof=1)/np.mean(L)*100
        hz=[x['hz'] for x in v]   # a single rate unless it varies by more than 10 % across runs
        rate=f"{np.median(hz):.0f}" if max(hz)/min(hz)<1.1 else f"{min(hz):.0f}--{max(hz):.0f}"
        d=np.median([x['cierre_m'] for x in v]); zl=np.median([x['dZ_m'] for x in v])
        zb=np.median([dz[(e,r['run'],a)]['dZ_bruto_m'] for r in ok if r['exp']==e and N(r['algoritmo'])==a])
        if e=='EXP1':
            print(f"{a} & {len(v)} & {rate} & {L.mean():.2f} & {np.std(L,ddof=1):.2f} & {cv:.2f} & {d:.3f} & {zb:.2f} / {zl:.2f}\\\\")
        else:
            print(f"{a} & {len(v)}/{len(todos)} & {np.median(L):.2f} & {cv:.2f} & {d:.3f} & {zb:.2f} & {zl:.2f} & ${zl-EP-DELTA_HAND:+.2f}$\\\\")
