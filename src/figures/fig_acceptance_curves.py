"""Acceptance curves: median coverage of the TLS reference against tolerance, by algorithm
and scenario. Data: data/runwise/map_quality.jsonl (registration v2), via datos_v2.py."""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter

TAUS=[10,20,30,50,75,100,150,200]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datos_v2 import cobertura, TAUS_MM
assert TAUS == TAUS_MM
COV=cobertura()
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
# orden de tonos fijo y validado (CVD), asignado a la entidad, no al rango
COL={'POINT-LIO':'#0072B2','FAST-LIO2':'#D55E00','HDMapping-LIO':'#009E73',
     'D-LIO':'#E69F00','LIO-LIVOX':'#CC79A7','KISS-ICP':'#56B4E9'}
MRK={'POINT-LIO':'o','FAST-LIO2':'s','HDMapping-LIO':'^','D-LIO':'D','LIO-LIVOX':'v','KISS-ICP':'P'}
INK='#1a1a1a'; MUTED='#6b6b6b'; GRID='#e3e3e1'

plt.rcParams.update({'font.size':8,'axes.labelsize':8.5,'xtick.labelsize':7.5,
                     'ytick.labelsize':7.5,'legend.fontsize':7.5,
                     'axes.edgecolor':MUTED,'axes.linewidth':0.6,
                     'xtick.color':MUTED,'ytick.color':MUTED,
                     'text.color':INK,'axes.labelcolor':INK,'pdf.fonttype':42})

fig,axes=plt.subplots(1,2,figsize=(6.3,2.85),sharey=True)
for ax,(exp,tit) in zip(axes,[('EXP1','Experiment 1 — single floor'),
                              ('EXP2','Experiment 2 — multi-level')]):
    ax.set_axisbelow(True)
    ax.grid(True,which='major',color=GRID,linewidth=0.6)
    for t in (20,50):
        ax.axvline(t,color=MUTED,linewidth=0.6,linestyle=(0,(2,3)),alpha=.7,zorder=1)
    for a in ALG:
        ax.plot(TAUS,COV[f'{exp}|{a}'],color=COL[a],marker=MRK[a],markersize=3.6,
                linewidth=1.6,markeredgecolor='white',markeredgewidth=0.5,
                label=a,zorder=3,clip_on=False)
    ax.set_xscale('log')
    ax.xaxis.set_major_locator(FixedLocator(TAUS))
    ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in TAUS]))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.set_xlim(9.3,215); ax.set_ylim(0,1.0)
    ax.set_xlabel('Tolerance $\\tau$ (mm)')
    ax.set_title(tit,fontsize=8.5,color=INK,pad=6)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)
    ax.text(20*1.06,0.015,'2 cm',ha='left',va='bottom',fontsize=6.5,color=MUTED)
    ax.text(50*1.06,0.015,'5 cm',ha='left',va='bottom',fontsize=6.5,color=MUTED)
axes[0].set_ylabel('Coverage (fraction of TLS points)')
axes[0].set_yticks([0,.2,.4,.6,.8,1.0])
h,l=axes[0].get_legend_handles_labels()
fig.legend(h,l,loc='lower center',ncol=6,frameon=False,
           bbox_to_anchor=(0.5,-0.03),handlelength=1.8,columnspacing=1.4,handletextpad=0.5)
fig.tight_layout(rect=[0,0.075,1,1])
import os as _os
_OUT=_os.environ.get('SLAM_FIGDIR','.')
fig.savefig(_os.path.join(_OUT,'fig_acceptance_curves.pdf'),bbox_inches='tight')
print("ok")
