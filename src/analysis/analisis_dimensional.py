# -*- coding: utf-8 -*-
"""Tablas run-wise de la verificacion dimensional."""
import json,os,numpy as np
from scipy.stats import rankdata,chi2
from paths import raiz
AQUI = raiz()
ALG=['HDMapping-LIO','POINT-LIO','FAST-LIO2','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS={'EXP1':[str(i) for i in range(1,14)],'EXP2':[str(i) for i in range(1,13)]}
d=[json.loads(l) for l in open(os.path.join(AQUI,'dimensional.jsonl'),encoding='utf-8')]
D={(x['exp'],x['run'],x['algoritmo'].replace('_Denso','')):x for x in d}
me={(r['exp'],r['run'],r['algoritmo'].replace('_Denso','')):r for r in
    map(json.loads,open(os.path.join(AQUI,'resultados_con_filtrado.jsonl'),encoding='utf-8'))}
def v(e,a,k):
    o=[D[(e,r,a)][k] for r in RUNS[e] if (e,r,a) in D and k in D[(e,r,a)]]
    return np.array(o,float)
# Rango numerico de la especificacion USIBD C120 v2.0. NO es una asignacion de banda:
# la norma fija sus limites al 95 % de confianza y la mediana es un percentil 50.
# La asignacion del articulo se hace desde el P95 (Seccion 5.2 del manuscrito).
def rango_usibd(mm): return 'LOA40' if mm<=5 else ('LOA30' if mm<=15 else ('LOA20' if mm<=50 else 'LOA10'))
loa = rango_usibd
def sm(e,k):
    A=np.array([[D[(e,r,a)][k] if (e,r,a) in D and k in D[(e,r,a)] else np.nan for a in ALG] for r in RUNS[e]])
    n,kk=A.shape; Aj=np.zeros(kk); S0=np.zeros((kk,kk))
    for i in range(n):
        m=~np.isnan(A[i]); ki=m.sum()
        if ki<2: continue
        rk=rankdata(A[i,m]); Aj[m]+=np.sqrt(12.0/(ki+1))*(rk-(ki+1)/2.0)
        idx=np.where(m)[0]
        for p in idx:
            S0[p,p]+=ki-1
            for q in idx:
                if p!=q: S0[p,q]-=1
    T=float(Aj@np.linalg.pinv(S0)@Aj); return T,kk-1,float(chi2.sf(T,kk-1))

L=["# Verificación dimensional sobre el lote completo\n",
"147 pares válidos, **1235 dimensiones medidas**. Cada dimensión es la distancia entre dos",
"planos paralelos detectados por histograma en X, Y o Z, de al menos 1 m. Una distancia es",
"invariante bajo transformación rígida, de modo que **no hereda el error del registro** — y es",
"la magnitud que se mide en obra.\n",
"## Error dimensional por algoritmo (mediana [IQR] de las medianas run-wise)\n",
"| Exp | Algoritmo | n runs | error mediano | P95 | máx | dentro 15 mm | dentro 50 mm | rango USIBD de la mediana |",
"|---|---|---|---|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        m=v(e,a,'error_abs_mediano_m')*1000
        if not len(m): continue
        p95=v(e,a,'error_abs_p95_m')*1000; mx=v(e,a,'error_abs_max_m')*1000
        d15=v(e,a,'dentro_15mm')*100; d50=v(e,a,'dentro_50mm')*100
        q=np.percentile(m,[25,75])
        L.append(f"| {e[-1]} | {a} | {len(m)} | **{np.median(m):.1f}** [{q[0]:.1f}, {q[1]:.1f}] mm | "
                 f"{np.median(p95):.1f} | {np.median(mx):.1f} | {np.median(d15):.0f} % | {np.median(d50):.0f} % | "
                 f"{loa(np.median(m))} |")
L+=["\n## Contraste estadístico (Skillings–Mack sobre el error dimensional mediano)\n",
    "| Experimento | T | df | p |","|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    T,df,p=sm(e,'error_abs_mediano_m')
    L.append(f"| {e[-1]} | {T:.2f} | {df} | {'<0.001' if p<0.001 else f'{p:.4f}'} |")
L+=["\n## Dimensión frente a nube: dos preguntas distintas\n",
"| Exp | Algoritmo | error dimensional mediano | P95 punto a punto | razón |","|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        m=v(e,a,'error_abs_mediano_m')
        pp=[me[(e,r,a)]['lim_p95_exactitud_m'] for r in RUNS[e]
            if (e,r,a) in me and 'lim_p95_exactitud_m' in me[(e,r,a)]]
        if not len(m) or not pp: continue
        dm=np.median(m); pm=np.median(pp)
        L.append(f"| {e[-1]} | {a} | {dm*1000:.1f} mm | {pm*100:.1f} cm | {pm/dm:.0f}× |")
L+=["\nEl P95 punto a punto es entre 30 y 90 veces mayor que el error dimensional. No hay",
"contradicción: una dimensión promedia el ruido de los dos planos que la definen, mientras que",
"el P95 lo acumula. Son dos preguntas distintas —*¿cuán ruidosa es la nube?* frente a *¿cuán",
"fiable es una medida tomada sobre ella?*— y para documentación as-built importa la segunda.\n",
"## Qué se puede afirmar\n",
"Con la plataforma de bajo costo evaluada, una distancia entre elementos constructivos se mide",
"con un error mediano de una decena de milímetros. Ese enunciado es verificable, no depende de",
"dónde se ponga el umbral τ, y responde la pregunta que trae un lector de JOBE.\n",
"## Cautelas\n",
"- Las dimensiones se detectan por histograma en los ejes X, Y y Z: solo captura elementos",
"  aproximadamente alineados con los ejes del levantamiento. Declararlo como limitación.",
"- El emparejamiento de planos usa tolerancia estrecha de 12 cm; con tolerancia amplia se",
"  emparejan planos físicos distintos y aparecen errores de ~300 mm idénticos en todos los",
"  algoritmos, firma inconfundible del artefacto.",
"- El número de dimensiones varía entre 2 y 13 por par (mediana 9), según cuántos planos",
"  quedaron reconstruidos. Un par con pocas dimensiones es menos informativo, no mejor."]
open(os.path.join(AQUI,'RESULTADOS_DIMENSIONAL.md'),'w',encoding='utf-8').write("\n".join(L)+"\n")
print("\n".join(L[5:32]))
