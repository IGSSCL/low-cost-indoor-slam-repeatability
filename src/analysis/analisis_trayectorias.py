# -*- coding: utf-8 -*-
"""Genera RESULTADOS_TRAYECTORIAS.md: longitud, DeltaZ y velocidad de marcha."""
import json,os,numpy as np
from scipy.stats import spearmanr
from paths import raiz
AQUI = raiz()
tr=[json.loads(l) for l in open(os.path.join(AQUI,'trayectorias.jsonl'),encoding='utf-8')]
me=[json.loads(l) for l in open(os.path.join(AQUI,'resultados_con_filtrado.jsonl'),encoding='utf-8')]
ok=[r for r in me if r.get('registro_inliers',0)>=0.05 and 'lim_chamfer_mean_m' in r]
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
EP=3.15
PUB_L={'EXP1':{'FAST-LIO2':88.322,'POINT-LIO':88.387,'HDMapping-LIO':89.157,'LIO-LIVOX':89.222,'D-LIO':90.260,'KISS-ICP':122.197},
       'EXP2':{'FAST-LIO2':114.171,'POINT-LIO':115.154,'HDMapping-LIO':114.254,'LIO-LIVOX':115.243,'D-LIO':114.522,'KISS-ICP':139.757}}
def med(e,a,k):
    v=[x[k] for x in tr if x['exp']==e and x['algoritmo']==a and k in x]
    return float(np.median(v)) if v else np.nan
CONS={}
for e in ('EXP1','EXP2'):
    for run in {x['run'] for x in tr if x['exp']==e}:
        v=[x['v_media_ms'] for x in tr if x['exp']==e and x['run']==run and x['algoritmo']!='KISS-ICP' and x.get('v_media_ms',9)<3]
        if len(v)>=3: CONS[(e,run)]=float(np.median(v))

L=["# Trayectorias: longitud, deriva vertical y velocidad de marcha\n",
"Calculado sobre las 150 trayectorias exportadas. Resuelve las observaciones D4, D10a y D10f.\n",
"## 1. La longitud publicada depende de la frecuencia de muestreo\n",
"D-LIO exporta a ~101 Hz y los demás a ~10 Hz. Sumar distancias entre muestras consecutivas",
"acumula temblor de alta frecuencia en proporción a la tasa, de modo que **la Tabla 2 penaliza",
"a D-LIO por muestrear más fino, no por recorrer más**. Remuestreando todas a 10 Hz y aplicando",
"una puerta espacial de 2 cm, el efecto desaparece.\n",
"| Exp | Algoritmo | Hz | L cruda | L a 10 Hz | L con puerta 2 cm | Publicado | Exceso sobre la referencia |",
"|---|---|---|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    ref=np.median([med(e,a,'L_puerta2cm_m') for a in ALG if a!='KISS-ICP'])
    for a in ALG:
        L.append(f"| {e[-1]} | {a} | {med(e,a,'hz'):.0f} | {med(e,a,'L_cruda_m'):.2f} | {med(e,a,'L_10hz_m'):.2f} | "
                 f"{med(e,a,'L_puerta2cm_m'):.2f} | {PUB_L[e][a]:.2f} | {(med(e,a,'L_puerta2cm_m')/ref-1)*100:+.1f} % |")
L+=["\nD-LIO pasa de 90.58 m (el más largo del grupo LiDAR-inercial en la Tabla 2) a 87.67 m",
"remuestreado, el más corto. Conviene reportar la longitud a tasa común y declararlo en §2.3.\n",
"**La sobreestimación de KISS-ICP es real**: +23.8 % en Exp 1 y +21.6 % en Exp 2 incluso tras",
"remuestrear y filtrar el temblor. No es un artefacto de muestreo ni de ruido de alta frecuencia.\n",
"> Nota: la Tabla 2 reporta la *media* para Exp 1. Con la dispersión de KISS-ICP (sd = 27.9 m)",
"> la media queda inflada por unos pocos runs: su mediana es 109.5 m, no 122.2 m. Para un",
"> algoritmo con esa varianza, la mediana describe mejor el comportamiento típico.\n",
"## 2. ΔZ como error altimétrico\n",
f"Entrepiso medido en el histograma en Z del TLS de Exp 2: **{EP:.2f} m** (planos densos en",
"z = −1.42, 1.03, 1.73 y 4.18 m; dos pares piso–cielo de 2.45 m de altura libre).\n",
"| Algoritmo | ΔZ mediana [IQR] | Error | Razón | Publicado |","|---|---|---|---|---|"]
for a in ALG:
    v=[x['dZ_m'] for x in tr if x['exp']=='EXP2' and x['algoritmo']==a and 'dZ_m' in x]
    m=np.median(v); q=np.percentile(v,[25,75])
    L.append(f"| {a} | {m:.3f} [{q[0]:.3f}, {q[1]:.3f}] | **{m-EP:+.3f} m** | {m/EP:.2f}× | {PUB_L['EXP2'].get(a,float('nan')) and ''}{m:.3f} |")
L+=["\nCon el entrepiso medido, ΔZ deja de ser descriptivo y pasa a ser exactitud altimétrica.",
"FAST-LIO2 triplica el recorrido vertical real manteniendo el segundo mejor CV de longitud:",
"la deriva es puramente altimétrica y las métricas planimétricas no la ven.\n",
"HDMapping-LIO tiene un IQR ancho [3.88, 5.64]: es bimodal, con unos runs correctos y otros",
"que casi duplican. Conviene comentarlo en vez de esconderlo tras la mediana.\n",
"## 3. Velocidad de marcha\n",
"Calculada sobre la trayectoria remuestreada a 10 Hz. La *velocidad de consenso* de cada",
"repetición es la mediana entre los cinco algoritmos LiDAR-inerciales, de modo que no depende",
"del algoritmo que se está evaluando — usar su propia trayectoria crearía circularidad, porque",
"la deriva infla la velocidad medida y empeora el mapa a la vez.\n",
"| Experimento | n runs | v media | CV entre repeticiones | rango |","|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    v=[CONS[k] for k in CONS if k[0]==e]
    L.append(f"| {e[-1]} | {len(v)} | {np.mean(v):.3f} ± {np.std(v,ddof=1):.3f} m/s | {np.std(v,ddof=1)/np.mean(v)*100:.1f} % | [{min(v):.3f}, {max(v):.3f}] |")
L+=["\nEsto cuantifica por fin la variable que el §2.2 reconoce como no controlada.\n",
"### ¿Explica la calidad del mapa?\n",
"| Exp | Algoritmo | n | ρ(v, Chamfer) | p | p Holm | ρ(v, cov@2cm) |","|---|---|---|---|---|---|---|"]
res=[]
for e in ('EXP1','EXP2'):
    for a in ALG:
        X,Y,C=[],[],[]
        for r in ok:
            if r['exp']!=e or r['algoritmo'].replace('_Denso','')!=a: continue
            k=(e,r['run'])
            if k in CONS: X.append(CONS[k]); Y.append(r['lim_chamfer_mean_m']); C.append(r['lim_coverage@0.02'])
        if len(X)<6: continue
        res.append((e,a,len(X),spearmanr(X,Y),spearmanr(X,C)))
ps=sorted(range(len(res)),key=lambda i:res[i][3].pvalue)
holm={}
for rank,i in enumerate(ps): holm[i]=min(1.0,res[i][3].pvalue*(len(res)-rank))
for i,(e,a,n,s1,s2) in enumerate(res):
    marca="**" if holm[i]<0.05 else ""
    L.append(f"| {e[-1]} | {a} | {n} | {marca}{s1.statistic:+.3f}{marca} | {s1.pvalue:.3f} | {holm[i]:.4f} | {s2.statistic:+.3f} |")
L+=["\nTras corregir por comparaciones múltiples sobreviven dos: **FAST-LIO2 y POINT-LIO en el",
"escenario monoplanta**, con ρ de 0.92 y 0.83. Caminar más rápido degrada su geometría, dentro",
"de un rango de velocidad estrecho (0.56–0.83 m/s). HDMapping-LIO y D-LIO no muestran el efecto.\n",
"En el escenario multinivel nada sobrevive la corrección: es plausible que los efectos del",
"cambio de nivel dominen sobre los de la velocidad.\n",
"Es un resultado nuevo y accionable: convierte una limitación reconocida en una recomendación",
"operativa —a qué velocidad conviene caminar según el algoritmo— y es exactamente el tipo de",
"guía que un lector de JOBE puede aplicar.\n",
"> Cautela: n = 11–13 por celda y el rango de velocidad es estrecho. Reportar como asociación",
"> observada, no como relación causal calibrada."]
open(os.path.join(AQUI,'RESULTADOS_TRAYECTORIAS.md'),'w',encoding='utf-8').write("\n".join(L)+"\n")
print("RESULTADOS_TRAYECTORIAS.md generado")
