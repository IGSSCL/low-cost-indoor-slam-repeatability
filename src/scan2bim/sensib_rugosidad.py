"""Sensibilidad de la rugosidad a los dos parametros libres: el ancho de la banda
alrededor del plano y el tamano de celda. Se recalcula sobre los mismos cache de banda
del Exp 1 (corridas 1, 8 y 13) y se compara el orden entre algoritmos."""
import numpy as np, glob, re, json, collections
g=json.load(open('geom_e1.json')); Z0=g['z_suelo']
def rugosidad(Q, banda, celda, minpts=40):
    s=Q[np.abs(Q[:,2]-Z0)<banda]
    if len(s)<5000: return None
    ij=np.floor(s[:,:2]/celda).astype(np.int64)
    key=ij[:,0]*1000003+ij[:,1]
    orden=np.argsort(key); key=key[orden]; z=s[orden,2].astype(np.float64)
    cortes=np.flatnonzero(np.diff(key))+1
    vals=[]
    for a,b in zip(np.r_[0,cortes], np.r_[cortes,len(key)]):
        if b-a<minpts: continue
        r=z[a:b]-np.median(z[a:b])
        vals.append(1.4826*np.median(np.abs(r)))
    return float(np.median(vals))*1000 if vals else None
cfg=[(0.05,0.5),(0.03,0.5),(0.08,0.5),(0.05,0.25),(0.05,1.0)]
res=collections.defaultdict(dict)
for f in sorted(glob.glob('band_*.npy')):
    run,alg=re.match(r'band_(\d+)_(.+)\.npy',f).groups()
    Q=np.load(f).astype(np.float64)
    for banda,celda in cfg:
        v=rugosidad(Q,banda,celda)
        res[alg].setdefault((banda,celda),[]).append(v)
print(f"{'algoritmo':16} " + " ".join(f"b{int(b*100)}/c{int(c*100):3d}" for b,c in cfg))
tab={}
for alg in sorted(res):
    fila=[float(np.median([x for x in res[alg][k] if x is not None])) for k in cfg]
    tab[alg]=fila
    print(f"{alg:16} " + " ".join(f"{v:9.1f}" for v in fila))
print()
for i,(b,c) in enumerate(cfg):
    orden=[a for a in sorted(tab, key=lambda a: tab[a][i])]
    print(f"orden con banda {int(b*100)} cm, celda {c} m: " + " < ".join(orden))
json.dump(tab, open('rugosidad_sensibilidad.json','w'), indent=1)
