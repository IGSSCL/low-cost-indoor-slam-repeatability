# -*- coding: utf-8 -*-
"""Recalcula Qa y Sa con las metricas filtradas y las compara con las crudas."""
import json,os,numpy as np
from paths import raiz
AQUI = raiz()
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS={'EXP1':[str(i) for i in range(1,14)],'EXP2':[str(i) for i in range(1,13)]}
rs=[json.loads(l) for l in open(os.path.join(AQUI,'resultados_con_filtrado.jsonl'),encoding='utf-8')]
D={(r['exp'],r['run'],r['algoritmo'].replace('_Denso','')):r for r in rs}
def ok(r,p): return r is not None and r.get('registro_inliers',0)>=0.05 and (p+'chamfer_mean_m' if p else 'chamfer_mean_m') in r
def res(e,a,k,p):
    v=[D.get((e,r,a)) for r in RUNS[e]]
    v=[x[p+k] for x in v if ok(x,p)]
    return float(np.median(v)) if v else np.nan
def norm(c,mm):
    c=np.array(c,float); lo,hi=np.nanmin(c),np.nanmax(c)
    return np.ones_like(c)*0.5 if hi-lo<1e-15 else ((c-lo)/(hi-lo) if mm else (hi-c)/(hi-lo))
def qa(claves,p):
    cols=[norm([res(e,a,k,p) for a in ALG],mm) for e in ('EXP1','EXP2') for k,mm in claves]
    return dict(zip(ALG,np.mean(cols,axis=0)))
RA=dict(zip(ALG,[0.886,0.801,0.902,0.856,0.482,0.231]))
CA=dict(zip(ALG,[0.880,0.928,0.276,0.706,0.399,0.956]))
def sa(Q): return {a:0.30*RA[a]+0.50*Q[a]+0.20*CA[a] for a in ALG}
C3=[('chamfer_mean_m',False),('p95_m',False),('coverage@0.02',True)]
Qc=qa(C3,''); Qf=qa([('chamfer_mean_m',False),('p95_exactitud_m',False),('coverage@0.02',True)],'lim_')
Sc,Sf=sa(Qc),sa(Qf)
oc=sorted(ALG,key=lambda a:-Sc[a]); of=sorted(ALG,key=lambda a:-Sf[a])
pub=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
L=["# Qa y Sa con las métricas filtradas\n",
   f"147 pares válidos de 150 (excluidos los 3 runs divergentes). ROR elimina una mediana del",
   f"0.70 % y la máscara de región observada un 4.99 %.\n",
   "En `Qa` filtrado se usa `lim_p95_exactitud_m` en lugar del P95 global: es la dirección que",
   "corresponde a una tolerancia de documentación, y la única que el filtrado modifica.\n",
   "| Algoritmo | Qa crudo | Qa filtrado | Sa crudo | Sa filtrado | publicado → filtrado |",
   "|---|---|---|---|---|---|"]
for a in of:
    L.append(f"| {a} | {Qc[a]:.3f} | {Qf[a]:.3f} | {Sc[a]:.3f} | **{Sf[a]:.3f}** | {pub.index(a)+1}º → **{of.index(a)+1}º** |")
L+=[f"\n- Ranking con métricas crudas:    `{' > '.join(oc)}`",
    f"- Ranking con métricas filtradas: `{' > '.join(of)}`",
    f"- Ranking publicado:              `{' > '.join(pub)}`",
    f"\n**El filtrado {'NO altera' if oc==of else 'ALTERA'} el orden respecto a las métricas crudas.**\n",
    "\n## P95 en la dirección exactitud, por algoritmo (mediana run-wise)\n",
    "| Algoritmo | Exp 1 | Exp 2 | banda USIBD (P95, asignable) |","|---|---|---|---|"]
def loa(x):
    return "LOA30" if x<=0.015 else ("LOA20" if x<=0.05 else "LOA10")
for a in ALG:
    e1=res('EXP1',a,'p95_exactitud_m','lim_'); e2=res('EXP2',a,'p95_exactitud_m','lim_')
    L.append(f"| {a} | {e1*100:.2f} cm | {e2*100:.2f} cm | {loa(max(e1,e2))} |")
L+=["\n## Mediana del error, por algoritmo (mediana run-wise)\n",
    "| Algoritmo | Exp 1 | Exp 2 | rango numerico de la mediana (NO asignable) |","|---|---|---|---|"]
for a in ALG:
    e1=res('EXP1',a,'mediana_m','lim_'); e2=res('EXP2',a,'mediana_m','lim_')
    L.append(f"| {a} | {e1*100:.2f} cm | {e2*100:.2f} cm | {loa(max(e1,e2))} |")
txt="\n".join(L)+"\n"
open(os.path.join(AQUI,'RESULTADOS_FILTRADOS.md'),'w',encoding='utf-8').write(txt)
print(txt)
