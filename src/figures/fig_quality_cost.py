# -*- coding: utf-8 -*-
"""Figura: calidad geometrica (D_bi, registro v2) frente a coste de CPU, con frontera de
Pareto. Tamano del marcador = tamano del PCD exportado. Datos: data/runwise/map_quality.jsonl y
data/runwise/computational.csv (medianas por algoritmo y escenario)."""
import json, csv, os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
AQUI=os.path.dirname(os.path.abspath(__file__))
REPO=os.environ.get('SLAM_REPO') or os.path.abspath(os.path.join(AQUI,'..','..'))
V=[json.loads(l) for l in open(os.path.join(REPO,'data','runwise','map_quality.jsonl'))]
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
COL={'POINT-LIO':'#0072B2','FAST-LIO2':'#D55E00','HDMapping-LIO':'#009E73','D-LIO':'#E69F00','LIO-LIVOX':'#CC79A7','KISS-ICP':'#56B4E9'}
MRK={'POINT-LIO':'o','FAST-LIO2':'s','HDMapping-LIO':'^','D-LIO':'D','LIO-LIVOX':'v','KISS-ICP':'P'}
INK='#1a1a1a'; MUTED='#6b6b6b'; GRID='#e3e3e1'
# Tamano del PCD exportado (MB), Tabla 6 del articulo (medianas)
PCD={('EXP1','POINT-LIO'):152.8,('EXP1','HDMapping-LIO'):657.2,('EXP1','FAST-LIO2'):19.0,('EXP1','D-LIO'):5.1,('EXP1','LIO-LIVOX'):715.0,('EXP1','KISS-ICP'):21.6,
     ('EXP2','POINT-LIO'):111.1,('EXP2','HDMapping-LIO'):605.4,('EXP2','FAST-LIO2'):17.7,('EXP2','D-LIO'):4.1,('EXP2','LIO-LIVOX'):792.0,('EXP2','KISS-ICP'):20.5}
EFF={}
for r in csv.DictReader(open(os.path.join(REPO,'data','runwise','computational.csv'))):
    EFF[(r['experiment'].replace('Exp ','EXP'),r['algorithm'])]=r
plt.rcParams.update({'font.size':8,'axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
    'axes.edgecolor':MUTED,'axes.linewidth':0.6,'xtick.color':MUTED,'ytick.color':MUTED,
    'text.color':INK,'axes.labelcolor':INK,'pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(6.4,2.9))
for ax,(e,tit) in zip(axes,[('EXP1','Experiment 1 — single floor'),('EXP2','Experiment 2 — multi-level')]):
    pts=[]
    for a in ALG:
        rs=[r for r in V if r['exp']==e and r['algoritmo'].replace('_Denso','')==a and r['registro_inliers']>=0.05]
        y=np.median([r['lim_chamfer_mean_m'] for r in rs])*100
        f=EFF[(e,a)]; x=float(f['cpu_core_s']); pcd=PCD[(e,a)]
        pts.append((x,y,a))
        ax.scatter(x,y,s=18+pcd*0.28,color=COL[a],marker=MRK[a],edgecolor='white',linewidth=0.6,zorder=3,alpha=0.95)
        ax.annotate(a,(x,y),xytext=(5,4),textcoords='offset points',fontsize=6.8,color=INK)
    # frontera de Pareto (menor coste y menor D_bi)
    fr=[]; best=np.inf
    for x,y,a in sorted(pts):
        if y<best: fr.append((x,y)); best=y
    ax.plot([p[0] for p in fr],[p[1] for p in fr],color=MUTED,linewidth=0.9,linestyle=(0,(3,2)),zorder=2)
    ax.set_xscale('log'); ax.set_title(tit,fontsize=8.5,pad=6)
    ax.set_xlabel('CPU cost (core-s, log scale)')
    ax.grid(True,color=GRID,linewidth=0.6); ax.set_axisbelow(True)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)
    ax.set_xlim(35,1400)
axes[0].set_ylabel('$D_{bi}$ to TLS (cm), lower is better')
for s,l in ((20,'~20 MB'),(150,'~150 MB'),(700,'~700 MB')):
    axes[1].scatter([],[],s=18+s*0.28,color='#b0b0b0',edgecolor='white',label=l)
axes[1].legend(title='Exported PCD',loc='upper right',frameon=False,fontsize=6.8,title_fontsize=7,labelspacing=1.1)
fig.tight_layout()
out=os.environ.get('SLAM_FIGDIR','.')
fig.savefig(os.path.join(out,'fig_quality_vs_cpu_cost.pdf'),bbox_inches='tight')
fig.savefig(os.path.join(out,'fig_quality_vs_cpu_cost.png'),dpi=200,bbox_inches='tight')
print('ok')
