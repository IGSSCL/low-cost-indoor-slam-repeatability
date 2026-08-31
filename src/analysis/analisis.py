# -*- coding: utf-8 -*-
"""Genera B.18/B.19 corregidas, subindice Qa, indice Sa y contrastes estadisticos."""
import json,os,itertools,numpy as np
from scipy.stats import rankdata, chi2, spearmanr
from paths import raiz
AQUI = raiz()
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
rs=[json.loads(l) for l in open(os.path.join(AQUI,'resultados.jsonl'))]
D={}
for r in rs: D[(r['exp'],r['run'],r['algoritmo'].replace('_Denso',''))]=r
# --- runs divergentes: mismo criterio operativo que la Tabla 4 del paper ---
DIV=[k for k,v in D.items() if 'chamfer_mean_m' not in v or v.get('registro_inliers',1)<0.05]
def val(e,r,a,k='chamfer_mean_m'):
    x=D.get((e,r,a))
    return None if (x is None or (e,r,a) in DIV or k not in x) else x[k]
RUNS={'EXP1':[str(i) for i in range(1,14)],'EXP2':[str(i) for i in range(1,13)]}
MET=[('chamfer_mean_m','Chamfer','cm',100,False),('median_m','mediana','cm',100,False),
     ('p95_m','P95','cm',100,False),('p99_m','P99','cm',100,False),
     ('coverage@0.02','cov@2cm','',1,True),('coverage@0.05','cov@5cm','',1,True)]

def tabla(e,robusto):
    L=[f"\n### {'Tabla B.19' if robusto else 'Tabla B.18'} corregida — {'Experimento 2, mediana [IQR] sobre 12' if robusto else 'Experimento 1, media ± sd sobre 13'} repeticiones\n",
       "| Algoritmo | n | "+" | ".join(f"{n} ({u})" if u else n for _,n,u,_,_ in MET)+" |",
       "|---"*(len(MET)+2)+"|"]
    for a in ALG:
        vs={k:[val(e,r,a,k) for r in RUNS[e]] for k,_,_,_,_ in MET}
        vs={k:[x for x in v if x is not None] for k,v in vs.items()}
        n=len(vs['chamfer_mean_m']); cel=[]
        for k,_,_,s,_ in MET:
            x=np.array(vs[k])*s
            if not len(x): cel.append("—"); continue
            cel.append(f"{np.median(x):.2f} [{np.percentile(x,25):.2f}, {np.percentile(x,75):.2f}]" if robusto
                       else f"{x.mean():.2f} ± {x.std(ddof=1):.2f}")
        L.append(f"| {a} | {n}/{len(RUNS[e])} | "+" | ".join(cel)+" |")
    return L

def skillings_mack(e,k):
    """Friedman generalizado a bloques incompletos (Skillings-Mack, 1981)."""
    A=[];  # matriz bloque x tratamiento con NaN
    for r in RUNS[e]:
        A.append([val(e,r,a,k) if val(e,r,a,k) is not None else np.nan for a in ALG])
    A=np.array(A,float); n,kk=A.shape
    Aj=np.zeros(kk)
    for i in range(n):
        ok=~np.isnan(A[i]); ki=ok.sum()
        if ki<2: continue
        rk=rankdata(A[i,ok])
        aj=np.sqrt(12.0/(ki+1))*(rk-(ki+1)/2.0)
        Aj[ok]+=aj
    S0=np.zeros((kk,kk))
    for i in range(n):
        ok=~np.isnan(A[i]); ki=ok.sum()
        if ki<2: continue
        idx=np.where(ok)[0]
        for p in idx:
            S0[p,p]+=(ki-1)
            for q in idx:
                if p!=q: S0[p,q]-=1
    S=np.linalg.pinv(S0)
    T=float(Aj@S@Aj); df=kk-1
    return T,df,float(chi2.sf(T,df))

# ---------- subindice de calidad geometrica Qa ----------
def resumen(e,a,k):
    v=[val(e,r,a,k) for r in RUNS[e]]; v=[x for x in v if x is not None]
    return float(np.median(v)) if v else np.nan

def norm(col,mayor_mejor):
    c=np.array(col,float); lo,hi=np.nanmin(c),np.nanmax(c)
    if hi-lo<1e-15: return np.ones_like(c)*0.5
    return (c-lo)/(hi-lo) if mayor_mejor else (hi-c)/(hi-lo)

def qa(claves):
    cols=[]
    for e in ('EXP1','EXP2'):
        for k,mm in claves:
            cols.append(norm([resumen(e,a,k) for a in ALG],mm))
    return dict(zip(ALG,np.mean(cols,axis=0)))

Q5=qa([('chamfer_mean_m',False),('p95_m',False),('p99_m',False),('coverage@0.02',True),('fscore@0.02',True)])
Q3=qa([('chamfer_mean_m',False),('p95_m',False),('coverage@0.02',True)])
# Ra y Ca provienen de tablas no afectadas (2,3,4,8,9) -> se reutilizan los de la Tabla 10
RA=dict(zip(ALG,[0.886,0.801,0.902,0.856,0.482,0.231]))
CA=dict(zip(ALG,[0.880,0.928,0.276,0.706,0.399,0.956]))
def sa(Q,wr=.30,wq=.50,wc=.20): return {a:wr*RA[a]+wq*Q[a]+wc*CA[a] for a in ALG}

out=["# Resultados recalculados — evaluación geométrica SLAM vs TLS\n",
 f"Pares procesados: {len([1 for v in D.values() if 'chamfer_mean_m' in v])}/150. "
 f"Runs excluidos por divergencia: {len(DIV)} → "+", ".join(f"{e} run{r} {a}" for e,r,a in sorted(DIV))+".",
 "\nEl criterio de exclusión (inliers de registro < 0.05 o ausencia de solape) reproduce",
 "**exactamente** los tres fallos que la Tabla 4 del paper documenta por otra vía",
 "(POINT-LIO 11/12, LIO-LIVOX 10/12). Es una verificación cruzada independiente.\n"]
out+=tabla('EXP1',False)+tabla('EXP2',True)
out+=["\n## Subíndice de calidad geométrica y ranking\n",
 "`Ra` y `Ca` se reutilizan de la Tabla 10 (sus insumos —Tablas 2, 3, 4, 8 y 9— no están afectados).",
 "`Qa` se reconstruye con las medianas run-wise nuevas, normalización min–max por métrica y experimento.\n",
 "| Algoritmo | Qa (5 métricas) | Qa (3 no redundantes) | Ra | Ca | Sa nuevo | Sa publicado | rango |",
 "|---|---|---|---|---|---|---|---|"]
S=sa(Q3); Sp=dict(zip(ALG,[0.811,0.623,0.617,0.579,0.478,0.459]))
orden=sorted(ALG,key=lambda a:-S[a]); pub=sorted(ALG,key=lambda a:-Sp[a])
for a in orden:
    out.append(f"| {a} | {Q5[a]:.3f} | {Q3[a]:.3f} | {RA[a]:.3f} | {CA[a]:.3f} | **{S[a]:.3f}** | {Sp[a]:.3f} | "
               f"{pub.index(a)+1}º → **{orden.index(a)+1}º** |")
out+=[f"\n- Ranking nuevo:      `{' > '.join(orden)}`",
      f"- Ranking publicado:  `{' > '.join(pub)}`"]
r5=[sorted(ALG,key=lambda a:-sa(Q5)[a]).index(a) for a in ALG]
out.append(f"- Con las 5 métricas el orden es {'idéntico' if r5==[orden.index(a) for a in ALG] else 'distinto'} al de 3.")

out+=["\n## Contrastes estadísticos (Skillings–Mack)\n",
 "El diseño es en bloques —los mismos runs procesados por los seis algoritmos— con bloques",
 "incompletos en Exp 2, así que ni Kruskal–Wallis (ignora el bloqueo) ni Friedman (exige bloques",
 "completos) son aplicables. Skillings–Mack es la generalización correcta.\n",
 "| Experimento | Métrica | T | df | p | Kruskal–Wallis publicado |","|---|---|---|---|---|---|"]
KW={'EXP1':{'chamfer_mean_m':'H=65.33, p<0.001','p95_m':'H=65.95, p<0.001','coverage@0.02':'H=66.30, p<0.001'},
    'EXP2':{'chamfer_mean_m':'H=43.27, p<0.001','p95_m':'H=29.99, p<0.001','coverage@0.02':'H=51.28, p<0.001'}}
for e in ('EXP1','EXP2'):
    for k,nm in (('chamfer_mean_m','Chamfer'),('p95_m','P95'),('coverage@0.02','coverage@2cm')):
        T,df,p=skillings_mack(e,k)
        out.append(f"| {e[-1]} | {nm} | {T:.2f} | {df} | {'<0.001' if p<0.001 else f'{p:.4f}'} | {KW[e][k]} |")

out+=["\n## Redundancia dentro de Qa\n","| Experimento | ρ(F-score, coverage) | ρ(Chamfer, P95) | ρ(coverage, Chamfer) |","|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    f=[resumen(e,a,'fscore@0.02') for a in ALG]; c=[resumen(e,a,'coverage@0.02') for a in ALG]
    ch=[resumen(e,a,'chamfer_mean_m') for a in ALG]; p=[resumen(e,a,'p95_m') for a in ALG]
    out.append(f"| {e[-1]} | {spearmanr(f,c).statistic:+.3f} | {spearmanr(ch,p).statistic:+.3f} | {spearmanr(c,ch).statistic:+.3f} |")
out.append("\nF-score sigue siendo casi un duplicado de coverage: conviene reportar uno de los dos.")

out+=["\n## Curvas de aceptación coverage(τ) — insumo para el mapeo a LOA\n",
 "| Exp | Algoritmo | "+" | ".join(f"τ={int(t*1000)}mm" for t in (0.01,0.02,0.03,0.05,0.075,0.10))+" |",
 "|---"*8+"|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        out.append(f"| {e[-1]} | {a} | "+" | ".join(f"{resumen(e,a,f'coverage@{t}'):.3f}" for t in (0.01,0.02,0.03,0.05,0.075,0.10))+" |")
open(os.path.join(AQUI,'RESULTADOS_RECALCULADOS.md'),'w',encoding='utf-8').write("\n".join(out)+"\n")
print("\n".join(out))
