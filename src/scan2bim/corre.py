import numpy as np, json, sys
sys.path.insert(0,'.')
from bandas import leer_banda
import os as _os
# Raiz de datos: carpeta que contiene 'EXP 1' y 'EXP 2'. Se fija con la variable
# de entorno SLAM_DATA; por defecto, dos niveles por encima de este archivo.
B = _os.environ.get('SLAM_DATA') or _os.path.abspath(
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..')) + _os.sep
g=json.load(open('geom_e1.json')); lo=np.array(g['lo']); hi=np.array(g['hi'])
planos=[g['z_suelo'],g['z_cielo']]
alg=sys.argv[1]; run=sys.argv[2]
T=None
for l in open(B+'reproceso_geometrico/resultados.jsonl'):
    d=json.loads(l)
    if d['exp']=='EXP1' and d['run']==run and d['algoritmo']==alg: T=np.array(d['T'])
Z=B+'EXP 1/Nubes de puntos/%s_mapa 3d.zip'%run
Q=leer_banda(Z, alg+'.pcd', T, lo, hi, planos)
np.save('band_%s_%s.npy'%(run,alg), Q.astype(np.float32))
print('%s: %d puntos en banda'%(alg,len(Q)))
