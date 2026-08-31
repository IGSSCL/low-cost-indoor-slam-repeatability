import numpy as np, json, sys
sys.path.insert(0,'.')
from bandas import leer_banda
import os as _os
# Raiz de datos: carpeta que contiene 'EXP 1' y 'EXP 2'. Se fija con la variable
# de entorno SLAM_DATA; por defecto, dos niveles por encima de este archivo.
B = _os.environ.get('SLAM_DATA') or _os.path.abspath(
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..')) + _os.sep
g=json.load(open('geom_e2.json')); lo=np.array(g['lo']); hi=np.array(g['hi'])
planos=[g['z_suelo'],g['z_cielo']]
alg=sys.argv[1]; run=sys.argv[2]
T=None
for l in open(B+'reproceso_geometrico/resultados.jsonl'):
    d=json.loads(l)
    if d['exp']=='EXP2' and d['run']==run and d['algoritmo']==alg: T=np.array(d['T'])
if T is None: print('sin T para %s run %s'%(alg,run)); sys.exit(1)
Z=B+'EXP 2/Nubes de punto/Exp%s_2.zip'%run
import subprocess
miem=[l.split()[-1] for l in subprocess.run(['unzip','-l',Z],capture_output=True,text=True).stdout.splitlines() if l.strip().endswith('.pcd')]
cand=[m for m in miem if m.endswith('_%s.pcd'%alg)]
if not cand: print('no encontrado %s en %s'%(alg,Z)); sys.exit(1)
Q=leer_banda(Z, cand[0], T, lo, hi, planos)
np.save('e2band_%s_%s.npy'%(run,alg), Q.astype(np.float32))
print('%s r%s: %d puntos'%(alg,run,len(Q)))
