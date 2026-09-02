# -*- coding: utf-8 -*-
"""Figuras 4 y 7: vista general de las seis reconstrucciones y de la referencia TLS.

Cualitativa. Cada algoritmo con su color; la referencia coloreada por altura. Los
rotulos usan los nombres tal como aparecen en el texto.

    python3 vista_fig.py EXP1 8 "Experiment 1" fig04_exp1_map_overview_en
"""
import sys, os, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

EXP, RUN, TIT, NAME = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
OUT = os.environ.get('SLAM_FIGDIR', '.')
AQUI = os.path.expanduser('~/trip')
BASE = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam')

ALG = ['D-LIO', 'FAST-LIO2', 'HDMapping-LIO', 'KISS-ICP', 'LIO-LIVOX', 'POINT-LIO']
COL = {'D-LIO': '#E69F00', 'FAST-LIO2': '#009E73', 'HDMapping-LIO': '#56B4E9',
       'KISS-ICP': '#CC79A7', 'LIO-LIVOX': '#D55E00', 'POINT-LIO': '#0072B2'}
INK, MUTED = '#1a1a1a', '#6b6b6b'
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 7.5, 'xtick.labelsize': 6.0,
                     'ytick.labelsize': 6.0, 'text.color': INK, 'axes.labelcolor': INK,
                     'figure.facecolor': 'white', 'pdf.fonttype': 42})

rng = np.random.default_rng(3)
NMAX = 130_000
def carga(f):
    P = np.load(f)
    if len(P) > NMAX:
        P = P[rng.choice(len(P), NMAX, replace=False)]
    return P

nubes = {a: carga(os.path.join(AQUI, 'vista_%s_%s.npy' % (EXP, a))) for a in ALG}
tls = np.load(os.path.join(BASE, 'reproceso_geometrico',
                           'tls_e1.npy' if EXP == 'EXP1' else 'tls_e2.npy')).astype(np.float32)
if len(tls) > 320_000:
    tls = tls[rng.choice(len(tls), 320_000, replace=False)]

todo = np.vstack(list(nubes.values()) + [tls])
lo, hi = np.percentile(todo, 0.3, axis=0), np.percentile(todo, 99.7, axis=0)

fig = plt.figure(figsize=(12.7, 4.9))
gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1, 1.5], wspace=0.14, hspace=0.06,
                      left=0.01, right=0.965, top=0.97, bottom=0.03)

def ejes(ax, P, c, titulo, size=0.06):
    ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=size, c=c, linewidths=0,
               rasterized=True, depthshade=False)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_xlabel('X (m)', labelpad=-1); ax.set_ylabel('Y (m)', labelpad=-1)
    ax.set_zlabel('Z (m)', labelpad=-3)
    ax.tick_params(pad=0.4)
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(3)); ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.zaxis.set_major_locator(MaxNLocator(3))
    ax.set_title(titulo, fontsize=8.5, pad=1, color=INK)
    ax.view_init(elev=24, azim=-58)
    try: ax.set_box_aspect((hi[0]-lo[0], hi[1]-lo[1], max(hi[2]-lo[2], 1.0)))
    except Exception: pass
    ax.grid(False)
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.pane.set_edgecolor('#dddddd'); pane.pane.set_alpha(0.25)

for k, a in enumerate(ALG):
    ax = fig.add_subplot(gs[k // 3, k % 3], projection='3d')
    ejes(ax, nubes[a], COL[a], a)

ax = fig.add_subplot(gs[:, 3], projection='3d')
ejes(ax, tls, tls[:, 2], 'TLS reference — %s' % TIT, size=0.05)

fig.savefig(os.path.join(OUT, NAME + '.png'), dpi=380, bbox_inches='tight')
w = fig.get_size_inches()[0] * 300
print('%s: %d paneles, ancho ~%d px' % (NAME, len(ALG) + 1, w))
