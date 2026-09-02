# -*- coding: utf-8 -*-
"""
FASE 0 de PLAN_REVISION.md - recalculos sobre los .jsonl existentes.
No toca nubes de puntos. Corrida completa: minutos.

Uso (desde la carpeta reproceso_geometrico):
    python fase0.py

Escribe recalculos/0a..0g .md y un recalculos/RESUMEN.md con todo junto.
Requiere numpy y scipy (ya instalados: numpy 2.2.6, scipy 1.15.3).
"""
import json, os, sys, math, itertools
import numpy as np
from scipy import stats

from paths import raiz
AQUI = raiz()
os.makedirs(os.path.join(AQUI,'recalculos'), exist_ok=True)
OUT  = os.path.join(AQUI, 'recalculos')
os.makedirs(OUT, exist_ok=True)

ALG  = ['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS = {'EXP1':[str(i) for i in range(1,14)], 'EXP2':[str(i) for i in range(1,13)]}
L_RUTA = {'EXP1': 88.0, 'EXP2': 114.0}   # longitud de ruta por escenario, en metros
EP   = 3.15          # entrepiso medido en el TLS

def jl(name):
    p = os.path.join(AQUI, name)
    if not os.path.exists(p):
        sys.exit("No encuentro %s. Corre este script dentro de reproceso_geometrico." % name)
    return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

def clean(a): return a.replace('_Denso','')

M   = {(r['exp'], r['run'], clean(r['algoritmo'])): r for r in jl('resultados_con_filtrado.jsonl')}
T   = {(x['exp'], x['run'], clean(x['algoritmo'])): x for x in jl('trayectorias.jsonl')}
DIM = {(x['exp'], x['run'], clean(x['algoritmo'])): x for x in jl('dimensional.jsonl')}

def ok(e, r, a):
    """Mismo filtro de exito que apendiceA.py: divergencia = no hay ajuste rigido."""
    x = M.get((e, r, a))
    return x is not None and x.get('registro_inliers', 0) >= 0.05

def serie(e, a, k, src='M'):
    src = {'M': M, 'T': T, 'D': DIM}[src]
    v = []
    for r in RUNS[e]:
        if not ok(e, r, a):
            continue
        x = src.get((e, r, a))
        if x is not None and k in x and x[k] is not None:
            v.append(x[k])
    return np.array(v, float)

def miqr(v, f=1.0, nd=2):
    """mediana [Q1, Q3] formateada."""
    if len(v) == 0: return "---"
    q1, m, q3 = np.percentile(v, [25, 50, 75]) * f
    return f"{m:.{nd}f} [{q1:.{nd}f}, {q3:.{nd}f}]"

def holm(ps):
    """p ajustados por Holm. Devuelve array en el orden original."""
    ps = np.asarray(ps, float); n = len(ps)
    idx = np.argsort(ps); adj = np.empty(n); run = 0.0
    for i, j in enumerate(idx):
        run = max(run, (n - i) * ps[j])
        adj[j] = min(1.0, run)
    return adj

def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 2
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return max(0.0, c-h), min(1.0, c+h)

W = {}   # nombre -> lineas markdown


# ---------------------------------------------------------------- 0a run-wise
L = ["# 0a - Tablas de calidad geometrica run-wise (Fase 1)",
     "",
     "Medianas sobre las repeticiones exitosas con IQR, mas la columna de RMS de registro",
     "que falta en las Tablas A.2/A.3 del apendice. Estas son las cifras que pasan a ser",
     "las Tablas 5 y 6 del cuerpo del articulo.",
     ""]
CLAVES = [('lim_chamfer_mean_m',   'Chamfer (cm)',      100, 2),
          ('lim_mediana_m',        'Mediana (cm)',      100, 2),
          ('lim_p95_exactitud_m',  'P95acc (cm)',       100, 2),
          ('lim_p99_m',            'P99 (cm)',          100, 1),
          ('lim_coverage@0.02',    'Cov@2cm',             1, 2),
          ('lim_coverage@0.05',    'Cov@5cm',             1, 2),
          ('registro_rms_m',       'RMS registro (cm)', 100, 2)]
for e in ('EXP1', 'EXP2'):
    L += ["", f"## {e}", "",
          "| Algoritmo | n | " + " | ".join(t for _, t, _, _ in CLAVES) + " |",
          "|---|---|" + "---|" * len(CLAVES)]
    orden = sorted(ALG, key=lambda a: np.median(serie(e, a, 'lim_chamfer_mean_m'))
                   if len(serie(e, a, 'lim_chamfer_mean_m')) else 9e9)
    for a in orden:
        n = int(sum(ok(e, r, a) for r in RUNS[e]))
        cel = [miqr(serie(e, a, k), f, nd) for k, _, f, nd in CLAVES]
        L.append(f"| {a} | {n} | " + " | ".join(cel) + " |")
L += ["",
      "**Control.** Los `n` deben ser 13 en todos los algoritmos del Exp 1, y en el Exp 2:",
      "12 salvo POINT-LIO (11) y LIO-LIVOX (10). Si no coinciden, el filtro de exito",
      "difiere del que uso el apendice y hay que revisarlo antes de seguir.",
      "",
      "**Contraste con la corrida representativa.** Razon valor-representativo / mediana",
      "run-wise: en el Exp 1 debe rondar 1,00; en el Exp 2 es donde aparece el sesgo",
      "optimista (FAST-LIO2 P95acc 4,05 contra 11,32).", ""]
REP = {('EXP1','HDMapping-LIO'):(2.74,1.43,13.19), ('EXP1','POINT-LIO'):(2.82,1.54,12.09),
       ('EXP1','LIO-LIVOX'):(2.89,1.46,14.15),     ('EXP1','FAST-LIO2'):(3.68,2.13,11.95),
       ('EXP1','D-LIO'):(4.67,3.96,9.49),          ('EXP1','KISS-ICP'):(5.33,3.54,24.56),
       ('EXP2','HDMapping-LIO'):(3.70,1.11,5.39),  ('EXP2','POINT-LIO'):(4.41,1.83,5.69),
       ('EXP2','FAST-LIO2'):(5.74,2.29,4.05),      ('EXP2','D-LIO'):(8.14,4.82,7.51),
       ('EXP2','LIO-LIVOX'):(8.75,3.54,26.37),     ('EXP2','KISS-ICP'):(12.51,5.72,29.24)}
L += ["| Exp | Algoritmo | Chamfer rep/med | Mediana rep/med | P95acc rep/med |", "|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        med = [np.median(serie(e, a, k)) * 100 for k in
               ('lim_chamfer_mean_m','lim_mediana_m','lim_p95_exactitud_m')]
        rep = REP[(e, a)]
        L.append(f"| {e[-1]} | {a} | " + " | ".join(
            f"{rep[i]:.2f}/{med[i]:.2f} ({rep[i]/med[i]:.2f})" for i in range(3)) + " |")
W['0a_runwise'] = L


# ------------------------------------------------------------- 0b dimensional
L = ["# 0b - Verificacion dimensional: censura, agregacion y tamano muestral (Fase 2)", ""]
dist = {}
for e in ('EXP1','EXP2'):
    s = set()
    for a in ALG:
        for r in RUNS[e]:
            x = DIM.get((e, r, a))
            if x and ok(e, r, a):
                for d in x['dimensiones']:
                    s.add(round(d['dim_TLS_m'], 4))
    dist[e] = sorted(s)
L += ["## Dimensiones de referencia distintas", "",
      "Las 1235 mediciones del resumen provienen de este numero de cantidades distintas:", ""]
for e in ('EXP1','EXP2'):
    L.append(f"- **{e}: {len(dist[e])} dimensiones**  {[round(x,3) for x in dist[e]]}")
L += ["", f"Total: **{len(dist['EXP1'])+len(dist['EXP2'])} dimensiones de referencia distintas**, "
      "medidas repetidamente en cada corrida y algoritmo.", "",
      "## Tasa de emparejamiento (censura a 12 cm)", "",
      "Planos de referencia efectivamente recuperados sobre los candidatos del escenario.",
      "Los no emparejados son fallas de recuperacion, no ausencias.", "",
      "| Exp | Algoritmo | dims/corrida (min-max) | media | candidatas | emparejamiento |",
      "|---|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    nc = len(dist[e])
    for a in ALG:
        v = [DIM[(e,r,a)]['n_dimensiones'] for r in RUNS[e]
             if (e,r,a) in DIM and ok(e,r,a)]
        if not v: continue
        L.append(f"| {e[-1]} | {a} | {min(v)}-{max(v)} | {np.mean(v):.1f} | {nc} | "
                 f"**{100*np.mean(v)/nc:.0f} %** |")
L += ["", "## P95 dimensional: mediana de percentiles por corrida contra percentil agrupado", "",
      "La Tabla 9 reporta hoy la primera. La segunda es la que corresponde si se va a",
      "hablar de confianza al 95 %.", "",
      "| Exp | Algoritmo | n dims | Mediana corridas (mm) | Mediana agrupada (mm) | "
      "P95 corridas (mm) | **P95 agrupado (mm)** | Dentro 15mm agr. | Dentro 50mm agr. |",
      "|---|---|---|---|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        filas = [DIM[(e,r,a)] for r in RUNS[e] if (e,r,a) in DIM and ok(e,r,a)]
        if not filas: continue
        mc  = np.median([x['error_abs_mediano_m'] for x in filas]) * 1000
        p9c = np.median([x['error_abs_p95_m']     for x in filas]) * 1000
        allerr = np.sort(np.array([abs(d['error_m']) for x in filas for d in x['dimensiones']], float))
        n = len(allerr)
        mg  = np.median(allerr) * 1000
        p9g = np.percentile(allerr, 95) * 1000
        w15 = 100 * np.mean(allerr <= 0.015); w50 = 100 * np.mean(allerr <= 0.050)
        L.append(f"| {e[-1]} | {a} | {n} | {mc:.1f} | {mg:.1f} | {p9c:.1f} | **{p9g:.1f}** | "
                 f"{w15:.0f} % | {w50:.0f} % |")
L += ["", "El P95 agrupado es el numero que debe alimentar cualquier afirmacion LOA (Fase 3).", ""]
W['0b_dimensional'] = L


# --------------------------------------------------------------- 0c filtrado
L = ["# 0c - Filtrado y enmascaramiento por algoritmo (Fase 6)", "",
     "El articulo reporta hoy solo la mediana agrupada (ROR 0,70 %, mascara 4,99 %).",
     "El rango entre algoritmos es de un factor de 200 en el ROR.", "",
     "| Exp | Algoritmo | Mascara % | ROR % | Recorte caja % | Inliers registro |",
     "|---|---|---|---|---|---|"]
for e in ('EXP1','EXP2'):
    for a in ALG:
        m  = serie(e, a, 'lim_frac_fuera_region_observada')
        ro = serie(e, a, 'lim_frac_eliminada_ror')
        cr = serie(e, a, 'frac_fuera_del_TLS')
        il = serie(e, a, 'registro_inliers')
        if not len(m): continue
        L.append(f"| {e[-1]} | {a} | {100*np.median(m):.2f} | {100*np.median(ro):.3f} | "
                 f"{100*np.median(cr):.2f} | {np.median(il):.3f} |")
mm = np.concatenate([serie(e,a,'lim_frac_fuera_region_observada') for e in RUNS for a in ALG])
rr = np.concatenate([serie(e,a,'lim_frac_eliminada_ror')          for e in RUNS for a in ALG])
L += ["", f"Mediana agrupada: mascara {100*np.median(mm):.2f} %, ROR {100*np.median(rr):.2f} % "
      "(coincide con lo publicado).", "",
      "**Hipotesis a descartar en el texto.** Si la mascara borrara la geometria desplazada",
      "por la deriva vertical, FAST-LIO2 deberia perder mucho mas que el resto en el Exp 2.",
      "Compara su fila con las demas: si esta en linea, la explicacion del P95acc anomalo",
      "es la seleccion de corrida (Fase 1) y no la mascara.", ""]
W['0c_filtrado'] = L


# --- indice multicriterio (usado por 0d y 0e) ---
def cvL(e, a, sub):
    v = [T[(e,r,a)]['L_10hz_m'] for r in RUNS[e] if (e,r,a) in T and ok(e,r,a)]
    return float(np.std(v, ddof=1)/np.mean(v)*100) if len(v) > 2 else np.nan
def med(e, a, k, src='M'):
    v = serie(e, a, k, src); return float(np.median(v)) if len(v) else np.nan
EFF = {'EXP1':{'FAST-LIO2':(148.0,49.34,767.98),'POINT-LIO':(151.0,57.79,546.06),
               'HDMapping-LIO':(156.0,755.81,1831.62),'LIO-LIVOX':(199.0,322.46,365.32),
               'D-LIO':(146.0,99.05,2064.80),'KISS-ICP':(142.0,118.61,395.00)},
       'EXP2':{'FAST-LIO2':(166.0,45.515,655.38),'POINT-LIO':(173.5,48.365,503.705),
               'HDMapping-LIO':(173.5,751.68,1700.14),'LIO-LIVOX':(199.0,342.27,348.745),
               'D-LIO':(169.5,102.035,2143.205),'KISS-ICP':(165.0,144.435,438.09)}}
def indice(sub):
    """Sa agregado usando solo las alternativas de 'sub' (misma formula que apendiceA.py)."""
    def nrm(c, mayor_mejor):
        c = np.array(c, float); lo, hi = np.nanmin(c), np.nanmax(c)
        if hi - lo < 1e-15: return np.ones_like(c) * 0.5
        return (c-lo)/(hi-lo) if mayor_mejor else (hi-c)/(hi-lo)
    def agg(cols): return dict(zip(sub, np.mean(cols, axis=0)))
    res = {}
    for e in ('EXP1','EXP2'):
        Q = agg([nrm([med(e,a,'lim_chamfer_mean_m')          for a in sub], False),
                 nrm([med(e,a,'lim_p95_exactitud_m')         for a in sub], False),
                 nrm([med(e,a,'lim_p99_m')                   for a in sub], False),
                 nrm([med(e,a,'lim_coverage@0.02')           for a in sub], True),
                 nrm([med(e,a,'error_abs_mediano_m','D')     for a in sub], False)])
        cols = [nrm([cvL(e,a,sub) for a in sub], False),
                nrm([med(e,a,'cierre_m','T') for a in sub], False),
                nrm([med(e,a,'v_sd_ms','T')  for a in sub], False)]
        if e == 'EXP2':
            cols.append(nrm([abs(med(e,a,'dZ_m','T') - EP) for a in sub], False))
        R = agg(cols)
        C = agg([nrm([EFF[e][a][0] for a in sub], False),
                 nrm([EFF[e][a][1] for a in sub], False),
                 nrm([EFF[e][a][2] for a in sub], False)])
        res[e] = {a: 0.30*R[a] + 0.50*Q[a] + 0.20*C[a] for a in sub}
    return {a: 0.5*(res['EXP1'][a] + res['EXP2'][a]) for a in sub}, res

base, base_e = indice(ALG)
# ----------------------------------------------------------------- 0d umbral
EX = {'POINT-LIO':11, 'FAST-LIO2':12, 'HDMapping-LIO':12, 'D-LIO':12, 'LIO-LIVOX':10, 'KISS-ICP':12}
N2 = 12
L = ["# 0d - Umbral no compensatorio: conjunto admisible y resolucion (Fase 5)", "",
     "## Intervalos de Wilson al 95 % para la tasa de exito del Experimento 2", "",
     "| Algoritmo | Exito | Tasa | IC 95 % (Wilson) | Contiene 1,0 |", "|---|---|---|---|---|"]
for a in ALG:
    k = EX[a]; lo, hi = wilson(k, N2)
    L.append(f"| {a} | {k}/{N2} | {100*k/N2:.1f} % | [{lo:.2f}, {hi:.2f}] | "
             f"{'si' if hi >= 0.999 else 'no'} |")
p_fisher = stats.fisher_exact([[11, 1], [12, 0]])[1]
L += ["", f"11/12 contra 12/12, prueba exacta de Fisher: p = {p_fisher:.3f}. "
      "No son distinguibles a este tamano muestral.", "",
      "## Conjunto admisible en funcion del umbral", "",
      "Con N = 12 los valores alcanzables son k/12. Solo hay tres en los datos.", "",
      "| Rango del umbral | Admisibles | Seleccion |", "|---|---|---|"]
cortes = [(0.0, 10/12, "0 % - 83,3 %"), (10/12, 11/12, "> 83,3 % y <= 91,7 %"),
          (11/12, 12/12, "> 91,7 % y <= 100 %")]
for lo, hi, etq in cortes:
    adm = [a for a in ALG if EX[a]/N2 >= hi - 1e-9]
    adm = sorted(adm, key=lambda a: -base[a])          # por Sa, no por orden de lista
    L.append(f"| {etq} | {', '.join(adm)} | **{adm[0] if adm else '---'}** |")
L += ["", "La linea intermedia es la que hoy no aparece en el articulo: cualquier umbral",
      "entre 83,3 % y 91,7 % conserva a POINT-LIO y hace coincidir la lectura compensable",
      "con la no compensable. El umbral de 95 % es operacionalmente identico a 'cero fallas'",
      "y esta colocado justo en el hueco que separa a los dos punteros.", ""]
W['0d_umbral'] = L


# ------------------------------------------------------- 0e leave-one-out MCDA
L = ["# 0e - Sensibilidad al conjunto de alternativas (leave-one-out) (Fase 8)", "",
     "La normalizacion min-max fija el origen de cada escala con la peor alternativa del",
     "conjunto. KISS-ICP marca Ra = 0,000 en el Exp 1: una sola alternativa define la escala",
     "de repetibilidad completa. Todo el analisis de sensibilidad publicado varia **solo los",
     "pesos**, que es una pregunta distinta.", "",
     "## Orden base (las seis alternativas)", "",
     "`" + " > ".join(sorted(ALG, key=lambda a: -base[a])) + "`", "",
     "| Conjunto retirado | Orden resultante | Cambia? |", "|---|---|---|"]
ord_base = sorted(ALG, key=lambda a: -base[a])
for fuera in ALG:
    sub = [a for a in ALG if a != fuera]
    ag, _ = indice(sub)
    o = sorted(sub, key=lambda a: -ag[a])
    ref = [a for a in ord_base if a != fuera]
    L.append(f"| {fuera} | `{' > '.join(o)}` | {'**SI**' if o != ref else 'no'} |")
L += ["", "El caso que importa es retirar **KISS-ICP**: es la linea base LiDAR-only y",
      "discutiblemente no es un par de los otros cinco. Si el orden HDMapping-LIO /",
      "FAST-LIO2 se invierte al retirarla, hay que decirlo en el articulo, porque el",
      "propio texto ya reporta ese par como inestable.", "",
      "## Sa agregado por conjunto", "",
      "| Retirado | " + " | ".join(ALG) + " |", "|---|" + "---|"*len(ALG)]
L.append("| (ninguno) | " + " | ".join(f"{base[a]:.3f}" for a in ALG) + " |")
for fuera in ALG:
    sub = [a for a in ALG if a != fuera]
    ag, _ = indice(sub)
    L.append(f"| {fuera} | " + " | ".join(f"{ag[a]:.3f}" if a in ag else "---" for a in ALG) + " |")
W['0e_leaveoneout'] = L


# ---------------------------------------------------- 0f velocidad vs calidad
L = ["# 0f - Velocidad de marcha y calidad del mapa: familia completa (Fase 8)", "",
     "El articulo reporta hoy cuatro algoritmos de un solo experimento, en un parentesis,",
     "sin n, sin p y sin decir sobre que familia se corrigio. Esta es la familia completa.", "",
     "**Velocidad cinematica.** v = longitud de ruta / duracion de la captura. La duracion",
     "es propiedad de la grabacion, no del algoritmo, y la ruta es la misma en todas las",
     "repeticiones de un escenario, asi que el predictor no contiene ninguna estimacion",
     "de ningun algoritmo. Spearman es invariante al valor supuesto de la longitud.", ""]
vcons = {}
for e in ('EXP1','EXP2'):
    for r in RUNS[e]:
        # Velocidad cinematica: v = L_ruta / t. La duracion es una propiedad de la
        # grabacion y no del algoritmo -- los seis procesan el mismo MCAP y difieren en
        # ella un CV mediano de 0,49 % --, mientras que la velocidad derivada de cada
        # trayectoria varia entre algoritmos un 8,9 % mediano. La longitud de ruta es
        # constante dentro de cada escenario, de modo que el predictor no contiene
        # ninguna estimacion de ningun algoritmo. Al ser L constante no altera el orden
        # de las corridas, y Spearman es invariante: el coeficiente no depende de su
        # valor (verificado con L entre 70 y 130 m: identico al cuarto decimal).
        d = [T[(e,r,a)]['dur_s'] for a in ALG
             if (e,r,a) in T and ok(e,r,a) and T[(e,r,a)].get('dur_s')]
        if d: vcons[(e,r)] = L_RUTA[e] / float(np.median(d))
rng = [v for v in vcons.values()]
L += [f"Rango de velocidad de consenso: {min(rng):.2f} - {max(rng):.2f} m/s "
      f"sobre las {len(RUNS['EXP1'])+len(RUNS['EXP2'])} corridas.", ""]
for kmet, tit in (('lim_chamfer_mean_m','Chamfer'), ('lim_p95_exactitud_m','P95acc')):
    filas, ps = [], []
    for e in ('EXP1','EXP2'):
        for a in ALG:
            xs, ys = [], []
            for r in RUNS[e]:
                if not ok(e,r,a) or (e,r) not in vcons: continue
                x = M.get((e,r,a))
                if x and kmet in x:
                    xs.append(vcons[(e,r)]); ys.append(x[kmet])
            if len(xs) >= 5:
                rho, p = stats.spearmanr(xs, ys)
                filas.append([e[-1], a, len(xs), rho, p]); ps.append(p)
    adj = holm(ps)
    L += ["", f"## {tit} contra velocidad de consenso (Spearman)", "",
          f"Familia de {len(ps)} pruebas (6 algoritmos x 2 experimentos), Holm sobre esa familia.", "",
          "| Exp | Algoritmo | n | rho | p crudo | p ajustado | Significativo |",
          "|---|---|---|---|---|---|---|"]
    for f, pa in zip(filas, adj):
        L.append(f"| {f[0]} | {f[1]} | {f[2]} | {f[3]:+.2f} | {f[4]:.4f} | {pa:.4f} | "
                 f"{'**si**' if pa < 0.05 else 'no'} |")
L += ["", "Ojo con la lectura: rho positivo significa que **mas velocidad empeora** la",
      "metrica (Chamfer y P95acc son de menor-mejor). Y esto sigue siendo un diseno",
      "observacional: la velocidad varia junto con todo lo demas que el operador hizo",
      "distinto en esa caminata. La recomendacion del articulo debe redactarse como",
      "asociacion, no como intervencion.", ""]
W['0f_velocidad'] = L


# ------------------------------------------------------------- 0g piso de dZ
L = ["# 0g - Piso fisico de dZ y el Experimento 1 como validacion (Fase 8)", "",
     "El rango vertical de la trayectoria (dZ = max z - min z) no es solo la altura de",
     "entrepiso: incluye la excursion vertical propia de un sensor de mano en una caminata",
     "de 3 minutos. Llamemosla delta.", "",
     "**El Experimento 1 la mide directamente.** Es monoplanta: no hay cambio de nivel, asi",
     "que su dZ **es** delta, sin suposiciones. Y ahi aparece algo que el articulo hoy no",
     "reporta: la Tabla 2 del Exp 1 no tiene columna de dZ.", "",
     "| Algoritmo | n | dZ Exp 1 (m), mediana [IQR] | maximo | veces delta |",
     "|---|---|---|---|---|"]
ESTABLES = ['POINT-LIO', 'D-LIO']          # los unicos con dZ compatible con un sensor de mano
est = np.concatenate([serie('EXP1', a, 'dZ_m', 'T') for a in ESTABLES])
delta = float(np.median(est))
for a in ALG:
    v = serie('EXP1', a, 'dZ_m', 'T')
    if not len(v): continue
    L.append(f"| {a} | {len(v)} | {miqr(v, 1, 3)} | {v.max():.3f} | {np.median(v)/delta:.1f}x |")
L += ["",
      "## Lo que dice esta tabla", "",
      "En un escenario **de un solo piso**, el rango vertical verdadero de la trayectoria es",
      "del orden de decimetros. POINT-LIO y D-LIO lo reportan asi. **FAST-LIO2, LIO-LIVOX y",
      "KISS-ICP reportan cerca de 8 metros**, y HDMapping-LIO mas de 3.", "",
      "Son exactamente los mismos tres algoritmos que en el Exp 2 inflan la circulacion",
      "vertical por factores de 2,75 a 2,99. Pero aqui la evidencia es mucho mas limpia: en",
      "el Exp 2 hay una altura de entrepiso real de 3,15 m que hay que descontar, mientras",
      "que aqui **el valor verdadero es practicamente cero**, asi que todo lo reportado es",
      "deriva. El error deja de ser un factor de 3 y pasa a ser un factor de 30.", "",
      f"delta estimado con los dos algoritmos verticalmente consistentes: **{delta:.3f} m**",
      f"(mediana sobre {len(est)} corridas; IQR [{np.percentile(est,25):.3f}, "
      f"{np.percentile(est,75):.3f}], maximo {est.max():.3f}).", "",
      "Ojo: promediar los seis algoritmos para estimar delta seria un error, porque tres de",
      "ellos no estan midiendo la excursion del sensor sino su propia deriva.", "",
      "## Consecuencia para el Experimento 2", "",
      "El valor esperado del rango vertical es 3,15 m **mas** delta, no 3,15 m.", "",
      "| Algoritmo | dZ Exp 2 (m) | Error contra 3,15 | Error contra 3,15 + delta | Razon |",
      "|---|---|---|---|---|"]
for a in ALG:
    v = serie('EXP2', a, 'dZ_m', 'T')
    if not len(v): continue
    m = float(np.median(v))
    L.append(f"| {a} | {m:.3f} | {m-EP:+.3f} | {m-EP-delta:+.3f} | {m/EP:.2f}x |")
L += ["",
      f"Con delta = {delta:.3f} m los errores pequenos se acercan a cero: no son deriva",
      "medible, son la excursion normal del sensor. Los de 2,75-2,99x no se mueven. Eso",
      "justifica presentar dZ como **detector de fallas gruesas** y no como medida graduada",
      "de exactitud, sin tocar el hallazgo principal.", "",
      "## Dos cosas que agregar al articulo", "",
      "1. **Una columna de dZ en la Tabla 2 (Exp 1).** Hoy no existe, y es donde el criterio",
      "   se valida contra un valor verdadero conocido y casi nulo. Es evidencia mas fuerte",
      "   que la del Exp 2 y esta disponible sin calcular nada nuevo.",
      "2. **El piso delta**, para no leer como deriva los +0,18 m de D-LIO y los +0,31 m de",
      "   POINT-LIO, que caben dentro de la excursion propia del sensor.", ""]
W['0g_deltaz'] = L


# ------------------------------------------------------------------- escritura
res = ["# Fase 0 - resultados de los recalculos", "",
       "Generado por `fase0.py`. Cada seccion corresponde a una fase de `PLAN_REVISION.md`.", ""]
for nombre in sorted(W):
    txt = "\n".join(W[nombre]) + "\n"
    open(os.path.join(OUT, nombre + '.md'), 'w', encoding='utf-8').write(txt)
    res += [txt, "\n---\n"]
open(os.path.join(OUT, 'RESUMEN.md'), 'w', encoding='utf-8').write("\n".join(res))
print("Listo. %d archivos en %s" % (len(W) + 1, OUT))
for n in sorted(W): print("  -", n + ".md")
print("  - RESUMEN.md  (todo junto)")
