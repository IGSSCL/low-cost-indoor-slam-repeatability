# -*- coding: utf-8 -*-
"""Prepara una nube para las vistas generales (Figuras 4 y 7): la lee del zip a
resolucion de dibujo, le aplica la transformacion ya guardada y la recorta al TLS.

No calcula distancias: estas figuras son cualitativas y colorean por algoritmo.

    python3 vista.py EXP1 8 D-LIO
"""
import sys, os, json, zipfile, shutil
import numpy as np

REPO = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam/repositorio')
BASE = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam')
sys.path.insert(0, os.path.join(REPO, 'src', 'pipeline'))
from geo import load_voxel, crop_to

EXP, RUN, ALG = sys.argv[1], sys.argv[2], sys.argv[3]
VOX_DIBUJO = 0.05
tls_npy = os.path.join(BASE, 'reproceso_geometrico', 'tls_e1.npy' if EXP == 'EXP1' else 'tls_e2.npy')
nubes = os.path.join(BASE, 'EXP 1' if EXP == 'EXP1' else 'EXP 2',
                     'Nubes de puntos' if EXP == 'EXP1' else 'Nubes de punto')
T, alg_zip = None, None
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
tmp = os.path.join(os.path.expanduser('~/trip'), 'v_%s_%s.pcd' % (EXP, ALG))
with z.open(nm) as s, open(tmp, 'wb') as o:
    shutil.copyfileobj(s, o, 1 << 22)
P, n_raw = load_voxel(tmp, VOX_DIBUJO)
os.remove(tmp)
Q = (P.astype(np.float64) @ T[:3, :3].T) + T[:3, 3]
Q = crop_to(Q, np.load(tls_npy).astype(np.float32), margin=1.0)
np.save(os.path.join(os.path.expanduser('~/trip'), 'vista_%s_%s.npy' % (EXP, ALG)),
        Q.astype(np.float32))
print('%-16s %s: %d crudos -> %d a %d cm' % (ALG, EXP, n_raw, len(Q), VOX_DIBUJO * 100))
