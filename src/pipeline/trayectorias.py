# -*- coding: utf-8 -*-
"""Metricas de trayectoria: longitud, DeltaZ, cierre y velocidad de marcha.

Tres cuidados que el analisis original no tomaba:

 1. La longitud acumulada depende de la FRECUENCIA DE MUESTREO. D-LIO exporta a ~100 Hz y
    el resto a ~10 Hz; sumar distancias entre muestras consecutivas favorece o penaliza
    segun la tasa, no segun el recorrido. Se reporta tambien L remuestreada a 10 Hz y con
    una puerta espacial, para separar recorrido real de temblor de alta frecuencia.
 2. DeltaZ se compara contra el entrepiso medido en el TLS de Exp 2 (3.15 m), de modo que
    deja de ser descriptor y pasa a ser error altimetrico.
 3. La velocidad se calcula sobre la version remuestreada, por la misma razon.
"""
import os,sys,io,json,zipfile,numpy as np
AQUI=os.path.dirname(os.path.abspath(__file__))
def _raiz():
    b=os.environ.get("BASE")
    if b and os.path.isdir(b): return b
    for c in (os.path.dirname(AQUI),AQUI,os.getcwd()):
        if os.path.isdir(os.path.join(c,"EXP 1")): return c
    raise SystemExit("No encuentro 'EXP 1'/'EXP 2'.")
B=_raiz()
ENTREPISO=3.15   # medido en el histograma en Z del TLS de Exp 2

def tum(txt):
    a=np.array([[float(x) for x in l.split()[:4]] for l in txt.splitlines()
                if l.strip() and not l.startswith('#') and len(l.split())>=4])
    return a[:,0], a[:,1:4]

def remuestrea(t,P,hz=10.0):
    if len(t)<3: return t,P
    tt=np.arange(t[0],t[-1],1.0/hz)
    return tt, np.stack([np.interp(tt,t,P[:,i]) for i in range(3)],1)

def puerta(P,d=0.02):
    """Descarta pasos por debajo de d: elimina temblor sin tocar el recorrido."""
    keep=[0]
    for i in range(1,len(P)):
        if np.linalg.norm(P[i]-P[keep[-1]])>=d: keep.append(i)
    return P[keep]

def L(P): return float(np.linalg.norm(np.diff(P,axis=0),axis=1).sum()) if len(P)>1 else 0.0

def analiza(t,P):
    dur=float(t[-1]-t[0]); hz=len(t)/dur if dur>0 else np.nan
    tr,Pr=remuestrea(t,P,10.0)
    v=np.linalg.norm(np.diff(Pr,axis=0),axis=1)*10.0
    return {"n":len(t),"dur_s":round(dur,1),"hz":round(hz,1),
            "L_cruda_m":round(L(P),3),"L_10hz_m":round(L(Pr),3),
            "L_puerta2cm_m":round(L(puerta(Pr,0.02)),3),
            "dZ_m":round(float(P[:,2].max()-P[:,2].min()),3),
            "cierre_m":round(float(np.linalg.norm(P[-1]-P[0])),3),
            "v_media_ms":round(float(v.mean()),3),"v_sd_ms":round(float(v.std()),3),
            "v_p95_ms":round(float(np.percentile(v,95)),3)}

def recorre():
    out=[]
    # Exp 1: zips anidados
    z1=zipfile.ZipFile(f"{B}/EXP 1/EXP1_trayectorias.zip")
    for nm in z1.namelist():
        if not nm.endswith(".zip"): continue
        run="".join(c for c in os.path.basename(nm).split("_")[0] if c.isdigit())
        zi=zipfile.ZipFile(io.BytesIO(z1.read(nm)))
        for f in zi.namelist():
            if not f.lower().endswith((".txt",".tum")) or f.startswith("__MACOSX"): continue
            alg=os.path.basename(f).rsplit(".",1)[0].replace("_Denso","")
            try:
                t,P=tum(zi.read(f).decode("utf-8","ignore"))
                out.append({"exp":"EXP1","run":run,"algoritmo":alg,**analiza(t,P)})
            except Exception as e: out.append({"exp":"EXP1","run":run,"algoritmo":alg,"error":str(e)[:80]})
    # Exp 2: .tum planos
    z2=zipfile.ZipFile(f"{B}/EXP 2/Exp 2 Trayectorias.zip")
    for f in z2.namelist():
        if not f.lower().endswith(".tum") or "camera_init" in f: continue
        base=os.path.basename(f).replace(".tum","")
        run="".join(c for c in base.split("_")[0] if c.isdigit())
        alg=base.split("_trayectoria_")[-1].replace("_Denso","")
        try:
            t,P=tum(z2.read(f).decode("utf-8","ignore"))
            out.append({"exp":"EXP2","run":run,"algoritmo":alg,**analiza(t,P)})
        except Exception as e: out.append({"exp":"EXP2","run":run,"algoritmo":alg,"error":str(e)[:80]})
    return out

if __name__=="__main__":
    r=recorre()
    with open(os.path.join(AQUI,"trayectorias.jsonl"),"w",encoding="utf-8") as f:
        for x in r: f.write(json.dumps(x)+"\n")
    print(f"{len(r)} trayectorias -> trayectorias.jsonl")
