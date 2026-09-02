# -*- coding: utf-8 -*-
"""Paso 1 de la figura tripartita: reconstruye, con el pipeline vigente, la nube
alineada y filtrada de una corrida y su distancia punto a punto a la referencia TLS.

Reutiliza la matriz T ya guardada en resultados_con_filtrado.jsonl, de modo que la
figura describe exactamente la misma alineacion que las Tablas 3 y 4. Guarda un .npz
con los puntos y su distancia para que el paso 2 solo dibuje.

    python3 paso1.py EXP1 8 D-LIO
"""
import sys, os, json, zipfile, shutil
import numpy as np
from scipy.spatial import cKDTree

REPO = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam/repositorio')
BASE = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam')
sys.path.insert(0, os.path.join(REPO, 'src', 'pipeline'))
from geo import load_voxel, crop_to
import limpieza as LIM

EXP, RUN, ALG = sys.argv[1], sys.argv[2], sys.argv[3]
VOX = 0.01
tls_npy = os.path.join(REPO.replace('repositorio', 'reproceso_geometrico'),
                       'tls_e1.npy' if EXP == 'EXP1' else 'tls_e2.npy')
nubes = os.path.join(BASE, 'EXP 1' if EXP == 'EXP1' else 'EXP 2',
                     'Nubes de puntos' if EXP == 'EXP1' else 'Nubes de punto')

T = None
alg_zip = ALG + '_Denso' if ALG == 'FAST-LIO2' else ALG
for l in open(os.path.join(REPO, 'data', 'runwise', 'map_quality.jsonl'), encoding='utf-8'):
    d = json.loads(l)
    if d['exp'] == EXP and d['run'] == RUN and d['algoritmo'].replace('_Denso', '') == ALG:
        T = np.array(d['T']); alg_zip = d['algoritmo']
if T is None:
    sys.exit('sin T para %s %s %s' % (EXP, RUN, ALG))

zn = [f for f in os.listdir(nubes) if f.lower().endswith('.zip')
      and ''.join(c for c in f.split('_')[0] if c.isdigit()) == str(RUN)][0]
z = zipfile.ZipFile(os.path.join(nubes, zn))
nm = [n for n in z.namelist() if n.lower().endswith('.pcd') and not n.startswith('__MACOSX')
      and os.path.basename(n).replace('.pcd', '').split('_mapa_')[-1] == alg_zip][0]
tmp = os.path.join(os.path.expanduser('~/trip'), 'cur.pcd')
with z.open(nm) as s, open(tmp, 'wb') as o:
    shutil.copyfileobj(s, o, 1 << 22)
P, n_raw = load_voxel(tmp, VOX)
os.remove(tmp)

tls = np.load(tls_npy).astype(np.float32)
Q = (P.astype(np.float64) @ T[:3, :3].T) + T[:3, 3]
Q = crop_to(Q, tls, margin=1.0)
Q, frac_ror = LIM.ror(Q, v=0.10, min_vecinos=3)
mask = LIM.mascara_observada(Q, tls, celda=0.25)
frac_mask = float(1.0 - mask.mean())
Q = Q[mask]
d, _ = cKDTree(tls).query(Q.astype(np.float32), k=1, workers=-1)

np.savez_compressed(os.path.join(os.path.expanduser('~/trip'),
                    'trip_%s_%s_%s.npz' % (EXP, RUN, ALG)),
                    pts=Q.astype(np.float32), dist=d.astype(np.float32))
print('%s run %s %s: %d crudos -> %d evaluados | ROR %.2f%% | mascara %.2f%% | media %.4f m | mediana %.4f m'
      % (ALG, RUN, EXP, n_raw, len(Q), 100*frac_ror, 100*frac_mask, d.mean(), np.median(d)))
