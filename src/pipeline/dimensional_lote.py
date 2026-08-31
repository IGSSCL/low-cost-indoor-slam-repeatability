# -*- coding: utf-8 -*-
"""Verificacion dimensional sobre el lote. Reutiliza la matriz T ya guardada.

Por defecto solo los runs representativos (8 en Exp 1, 9 en Exp 2) -- unos 10 minutos:

    python -W ignore dimensional_lote.py

Para el lote completo (~2 h), pasar "todo" como argumento:

    python -W ignore dimensional_lote.py todo

Reanudable: relee dimensional.jsonl y salta lo ya hecho. Reutiliza la matriz T guardada en
resultados_con_filtrado.jsonl, asi que no vuelve a registrar.
"""
import os,sys,json,time,zipfile,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from geo import load_voxel, crop_to
from dimensional import compara, resumen
AQUI=os.path.dirname(os.path.abspath(__file__))
def _raiz():
    b=os.environ.get("BASE")
    if b and os.path.isdir(b): return b
    for c in (os.path.dirname(AQUI),AQUI,os.getcwd()):
        if os.path.isdir(os.path.join(c,"EXP 1")): return c
    raise SystemExit("No encuentro 'EXP 1'/'EXP 2'.")
B=_raiz(); VOX=float(os.environ.get("VOX","0.01"))
# Alcance: por defecto solo los runs representativos. "todo" como argumento procesa el lote.
TODO = any(a.lower() in ("todo","all","--todo","--all") for a in sys.argv[1:])
SOLO = "" if TODO else os.environ.get("SOLO","EXP1:8,EXP2:9")
FILTRO=[tuple(x.split(":")) for x in SOLO.split(",") if x] if SOLO else None
print(f"[alcance] {'LOTE COMPLETO (150 pares)' if FILTRO is None else 'runs '+SOLO}",flush=True)
DIRS={"EXP1":(f"{B}/EXP 1/Nubes de puntos",os.path.join(AQUI,"tls_e1.npy")),
      "EXP2":(f"{B}/EXP 2/Nubes de punto",os.path.join(AQUI,"tls_e2.npy"))}
TMP=os.environ.get("RXTMP") or os.path.join(AQUI,"_tmp"); os.makedirs(TMP,exist_ok=True)
SAL=os.path.join(AQUI,"dimensional.jsonl")
hechos=set()
if os.path.exists(SAL):
    for l in open(SAL,encoding="utf-8"):
        try: r=json.loads(l); hechos.add((r["exp"],r["run"],r["algoritmo"]))
        except Exception: pass
filas=[json.loads(l) for l in open(os.path.join(AQUI,"resultados_con_filtrado.jsonl"),encoding="utf-8")]
tls={}
def G(e):
    if e not in tls: tls[e]=np.load(DIRS[e][1]).astype(np.float64)
    return tls[e]
def zip_de(e,run):
    nd=DIRS[e][0]
    for f in os.listdir(nd):
        if f.lower().endswith(".zip") and "".join(c for c in f.split("_")[0] if c.isdigit())==str(run):
            return os.path.join(nd,f)
t0=time.time(); n=0
for r in filas:
    k=(r.get("exp"),r.get("run"),r.get("algoritmo"))
    if k in hechos or "T" not in r: continue
    if r.get("registro_inliers",0)<0.05: continue
    if FILTRO and not any(e==k[0] and rr==k[1] for e,rr in FILTRO): continue
    dst=os.path.join(TMP,"cur.pcd"); ti=time.time()
    try:
        z=zipfile.ZipFile(zip_de(k[0],k[1]))
        nm=[x for x in z.namelist() if x.lower().endswith(".pcd") and not x.startswith("__MACOSX")
            and os.path.basename(x).replace(".pcd","").split("_mapa_")[-1]==k[2]][0]
        with z.open(nm) as s,open(dst,"wb") as d: shutil.copyfileobj(s,d,1<<22)
        z.close()
        E,_=load_voxel(dst,VOX); T=np.array(r["T"])
        ec=crop_to(E.astype(np.float64)@T[:3,:3].T+T[:3,3],G(k[0]),1.0)
        dims=compara(ec,G(k[0])); s=resumen(dims)
        fila={"exp":k[0],"run":k[1],"algoritmo":k[2],**s,"dimensiones":dims}
        msg=(f"n={s.get('n_dimensiones',0):>2}  mediana={s.get('error_abs_mediano_m',0)*1000:5.1f}mm  "
             f"max={s.get('error_abs_max_m',0)*1000:6.1f}mm  <15mm={s.get('dentro_15mm',0)*100:3.0f}%")
    except Exception as ex:
        fila={"exp":k[0],"run":k[1],"algoritmo":k[2],"error":f"{type(ex).__name__}: {ex}"}; msg=f"ERROR {ex}"
    finally:
        try:
            if os.path.exists(dst): os.remove(dst)
        except OSError: pass
    with open(SAL,"a",encoding="utf-8") as f: f.write(json.dumps(fila)+"\n")
    n+=1; print(f"[{k[0]}/run{k[1]}/{k[2][:16]:<16}] {time.time()-ti:5.1f}s  {msg}",flush=True)
print(f"[fin] {n} filas en {(time.time()-t0)/60:.1f} min -> dimensional.jsonl",flush=True)
