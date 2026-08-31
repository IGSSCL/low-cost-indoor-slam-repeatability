import numpy as np

def altura_suelo(z, q=1.0):
    h,e = np.histogram(z, bins=400)
    return e[np.argmax(h)]

def caras(xyz, eje, z0, z1, res=0.005, min_frac=0.004, sep_min=0.06):
    """Detecta caras planas perpendiculares a 'eje' dentro de la banda [z0,z1]."""
    m = (xyz[:,2]>=z0)&(xyz[:,2]<=z1)
    v = xyz[m, eje]
    if len(v) < 1000: return [], m
    lo, hi = np.percentile(v,[0.2,99.8])
    nb = max(50, int((hi-lo)/res))
    h, e = np.histogram(v, bins=nb, range=(lo,hi))
    c = 0.5*(e[:-1]+e[1:])
    umbral = max(h.max()*0.10, len(v)*min_frac)
    picos=[]
    for i in np.argsort(h)[::-1]:
        if h[i] < umbral: break
        if all(abs(c[i]-p) > sep_min for p,_ in picos):
            picos.append((c[i], h[i]))
    return sorted(picos), m

def ajusta_plano(xyz, eje, pos, tol=0.03, z0=None, z1=None, nmin=400):
    """PCA sobre los puntos de una cara; devuelve normal y desplome."""
    sel = np.abs(xyz[:,eje]-pos) <= tol
    if z0 is not None: sel &= (xyz[:,2]>=z0)&(xyz[:,2]<=z1)
    P = xyz[sel]
    if len(P) < nmin: return None
    if len(P) > 200000: P = P[np.random.default_rng(0).choice(len(P),200000,replace=False)]
    C = P - P.mean(0)
    _,_,Vt = np.linalg.svd(C, full_matrices=False)
    n = Vt[2]                      # normal = menor varianza
    n = n/np.linalg.norm(n)
    # desplome: angulo entre la normal y el plano horizontal
    desplome_deg = np.degrees(np.arcsin(abs(n[2])))
    rms = float(np.sqrt((C@n**1).__abs__().mean())) if False else float(np.sqrt(((C@n)**2).mean()))
    return dict(n=n, npts=int(len(P)), desplome_deg=float(desplome_deg),
                rms_m=rms, centro=P.mean(0).tolist())
