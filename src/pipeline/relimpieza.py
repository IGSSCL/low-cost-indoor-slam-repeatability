# -*- coding: utf-8 -*-
"""Segunda pasada: anade las metricas filtradas (lim_*) a un resultados.jsonl existente.

No vuelve a registrar. Reutiliza la matriz T que cada fila ya guarda, de modo que la
version cruda y la filtrada describen exactamente la misma alineacion -- dos ejecuciones
del ICP podrian converger distinto y harian incomparables ambas versiones.

Escribe resultados_con_filtrado.jsonl y deja intacto el original.
Es reanudable: si se interrumpe, relanzar y continua donde iba.

    python -W ignore relimpieza.py
"""
import os,sys,json,time,zipfile,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from geo import load_voxel, crop_to
from limpieza import metricas_limpias

AQUI=os.path.dirname(os.path.abspath(__file__))
def _raiz():
    b=os.environ.get("BASE")
    if b and os.path.isdir(b): return b
    for c in (os.path.dirname(AQUI),AQUI,os.getcwd()):
        if os.path.isdir(os.path.join(c,"EXP 1")) or os.path.isdir(os.path.join(c,"EXP 2")): return c
    raise SystemExit("No encuentro 'EXP 1'/'EXP 2'. Define la variable BASE.")
B=_raiz()
VOX=float(os.environ.get("VOX","0.01"))
DIRS={"EXP1":(f"{B}/EXP 1/TLS/Laboratorio1 - Cloud.pcd",f"{B}/EXP 1/Nubes de puntos",os.path.join(AQUI,"tls_e1.npy")),
      "EXP2":(f"{B}/EXP 2/TLS/ict 5-001 - Cloud1.pcd",f"{B}/EXP 2/Nubes de punto",os.path.join(AQUI,"tls_e2.npy"))}
ENT=os.path.join(AQUI,os.environ.get("ENTRADA","resultados.jsonl"))
SAL=os.path.join(AQUI,"resultados_con_filtrado.jsonl")
TMP=os.environ.get("RXTMP") or os.path.join(AQUI,"_tmp"); os.makedirs(TMP,exist_ok=True)

filas=[json.loads(l) for l in open(ENT,encoding="utf-8")]
hechos=set()
if os.path.exists(SAL):
    for l in open(SAL,encoding="utf-8"):
        try:
            r=json.loads(l); hechos.add((r["exp"],r["run"],r["algoritmo"]))
        except Exception: pass
print(f"[init] {len(filas)} filas de entrada, {len(hechos)} ya procesadas",flush=True)

tls_cache={}
def tls(exp):
    if exp not in tls_cache:
        p,_,c=DIRS[exp]
        if not os.path.exists(c):
            t,_=load_voxel(p,VOX); np.save(c,t.astype(np.float32))
        tls_cache[exp]=np.load(c).astype(np.float64)
    return tls_cache[exp]

def zip_de(exp,run):
    _,nd,_=DIRS[exp]
    for f in os.listdir(nd):
        if f.lower().endswith(".zip") and "".join(c for c in f.split("_")[0] if c.isdigit())==str(run):
            return os.path.join(nd,f)
    return None

t0=time.time(); n=0
for r in filas:
    k=(r.get("exp"),r.get("run"),r.get("algoritmo"))
    if k in hechos: continue
    if "T" not in r:                      # filas con error: se copian tal cual
        with open(SAL,"a",encoding="utf-8") as f: f.write(json.dumps(r)+"\n")
        continue
    zp=zip_de(r["exp"],r["run"]); dst=os.path.join(TMP,"cur.pcd"); ti=time.time()
    try:
        z=zipfile.ZipFile(zp)
        nm=[x for x in z.namelist() if x.lower().endswith(".pcd") and not x.startswith("__MACOSX")
            and os.path.basename(x).replace(".pcd","").split("_mapa_")[-1]==r["algoritmo"]][0]
        with z.open(nm) as s, open(dst,"wb") as d: shutil.copyfileobj(s,d,1<<22)
        z.close()
        E,_=load_voxel(dst,VOX)
        T=np.array(r["T"])
        ea=E.astype(np.float64)@T[:3,:3].T+T[:3,3]     # se REUTILIZA el registro guardado
        G=tls(r["exp"]); ec=crop_to(ea,G,1.0)
        for kk,v in metricas_limpias(ec,G).items(): r["lim_"+kk]=v
        r["lim_seg"]=round(time.time()-ti,1)
        msg=(f"lim_mediana={r['lim_mediana_m']*100:5.2f}cm  lim_P95={r['lim_p95_m']*100:6.2f}cm  "
             f"exac={r['lim_p95_exactitud_m']*100:6.2f}  ROR={r['lim_frac_eliminada_ror']*100:4.2f}%")
    except Exception as e:
        r["lim_error"]=f"{type(e).__name__}: {e}"; msg=f"ERROR {r['lim_error'][:70]}"
    finally:
        try:
            if os.path.exists(dst): os.remove(dst)
        except OSError: pass
    with open(SAL,"a",encoding="utf-8") as f: f.write(json.dumps(r)+"\n")
    n+=1
    print(f"[{r['exp']}/run{r['run']}/{r['algoritmo'][:16]:<16}] {time.time()-ti:5.1f}s  {msg}",flush=True)
print(f"[fin] {n} filas nuevas en {(time.time()-t0)/60:.1f} min -> {os.path.basename(SAL)}",flush=True)
