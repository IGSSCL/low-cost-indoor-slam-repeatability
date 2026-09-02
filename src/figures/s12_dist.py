# -*- coding: utf-8 -*-
"""Distancias punto a punto sobre las nubes ya alineadas de vista.py, para el resumen
visual del suplementario. Se calculan a resolucion de dibujo (5 cm), suficiente para una
figura cualitativa; las cifras cuantitativas de los paneles se toman de las Tablas 3 y 4."""
import numpy as np, glob, re, os
from scipy.spatial import cKDTree
BASE=os.path.expanduser('~/mnt/P RX-BIM/Paper Slam')
for exp,tlsf in (('EXP1','tls_e1.npy'),('EXP2','tls_e2.npy')):
    tls=np.load(os.path.join(BASE,'reproceso_geometrico',tlsf)).astype(np.float32)
    t=cKDTree(tls)
    for f in sorted(glob.glob('vista_%s_*.npy'%exp)):
        alg=re.match(r'vista_%s_(.+)\.npy'%exp,f).group(1)
        out='d_%s_%s.npy'%(exp,alg)
        if os.path.exists(out): continue
        P=np.load(f); d,_=t.query(P,k=1,workers=-1)
        np.save(out,d.astype(np.float32))
        print('%-16s %s: %d puntos, mediana %.3f m'%(alg,exp,len(d),np.median(d)))
