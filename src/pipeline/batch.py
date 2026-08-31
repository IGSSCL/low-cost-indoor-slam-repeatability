import sys,os,json,time,zipfile,shutil,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from geo import load_voxel
import subprocess
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
TMP=os.environ.get("RXTMP") or os.path.join(AQUI,"_tmp"); os.makedirs(TMP,exist_ok=True)
VOX=0.01
EXPS=[("EXP1",f"{B}/EXP 1/TLS/Laboratorio1 - Cloud.pcd",f"{B}/EXP 1/Nubes de puntos",os.path.join(AQUI,"tls_e1.npy")),
      ("EXP2",f"{B}/EXP 2/TLS/ict 5-001 - Cloud1.pcd",f"{B}/EXP 2/Nubes de punto",os.path.join(AQUI,"tls_e2.npy"))]
OUT=os.path.join(AQUI,"resultados.jsonl")
SOLO=os.environ.get("SOLO","")            # p.ej. "EXP1:8,EXP2:9"  vacio = todo
BUDGET=float(os.environ.get("BUDGET","0")) # segundos; 0 = sin limite
T0=time.time()
_filtro=[tuple(x.split(":")) for x in SOLO.split(",") if x] if SOLO else None
hechos=set()
if os.path.exists(OUT):
    for l in open(OUT):
        try: r=json.loads(l); hechos.add((r["exp"],r["run"],r["algoritmo"]))
        except: pass
print(f"[init] ya procesados: {len(hechos)}",flush=True)
for exp,tls_path,nubes_dir,cache in EXPS:
    if os.path.exists(cache):
        tls=np.load(cache).astype(np.float64)
    else:
        t=time.time(); tls,nr=load_voxel(tls_path,VOX)
        np.save(cache,tls.astype(np.float32))
        print(f"[{exp}] TLS {nr:,} -> {len(tls):,} vox ({time.time()-t:.0f}s)",flush=True)
    print(f"[{exp}] TLS listo: {len(tls):,} voxeles",flush=True)
    zips=sorted([f for f in os.listdir(nubes_dir) if f.lower().endswith(".zip")])
    for zn in zips:
        run="".join(c for c in zn.split("_")[0] if c.isdigit()) or zn
        try: zf=zipfile.ZipFile(os.path.join(nubes_dir,zn))
        except Exception as e:
            print(f"[{exp}/{zn}] ZIP ilegible: {e}",flush=True); continue
        if _filtro and not any(e==exp and r==run for e,r in _filtro): zf.close(); continue
        for nm in sorted(zf.namelist()):
            if not nm.lower().endswith(".pcd") or nm.startswith("__MACOSX"): continue
            alg=os.path.basename(nm).replace(".pcd","").split("_mapa_")[-1]
            if (exp,run,alg) in hechos: continue
            if BUDGET and time.time()-T0>BUDGET:
                print("[pausa] presupuesto agotado; relanzar para continuar",flush=True); zf.close(); sys.exit(7)
            dst=os.path.join(TMP,"cur.pcd"); t=time.time()
            try:
                with zf.open(nm) as s, open(dst,"wb") as d: shutil.copyfileobj(s,d,1<<22)
                cp=subprocess.run([sys.executable,"-W","ignore",
                    os.path.join(os.path.dirname(os.path.abspath(__file__)),"worker.py"),
                    dst,cache,str(VOX)],capture_output=True,text=True,timeout=3600)
                tag=[l for l in cp.stdout.splitlines() if l.startswith("@@JSON@@")]
                if tag: r=json.loads(tag[0][8:])
                else: r={"error":f"worker rc={cp.returncode} :: {(cp.stderr or '')[-300:]}"}
            except Exception as e:
                r={"error":f"{type(e).__name__}: {e}"}
            r.update({"exp":exp,"run":run,"algoritmo":alg,"zip":zn,"seg":round(time.time()-t,1)})
            with open(OUT,"a") as f: f.write(json.dumps(r)+"\n")
            ok=r.get("chamfer_mean_m")
            print(f"[{exp}/run{run}/{alg:<16}] {r['seg']:6.1f}s  "
                  + (f"rms_reg={r['registro_rms_m']*100:5.2f}cm  media={ok*100:6.2f}cm  p95={r['p95_m']*100:6.2f}cm  cov@2cm={r['coverage@0.02']:.4f}"
                     if ok is not None else f"ERROR {r.get('error')}"),flush=True)
            try:
                if os.path.exists(dst): os.remove(dst)
            except OSError: pass
        zf.close()
print("[fin] completo",flush=True)
