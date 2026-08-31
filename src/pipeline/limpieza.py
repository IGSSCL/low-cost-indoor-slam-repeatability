# -*- coding: utf-8 -*-
"""Filtrado automatico y declarado, sustituto de la 'limpieza manual en CloudCompare'.

Dos pasos, ambos con parametros explicitos y sin intervencion de operador:

 1. ROR sobre rejilla (radius outlier removal): descarta todo voxel con menos de
    `min_vecinos` voxeles ocupados en su vecindad 3x3x3. Elimina puntos volantes y no
    depende de la densidad global de la nube, a diferencia del SOR estadistico.

 2. Mascara de region observada: el TLS estatico no ve lo mismo que un sensor de mano.
    Se construye una rejilla de ocupacion del TLS a resolucion `celda`, se dilata un
    voxel en las 26 direcciones, y solo se evaluan puntos SLAM dentro de esa region.
    Es el criterio de "evaluation region" de ETH3D y Tanks&Temples: no se penaliza al
    mapa por cubrir mas que la referencia, solo por desviarse donde ambos observan.

Asimetria deliberada entre las dos direcciones:

 * SLAM->TLS (exactitud): se evalua sobre la nube filtrada y enmascarada. Un punto
   espurio no debe contar como si fuera geometria del edificio.

 * TLS->SLAM (completitud): se evalua contra la nube COMPLETA, sin filtrar ni enmascarar.
   Cada punto del TLS es por definicion region observada, y filtrar la nube objetivo
   penalizaria a los mapas mas escasos por el solo hecho de serlo -- el mismo defecto de
   densidad que invalidaba el pipeline anterior. Los puntos espurios no inflan esta
   metrica: por definicion estan lejos de la superficie del TLS.
"""
import numpy as np
from scipy.spatial import cKDTree

def _claves(P, v):
    q = np.floor(P/v).astype(np.int64) + (1<<20)
    return (q[:,0]<<42)|(q[:,1]<<21)|q[:,2]

_OFF = [(dx,dy,dz) for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1)
        if not (dx==0 and dy==0 and dz==0)]

def ror(P, v=0.10, min_vecinos=3):
    """Radius outlier removal sobre la rejilla de voxeles: descarta puntos con menos de
    `min_vecinos` celdas ocupadas en su vecindad 3x3x3 a resolucion `v` (por defecto 5 cm,
    es decir un radio de 15 cm). Elimina puntos volantes sin depender de la densidad global
    y es O(n) sobre claves empaquetadas. La resolucion del conteo es independiente del voxel
    de las metricas: a 1 cm la nube de un LiDAR de estado solido tiene los voxeles aislados.
    Devuelve (nube_filtrada, fraccion_eliminada)."""
    if len(P) < 100: return P, 0.0
    k = _claves(P, v); orden = np.argsort(k); ks = k[orden]
    n = np.zeros(len(k), dtype=np.int16)
    for dx,dy,dz in _OFF:
        despl = (dx<<42)|(dy<<21)|dz
        n += np.isin(k+despl, ks, assume_unique=False)
    keep = n >= min_vecinos
    return P[keep], float(1.0-keep.mean())

def mascara_observada(P, ref, celda=0.25):
    """True para los puntos de P dentro de la region observada por `ref` (dilatada 1 voxel)."""
    o = np.floor(ref/celda).astype(np.int64)
    o -= o.min(0)
    dims = o.max(0)+3
    ocup = set(map(tuple, o+1))
    dil = set()
    for c in ocup:
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in (-1,0,1):
                    dil.add((c[0]+dx,c[1]+dy,c[2]+dz))
    q = np.floor(P/celda).astype(np.int64) - np.floor(ref/celda).astype(np.int64).min(0) + 1
    return np.fromiter((tuple(v) in dil for v in q), bool, len(q))

def metricas_limpias(est, gt, taus=(0.01,0.02,0.03,0.05,0.075,0.10,0.15,0.20),
                     celda_ror=0.10, min_vecinos=3, celda=0.25, qcap=800_000, seed=11):
    rng = np.random.default_rng(seed)
    est_f, frac_sor = ror(est, celda_ror, min_vecinos)   # sobre la nube COMPLETA
    m = mascara_observada(est_f, gt, celda)
    est_ev = est_f[m]
    out = {"ror_celda_m":celda_ror,"ror_min_vecinos":min_vecinos,"celda_mascara_m":celda,
           "frac_eliminada_ror":frac_sor,
           "frac_fuera_region_observada":float(1.0-m.mean()),
           "n_est_evaluados":len(est_ev)}
    if len(est_ev)<1000: out["error"]="mascara vacia"; return out
    eq = est_ev if len(est_ev)<=qcap else est_ev[rng.choice(len(est_ev),qcap,replace=False)]
    gq = gt if len(gt)<=qcap else gt[rng.choice(len(gt),qcap,replace=False)]
    d_eg,_ = cKDTree(gt).query(eq,k=1)
    d_ge,_ = cKDTree(est).query(gq,k=1)       # completitud contra la nube SIN filtrar (ver nota)
    mg = np.concatenate([d_eg,d_ge])
    out.update({"chamfer_mean_m":float(0.5*(d_eg.mean()+d_ge.mean())),
                "mediana_m":float(np.median(mg)),
                "p95_m":float(np.percentile(mg,95)),
                "p95_exactitud_m":float(np.percentile(d_eg,95)),
                "p95_completitud_m":float(np.percentile(d_ge,95)),
                "p99_m":float(np.percentile(mg,99))})
    for t in taus:
        a=float((d_eg<=t).mean()); c=float((d_ge<=t).mean())
        out[f"accuracy@{t}"]=a; out[f"coverage@{t}"]=c
        out[f"fscore@{t}"]=float(2*a*c/max(a+c,1e-12))
    return out
