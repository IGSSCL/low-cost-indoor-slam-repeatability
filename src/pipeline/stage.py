"""Fase A: extrae del zip, voxeliza y guarda .npy. Fase B: registra y mide desde el .npy.
Permite trocear el trabajo cuando el entorno limita la duracion de cada comando."""
import sys,os,json,time,zipfile,shutil,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from geo import load_voxel, register, crop_to, metrics
import os as _os
# Raiz de datos: la carpeta que contiene "EXP 1" y "EXP 2".
# Por defecto, la carpeta padre de este script. Se puede forzar con la variable BASE.
def _raiz():
    b=_os.environ.get("BASE")
    if b and _os.path.isdir(b): return b
    aqui=_os.path.dirname(_os.path.abspath(__file__))
    for cand in (_os.path.dirname(aqui), aqui, _os.getcwd()):
        if _os.path.isdir(_os.path.join(cand,"EXP 1")) or _os.path.isdir(_os.path.join(cand,"EXP 2")):
            return cand
    raise SystemExit("No encuentro las carpetas 'EXP 1' / 'EXP 2'. "
                     "Copia este script dentro de la carpeta 'Paper Slam', o define la variable BASE.")
B=_raiz()
AQUI=_os.path.dirname(_os.path.abspath(__file__))
VOX=float(os.environ.get("VOX","0.01")); VD=os.environ.get("RXVOX") or os.path.join(AQUI,"vox"); os.makedirs(VD,exist_ok=True)
EXPS={"EXP1":(f"{B}/EXP 1/TLS/Laboratorio1 - Cloud.pcd",f"{B}/EXP 1/Nubes de puntos",os.path.join(AQUI,"tls_e1.npy")),
      "EXP2":(f"{B}/EXP 2/TLS/ict 5-001 - Cloud1.pcd",f"{B}/EXP 2/Nubes de punto",os.path.join(AQUI,"tls_e2.npy"))}
def key(e,r,a): return f"{VD}/{e}_r{r}_{a}.npy"
def fase_a(exp,run,alg):
    tls_p,nd,_=EXPS[exp]
    zn=[f for f in os.listdir(nd) if f.lower().endswith(".zip") and "".join(c for c in f.split("_")[0] if c.isdigit())==str(run)][0]
    z=zipfile.ZipFile(os.path.join(nd,zn))
    nm=[n for n in z.namelist() if n.lower().endswith(".pcd") and not n.startswith("__MACOSX")
        and os.path.basename(n).replace(".pcd","").split("_mapa_")[-1]==alg][0]
    _t=os.environ.get("RXTMP") or os.path.join(AQUI,"_tmp"); os.makedirs(_t,exist_ok=True); d=os.path.join(_t,"cur.pcd")
    with z.open(nm) as s, open(d,"wb") as o: shutil.copyfileobj(s,o,1<<22)
    P,n=load_voxel(d,VOX)
    try: os.remove(d)
    except OSError: pass
    np.save(key(exp,run,alg),P.astype(np.float32))
    json.dump({"n_raw":n,"n_voxel":len(P)},open(key(exp,run,alg)+".meta","w"))
    print(f"[A] {exp} run{run} {alg}: {n:,} -> {len(P):,} vox")
def fase_b1(exp,run,alg):
    """Registro + recorte. Guarda la nube alineada y recortada y la matriz T."""
    tls_p,_,cache=EXPS[exp]
    if not os.path.exists(cache):
        t,_=load_voxel(tls_p,VOX); np.save(cache,t.astype(np.float32))
    tls=np.load(cache).astype(np.float64)
    est=np.load(key(exp,run,alg)).astype(np.float64)
    T,rms,inl=register(est,tls)
    ea=est@T[:3,:3].T+T[:3,3]; ec=crop_to(ea,tls,1.0)
    np.save(key(exp,run,alg)+".crop.npy",ec.astype(np.float32))
    json.dump({"registro_rms_m":rms,"registro_inliers":inl,"T":np.round(T,6).tolist(),
               "n_tras_recorte":len(ec),"frac_fuera_del_TLS":1.0-len(ec)/max(len(ea),1)},
              open(key(exp,run,alg)+".reg","w"))
    print(f"[B1] {exp} run{run} {alg}: rms_reg={rms*100:.2f}cm inliers={inl:.3f} recorte {len(ea):,}->{len(ec):,}")

def fase_b2(exp,run,alg):
    """Metricas desde la nube ya alineada y recortada."""
    tls_p,_,cache=EXPS[exp]
    tls=np.load(cache).astype(np.float64)
    ec=np.load(key(exp,run,alg)+".crop.npy").astype(np.float64)
    meta=json.load(open(key(exp,run,alg)+".meta")); reg=json.load(open(key(exp,run,alg)+".reg"))
    r={"exp":exp,"run":str(run),"algoritmo":alg,"voxel_m":VOX,**meta,**reg}
    r.update(metrics(ec,tls))
    with open(os.path.join(AQUI,"resultados.jsonl"),"a") as f: f.write(json.dumps(r)+"\n")
    print(f"[B2] {exp} run{run} {alg}: media={r['chamfer_mean_m']*100:.2f}cm p95={r['p95_m']*100:.2f}cm cov@2cm={r['coverage@0.02']:.3f}")

def fase_b(exp,run,alg):
    tls_p,_,cache=EXPS[exp]
    if not os.path.exists(cache):
        t,_=load_voxel(tls_p,VOX); np.save(cache,t.astype(np.float32))
    tls=np.load(cache).astype(np.float64)
    est=np.load(key(exp,run,alg)).astype(np.float64)
    meta=json.load(open(key(exp,run,alg)+".meta"))
    T,rms,inl=register(est,tls)
    ea=est@T[:3,:3].T+T[:3,3]; ec=crop_to(ea,tls,1.0)
    r={"exp":exp,"run":str(run),"algoritmo":alg,"voxel_m":VOX,**meta,
       "registro_rms_m":rms,"registro_inliers":inl,"T":np.round(T,6).tolist(),
       "n_tras_recorte":len(ec),"frac_fuera_del_TLS":1.0-len(ec)/max(len(ea),1)}
    r.update(metrics(ec,tls))
    with open(os.path.join(AQUI,"resultados.jsonl"),"a") as f: f.write(json.dumps(r)+"\n")
    print(f"[B] {exp} run{run} {alg}: rms_reg={rms*100:.2f}cm media={r['chamfer_mean_m']*100:.2f}cm "
          f"p95={r['p95_m']*100:.2f}cm cov@2cm={r['coverage@0.02']:.3f}")
if __name__=="__main__":
    f,exp,run,alg=sys.argv[1:5]
    {"a":fase_a,"b":fase_b,"b1":fase_b1,"b2":fase_b2}[f](exp,run,alg)
