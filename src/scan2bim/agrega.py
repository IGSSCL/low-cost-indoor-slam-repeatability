import numpy as np, json, glob, os, collections, sys
import os as _os
# Raiz de datos: carpeta que contiene 'EXP 1' y 'EXP 2'. Se fija con la variable
# de entorno SLAM_DATA; por defecto, dos niveles por encima de este archivo.
B = _os.environ.get('SLAM_DATA') or _os.path.abspath(
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..')) + _os.sep
g=json.load(open('geom_e1.json'))
def rug(P,z0,w=0.05,celda=0.5,nmin=40):
    Q=P[np.abs(P[:,2]-z0)<w]
    if len(Q)<5000: return None
    ij=np.floor(Q[:,:2]/celda).astype(np.int64); key=ij[:,0]*100000+ij[:,1]
    o=np.argsort(key); key=key[o]; z=Q[o,2]
    b=np.flatnonzero(np.diff(key))+1; sig=[]
    for a,c in zip(np.r_[0,b], np.r_[b,len(z)]):
        if c-a<nmin: continue
        s=z[a:c]; sig.append(1.4826*np.median(np.abs(s-np.median(s))))
    if len(sig)<20: return None
    return 1000*float(np.median(sig)), len(sig)
acc=collections.defaultdict(list)
for f in sorted(glob.glob('band_*.npy')):
    _,run,alg=os.path.basename(f)[:-4].split('_',2)
    P=np.load(f).astype(np.float64)
    a=rug(P,g['z_suelo']); b=rug(P,g['z_cielo'])
    if a and b: acc[alg].append((int(run),a[0],b[0],a[1]))
print('RUGOSIDAD LOCAL DE SUPERFICIE — Experimento 1, tres repeticiones (1, 8, 13)')
print('sigma del residual en z en celdas de 0,5 m, resolucion nativa\n')
print('%-18s %-22s %-22s'%('','SUELO (mm)','CIELO (mm)'))
print('%-18s %7s %7s %6s %7s %7s'%('algoritmo','mediana','min','max','mediana','rango'))
tab={}
for alg,v in sorted(acc.items(), key=lambda x: np.median([i[1] for i in x[1]])):
    s=np.array([i[1] for i in v]); c=np.array([i[2] for i in v])
    print('%-18s %7.1f %7.1f %6.1f %7.1f %7s   n=%d'%(alg,np.median(s),s.min(),s.max(),
          np.median(c),'%.1f-%.1f'%(c.min(),c.max()),len(v)))
    tab[alg]=dict(suelo=[float(x) for x in s], cielo=[float(x) for x in c],
                  runs=[i[0] for i in v], celdas=[i[3] for i in v])
json.dump(tab,open('rugosidad_e1_runwise.json','w'))
