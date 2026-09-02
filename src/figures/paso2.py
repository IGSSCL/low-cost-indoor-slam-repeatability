# -*- coding: utf-8 -*-
"""Paso 2: dibuja la figura tripartita desde el .npz del paso 1.

Las tres vistas describen la MISMA direccion de la metrica: la distancia de cada punto
del mapa a la referencia TLS (direccion exactitud), que es la que colorea los puntos.
La mediana de las Tablas 3 y 4 agrupa las dos direcciones y por eso no coincide; se
declara en el pie.

    python3 paso2.py EXP1 8 D-LIO "Experiment 1"
"""
import sys, os, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

EXP, RUN, ALG, TIT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
OUT = os.environ.get('SLAM_FIGDIR', '.')
z = np.load(os.path.join(os.path.expanduser('~/trip'), 'trip_%s_%s_%s.npz' % (EXP, RUN, ALG)))
P, d = z['pts'], z['dist']
rng = np.random.default_rng(7)
NMAX = 260_000
sel = rng.choice(len(P), NMAX, replace=False) if len(P) > NMAX else np.arange(len(P))
Ps, ds = P[sel], d[sel]

INK, MUTED, GRID = '#1a1a1a', '#6b6b6b', '#e3e3e1'
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'text.color': INK,
                     'figure.facecolor': 'white', 'pdf.fonttype': 42})
VMAX = float(np.percentile(d, 95))
fig = plt.figure(figsize=(11.6, 3.5))

ax = fig.add_subplot(1, 3, 1, projection='3d')
s = ax.scatter(Ps[:, 0], Ps[:, 1], Ps[:, 2], c=ds, s=0.12, cmap='viridis',
               vmin=0, vmax=VMAX, linewidths=0, rasterized=True)
ax.set_xlabel('X (m)', labelpad=-4); ax.set_ylabel('Y (m)', labelpad=-4)
ax.set_zlabel('Z (m)', labelpad=-4)
ax.tick_params(pad=-2)
ax.set_title('(a) Perspective view', fontsize=8.5, pad=2)
try: ax.set_box_aspect((np.ptp(Ps[:,0]), np.ptp(Ps[:,1]), max(np.ptp(Ps[:,2]), 1e-3)))
except Exception: pass

ax = fig.add_subplot(1, 3, 2)
ax.scatter(Ps[:, 0], Ps[:, 1], c=ds, s=0.12, cmap='viridis', vmin=0, vmax=VMAX,
           linewidths=0, rasterized=True)
ax.set_aspect('equal'); ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)')
ax.set_title('(b) Plan view, coloured by distance to reference', fontsize=8.5, pad=6)
cb = fig.colorbar(s, ax=ax, fraction=0.046, pad=0.02)
cb.set_label('Distance to TLS reference (m)', fontsize=7.5)
cb.ax.tick_params(labelsize=7)

ax = fig.add_subplot(1, 3, 3)
ax.hist(d, bins=np.linspace(0, VMAX * 1.6, 90), color='#4C72B0', edgecolor='none')
ax.axvline(np.median(d), color='#D55E00', lw=1.2, ls='--')
ax.axvline(d.mean(), color='#1a1a1a', lw=1.2, ls=':')
ax.set_xlabel('Distance to TLS reference (m)'); ax.set_ylabel('Points')
ax.set_title('(c) Distribution', fontsize=8.5, pad=6)
ax.grid(axis='y', color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
txt = ('n = %s points\nmean = %.3f m\nmedian = %.3f m\n$P95$ = %.3f m'
       % (format(len(d), ','), d.mean(), np.median(d), np.percentile(d, 95)))
ax.text(0.97, 0.95, txt, transform=ax.transAxes, ha='right', va='top', fontsize=7.4,
        bbox=dict(fc='white', ec=GRID, lw=0.6, pad=3.5))

fig.suptitle('%s vs. TLS reference — %s, run %s' % (ALG, TIT, RUN), fontsize=9.5, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.95])
name = {'D-LIO': 'fig04b_exp1_dlio_slam_tls_tripartite',
        'LIO-LIVOX': 'fig05b_exp2_liolivox_slam_tls_tripartite'}[ALG]
fig.savefig(os.path.join(OUT, name + '.pdf'), bbox_inches='tight', dpi=300)
print('%s: n=%d media=%.4f mediana=%.4f P95=%.4f' % (ALG, len(d), d.mean(), np.median(d), np.percentile(d, 95)))
