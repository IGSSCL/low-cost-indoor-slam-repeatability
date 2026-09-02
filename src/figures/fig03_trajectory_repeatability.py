# -*- coding: utf-8 -*-
"""Figura 3: repetibilidad, robustez y fidelidad altimetrica. Cuatro paneles.
Datos: resultados_con_filtrado.jsonl + trayectorias.jsonl (medianas run-wise)."""
import json, math, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = json.load(open('/tmp/fig03_datos.json'))
ALG = ['POINT-LIO','HDMapping-LIO','FAST-LIO2','D-LIO','LIO-LIVOX','KISS-ICP']
EXP = [('EXP1','Experiment 1','#0072B2'), ('EXP2','Experiment 2','#D55E00')]
EP, DELTA = 3.15, 0.25
INK, MUTED, GRID = '#1a1a1a', '#6b6b6b', '#e3e3e1'

def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n
    c = (p+z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return max(0., c-h)*100, min(1., c+h)*100

plt.rcParams.update({'font.size':8,'axes.labelsize':8.5,'xtick.labelsize':7.5,
                     'ytick.labelsize':7.5,'legend.fontsize':8,
                     'axes.edgecolor':MUTED,'axes.linewidth':0.6,
                     'xtick.color':MUTED,'ytick.color':MUTED,
                     'text.color':INK,'axes.labelcolor':INK,'pdf.fonttype':42})

fig, axg = plt.subplots(2, 2, figsize=(6.4, 5.6))
axes = axg.ravel()
x = np.arange(len(ALG)); w = 0.38

def barras(ax, clave, log=True):
    for i,(e,lab,col) in enumerate(EXP):
        v = [D[f"{e}|{a}"][clave] for a in ALG]
        ax.bar(x+(i-0.5)*w, v, w, color=col, label=lab, zorder=3,
               edgecolor='white', linewidth=0.6)
    if log: ax.set_yscale('log')

# (a) variabilidad de longitud
ax = axes[0]; barras(ax,'cv')
ax.set_ylabel('CV of trajectory length (%)')
ax.set_yticks([1,2,5,10,20]); ax.set_yticklabels(['1','2','5','10','20'])
ax.set_ylim(1.2, 34)
ax.set_title('(a) Length variability', fontsize=8.5, color=INK, pad=6)
for i,(e,_,_) in enumerate(EXP):
    for j,a in enumerate(ALG):
        d = D[f"{e}|{a}"]
        if d['n'] < d['N']:
            ax.text(j+(i-0.5)*w, d['cv']*1.12, f"n={d['n']}", ha='center',
                    va='bottom', fontsize=6, color=INK, zorder=5,
                    bbox=dict(fc='white', ec='none', pad=0.6))

# (b) cierre de bucle
ax = axes[1]; barras(ax,'dc')
ax.set_ylabel('Median return-to-origin displacement (m)')
ax.set_title('(b) Return-to-origin displacement', fontsize=8.5, color=INK, pad=6)

# (c) rango vertical  <-- panel nuevo
ax = axes[2]; barras(ax,'dz')
ax.axhline(DELTA, color=EXP[0][2], linewidth=1.0, linestyle=(0,(3,2)), zorder=2)
ax.axhline(EP, color=EXP[1][2], linewidth=1.0, linestyle=(0,(3,2)), zorder=2)
ax.set_xlim(-1.62, len(ALG)-0.45)
ax.text(-1.55, DELTA, 'hand\nexcursion\nExp. 1', ha='left', va='center',
        fontsize=6.2, color=EXP[0][2], linespacing=1.1, zorder=5)
ax.text(-1.55, EP, 'storey\nheight\nExp. 2', ha='left', va='center',
        fontsize=6.2, color=EXP[1][2], linespacing=1.1, zorder=5)
ax.set_ylabel('Median vertical range of trajectory (m)')
ax.set_title('(c) Vertical range vs. reference', fontsize=8.5, color=INK, pad=6)
ax.set_ylim(0.15, 45)

# (d) tasa de exito, desde cero y con IC de Wilson
ax = axes[3]
for i,(e,lab,col) in enumerate(EXP):
    v, lo, hi = [], [], []
    for a in ALG:
        d = D[f"{e}|{a}"]; p = 100*d['n']/d['N']
        l, h = wilson(d['n'], d['N'])
        v.append(p); lo.append(p-l); hi.append(h-p)
    ax.bar(x+(i-0.5)*w, v, w, color=col, label=lab, zorder=3,
           edgecolor='white', linewidth=0.6)
    ax.errorbar(x+(i-0.5)*w, v, yerr=[lo,hi], fmt='none', ecolor=MUTED,
                elinewidth=0.8, capsize=2, zorder=4)
ax.set_ylim(0,118); ax.set_yticks([0,25,50,75,100])
ax.set_ylabel('Successful runs (%)')
ax.set_title('(d) Operational success rate', fontsize=8.5, color=INK, pad=6)

for k,ax in enumerate(axes):
    ax.set_axisbelow(True)
    ax.grid(True, axis='y', color=GRID, linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(ALG, rotation=34, ha='right')
    if k==2: ax.set_xlim(-1.62, len(ALG)-0.45)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)

h,l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc='lower center', ncol=2, frameon=False,
           bbox_to_anchor=(0.5,-0.015), handlelength=1.6, columnspacing=2.0)
fig.tight_layout(rect=[0,0.045,1,1])
import os as _os
_OUT=_os.environ.get('SLAM_FIGDIR','.')
fig.savefig(_os.path.join(_OUT,'fig03_trajectory_repeatability_v2.pdf'), bbox_inches='tight')
fig.savefig('/tmp/fig03_v2.png', dpi=190, bbox_inches='tight')
print("ok")
