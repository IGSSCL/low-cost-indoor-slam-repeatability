"""Alturas reconstruidas: separacion entre las dos losas dominantes, por algoritmo y corrida.
Invariante bajo la transformacion rigida, igual que las distancias plano a plano de la
verificacion dimensional. Se mide sobre los cache de banda (+-35 cm de cada plano del TLS):
el pico del histograma de z a 2 mm y luego el centroide de los puntos a +-2 cm del pico."""
import numpy as np, json, glob, re, collections
def pico(z, z0, w=0.35):
    s = z[np.abs(z-z0) < w]
    if len(s) < 50: return None
    h,e = np.histogram(s, bins=np.arange(z0-w, z0+w+0.002, 0.002))
    c = (e[:-1]+e[1:])/2
    return float(s[np.abs(s-c[h.argmax()]) < 0.02].mean())
def corre(geom, patron, rx):
    g = json.load(open(geom)); true = g['z_cielo']-g['z_suelo']
    acc = collections.defaultdict(list)
    for f in sorted(glob.glob(patron)):
        run, alg = re.match(rx, f).groups()
        z = np.load(f)[:,2].astype(np.float64)
        a, b = pico(z, g['z_suelo']), pico(z, g['z_cielo'])
        if a is None or b is None: continue
        acc[alg].append({'run': run, 'sep_m': round(b-a,4), 'err_mm': round((b-a-true)*1000,1)})
    return {'verdadera_m': round(true,4), 'algoritmos': dict(acc)}
out = {'EXP1': corre('geom_e1.json', 'band_*.npy', r'band_(\d+)_(.+)\.npy'),
       'EXP2': corre('geom_e2.json', 'e2band_*.npy', r'e2band_(\d+)_(.+)\.npy')}
json.dump(out, open('alturas_reconstruidas.json','w'), indent=1)
print(json.dumps({k:{a:[x['err_mm'] for x in v] for a,v in d['algoritmos'].items()} for k,d in out.items()}, indent=1))
