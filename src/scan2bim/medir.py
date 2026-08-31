import numpy as np, json, sys, glob, os
sys.path.insert(0,'.')
from walls import ajusta_plano, altura_suelo
import os as _os
# Raiz de datos: carpeta que contiene 'EXP 1' y 'EXP 2'. Se fija con la variable
# de entorno SLAM_DATA; por defecto, dos niveles por encima de este archivo.
B = _os.environ.get('SLAM_DATA') or _os.path.abspath(
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..')) + _os.sep
EXP=sys.argv[1]; RUN=sys.argv[2]
ref=json.load(open('ref_%s.json'%('e1' if EXP=='EXP1' else 'e2')))
T={}
for l in open(B+'reproceso_geometrico/resultados.jsonl'):
    d=json.loads(l)
    if d['exp']==EXP and d['run']==RUN: T[d['algoritmo']]=np.array(d['T'])
tls=np.load(B+'reproceso_geometrico/tls_%s.npy'%('e1' if EXP=='EXP1' else 'e2'))[:,:3].astype(np.float32)
suelo=altura_suelo(tls[:,2]); z0,z1=suelo+0.3, suelo+2.5
out={}
for f in sorted(glob.glob('r%s_*.npy'%RUN)):
    alg=os.path.basename(f)[len('r%s_'%RUN):-4]
    P=np.load(f).astype(np.float64)
    M=T.get(alg)
    if M is None: print('sin T:',alg); continue
    P=(P@M[:3,:3].T)+M[:3,3]
    filas=[]
    for r in ref:
        a=ajusta_plano(P, r['eje'], r['pos'], tol=0.03, z0=z0, z1=z1, nmin=300)
        if a is None: continue
        filas.append(dict(eje=r['nom'], pos=r['pos'], tls_desplome=r['desplome'],
                          slam_desplome=a['desplome_deg'], err=abs(a['desplome_deg']-r['desplome']),
                          tls_rms=r['rms'], slam_rms=a['rms_m'], n=a['npts']))
    out[alg]=filas
    e=np.array([x['err'] for x in filas]); rr=np.array([x['slam_rms'] for x in filas])
    print('%-18s caras=%2d/%d  err_desplome mediana=%.3f deg  p95=%.3f  |  rugosidad mediana=%.1f mm'%(
        alg, len(filas), len(ref), np.median(e), np.percentile(e,95), 1000*np.median(rr)))
json.dump(out, open('desplome_%s_%s.json'%(EXP,RUN),'w'))
