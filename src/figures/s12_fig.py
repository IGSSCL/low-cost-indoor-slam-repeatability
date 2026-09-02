# -*- coding: utf-8 -*-
"""Figuras S1 y S2: resumen visual de la comparacion mapa-TLS.

Las cifras de los paneles cuantitativos se toman de las Tablas 3 y 4 del cuerpo (medianas
run-wise sobre todas las repeticiones), no de la corrida mostrada, para que la figura no
pueda contradecir a la tabla. Las vistas ortogonales colorean la corrida representativa a
resolucion de dibujo.

    python3 s12_fig.py EXP1 "Experiment 1" app_exp1_multi_model_visual_summary
"""
import sys, os, json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

EXP, TIT, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.environ.get('SLAM_FIGDIR', '.')
AQUI = os.path.expanduser('~/trip')
REPO = os.path.expanduser('~/mnt/P RX-BIM/Paper Slam/repositorio')
ALG = ['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS = {'EXP1':[str(i) for i in range(1,14)],'EXP2':[str(i) for i in range(1,13)]}

M = {}
for l in open(os.path.join(REPO,'data','runwise','map_quality.jsonl'), encoding='utf-8'):
    x = json.loads(l); M[(x['exp'],x['run'],x['algoritmo'].replace('_Denso',''))] = x
def ok(e,r,a):
    x = M.get((e,r,a)); return x is not None and x.get('registro_inliers',0) >= 0.05 and 'lim_chamfer_mean_m' in x
def med(a,k):
    v = [M[(EXP,r,a)][k] for r in RUNS[EXP] if ok(EXP,r,a) and k in M[(EXP,r,a)]]
    return float(np.median(v))*100 if v else np.nan
DBI = {a: med(a,'lim_chamfer_mean_m') for a in ALG}
MED = {a: med(a,'lim_mediana_m') for a in ALG}
orden = sorted(ALG, key=lambda a: DBI[a])

INK, MUTED, GRID = '#1a1a1a', '#6b6b6b', '#e3e3e1'
plt.rcParams.update({'font.size':8,'axes.labelsize':8,'xtick.labelsize':7,
                     'ytick.labelsize':7,'axes.edgecolor':MUTED,'text.color':INK,
                     'axes.labelcolor':INK,'figure.facecolor':'white','pdf.fonttype':42})
D = {a: np.load(os.path.join(AQUI,'d_%s_%s.npy'%(EXP,a))) for a in ALG}
P = {a: np.load(os.path.join(AQUI,'vista_%s_%s.npy'%(EXP,a))) for a in ALG}
# escala de color: percentil 85 acotado a 20 cm, para que discrimine en el rango
# donde vive la mayoria de los puntos en vez de quedar dominada por la cola
VMAX = min(float(np.percentile(np.concatenate([D[a] for a in ALG]), 85)), 0.20)

fig = plt.figure(figsize=(9.6, 12.4))
gs = GridSpec(8, 3, figure=fig, height_ratios=[1.5,1.5]+[1]*6,
              hspace=0.42, wspace=0.14, left=0.075, right=0.965, top=0.955, bottom=0.035)

# (a) barras: D_bi y mediana run-wise, de las tablas del cuerpo
ax = fig.add_subplot(gs[0,:])
x = np.arange(len(orden)); w = 0.38
ax.bar(x-w/2, [DBI[a] for a in orden], w, color='#0072B2', label='$D_{bi}$', zorder=3)
ax.bar(x+w/2, [MED[a] for a in orden], w, color='#56B4E9', label='Median error', zorder=3)
ax.set_xticks(x); ax.set_xticklabels(orden, rotation=16, ha='right')
ax.set_ylabel('cm'); ax.legend(frameon=False, ncol=2, loc='upper left')
ax.grid(axis='y', color=GRID, lw=0.6, zorder=0); ax.set_axisbelow(True)
ax.set_title('(a) Run-wise geometric quality over all repetitions (from the main-text table)',
             fontsize=8.5, pad=5)

# (b) distribucion de distancias de la corrida mostrada
ax = fig.add_subplot(gs[1,:])
bp = ax.boxplot([D[a] for a in orden], showfliers=False,
                patch_artist=True, widths=0.55)
for b in bp['boxes']: b.set(facecolor='#dbe9f6', edgecolor=MUTED, lw=0.8)
for k in ('whiskers','caps'): [w_.set(color=MUTED, lw=0.8) for w_ in bp[k]]
for m in bp['medians']: m.set(color='#D55E00', lw=1.4)
ax.set_xticklabels(orden, rotation=16, ha='right', fontsize=6.5)
ax.set_ylabel('Distance to reference (m)')
ax.set_ylim(0, VMAX*2.2)
ax.grid(axis='y', color=GRID, lw=0.6, zorder=0); ax.set_axisbelow(True)
ax.set_title('(b) Distribution of point-to-reference distance, representative repetition',
             fontsize=8.5, pad=5)

VIS = [((0,1),'Plan (X--Y)'), ((0,2),'Elevation (X--Z)'), ((1,2),'Profile (Y--Z)')]
rng = np.random.default_rng(5)
for k,a in enumerate(orden):
    Q, dd = P[a], D[a]
    if len(Q) > 90_000:
        s = rng.choice(len(Q), 90_000, replace=False); Q, dd = Q[s], dd[s]
    for j,((i0,i1),lab) in enumerate(VIS):
        ax = fig.add_subplot(gs[2+k, j])
        sc = ax.scatter(Q[:,i0], Q[:,i1], c=dd, s=0.05, cmap='viridis', vmin=0, vmax=VMAX,
                        linewidths=0, rasterized=True)
        ax.set_aspect('equal'); ax.tick_params(labelsize=6)
        if k == 0: ax.set_title(lab, fontsize=8, pad=3)
        if j == 0:
            ax.set_ylabel('%s\n$D_{bi}$ = %.2f cm' % (a, DBI[a]), fontsize=7.2)

cax = fig.add_axes([0.30, 0.012, 0.42, 0.008])
cb = fig.colorbar(sc, cax=cax, orientation='horizontal')
cb.set_label('Distance to TLS reference (m)', fontsize=7.5); cb.ax.tick_params(labelsize=6.5)
fig.suptitle('Map--TLS comparison, %s' % TIT, fontsize=10, y=0.978)
fig.savefig(os.path.join(OUT, NAME + '.pdf'), bbox_inches='tight', dpi=200)
print('%s: %s' % (NAME, ', '.join('%s %.2f' % (a, DBI[a]) for a in orden)))
