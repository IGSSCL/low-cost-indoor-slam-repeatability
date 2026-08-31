# -*- coding: utf-8 -*-
"""Figura 1: flujo metodologico, vectorial (sin material rasterizado).
Salida: fig01_methodology_pipeline_v3.pdf"""
import json, os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon

AQUI = os.path.dirname(os.path.abspath(__file__))
BLUE, VERM, TEAL = '#0072B2', '#D55E00', '#009E73'
INK, MUTED, LINE = '#1a1a1a', '#5f5f5f', '#c9ced4'

plt.rcParams.update({'font.size':6.5,'text.color':INK,'pdf.fonttype':42})
fig = plt.figure(figsize=(6.30, 3.50))
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis('off')

def caja(x,y,w,h,ec=LINE,fc='white',lw=0.7,r=1.3,z=2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",
                 ec=ec,fc=fc,lw=lw,zorder=z))
def banda(x,y,w,txt,col,h=5.2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=1.1",
                 ec='none',fc=col,zorder=2))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',color='white',fontsize=6.5,
            fontweight='bold',zorder=3)
def flecha(p0,p1,col=MUTED,lw=0.9,ms=7):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle='-|>',mutation_scale=ms,lw=lw,
                 color=col,zorder=5,shrinkA=0,shrinkB=0))

# ---------------- fila 1: cinco etapas ----------------
w, g, x0 = 18.0, 2.2, 1.0
X = [x0+i*(w+g) for i in range(5)]
TOP, BOT = 90.0, 47.0
banda(X[0], 92.6, w+g+w, 'DATA CAPTURE', BLUE)
banda(X[2], 92.6, 3*w+2*g, 'BACKEND PROCESSING', TEAL)
for i in range(5): caja(X[i], BOT, w, TOP-BOT)
for i in range(4): flecha((X[i]+w+0.2, (TOP+BOT)/2-2), (X[i+1]-0.2, (TOP+BOT)/2-2))

def cab(i, n, titulo):
    ax.add_patch(Circle((X[i]+2.4, TOP-3.6), 1.7, fc=BLUE, ec='none', zorder=4))
    ax.text(X[i]+2.4, TOP-3.6, str(n), ha='center', va='center', color='white',
            fontsize=6.2, fontweight='bold', zorder=5)
    ax.text(X[i]+w/2+1.8, TOP-3.6, titulo, ha='center', va='center', fontsize=6.6,
            fontweight='bold', color=INK, zorder=5)
def pie(i, txt):
    ax.plot([X[i]+2, X[i]+w-2],[BOT+9.6]*2, color=LINE, lw=0.6, zorder=3)
    ax.text(X[i]+w/2, BOT+5.0, txt, ha='center', va='center', fontsize=6.2,
            color=INK, zorder=5, linespacing=1.35)

CY = 68.5
# 1 entorno
cab(0,1,'Environment'); cx=X[0]+w/2
ax.add_patch(Rectangle((cx-5.0,CY-4.6),10.0,7.2,fc='none',ec=BLUE,lw=0.9,zorder=4))
ax.add_patch(Polygon([[cx-6.3,CY+2.6],[cx,CY+7.4],[cx+6.3,CY+2.6]],closed=True,
             fc='none',ec=BLUE,lw=0.9,zorder=4))
ax.add_patch(Rectangle((cx-1.5,CY-4.6),3.0,3.8,fc=BLUE,ec='none',alpha=.22,zorder=4))
pie(0,'Indoor, GNSS-denied:\nsingle-floor and multi-level')
# 2 sensor
cab(1,2,'Sensor'); cx=X[1]+w/2
ax.add_patch(Rectangle((cx-5.0,CY-4.8),10.0,5.6,fc='none',ec=BLUE,lw=0.9,zorder=4))
ax.add_patch(Polygon([[cx-3.4,CY+0.8],[cx-2.4,CY+4.4],[cx+2.4,CY+4.4],[cx+3.4,CY+0.8]],
             closed=True,fc='none',ec=BLUE,lw=0.9,zorder=4))
for a in np.linspace(-55,55,7):
    r=np.deg2rad(a)
    ax.plot([cx,cx+7.4*np.sin(r)],[CY+4.4,CY+4.4+5.2*np.cos(r)],color=BLUE,lw=0.4,
            alpha=.45,zorder=3)
pie(1,'Livox Mid-360 with internal\nIMU, handheld mount')
# 3 registro
cab(2,3,'Recording'); cx=X[2]+w/2
t=np.linspace(0,4*np.pi,200)
ax.plot(cx-6.4+12.8*t/t.max(), CY+1.4+2.6*np.sin(t)*np.exp(-t/16), color=BLUE, lw=0.8, zorder=4)
ax.add_patch(Circle((cx,CY-4.2),1.5,fc='none',ec=VERM,lw=0.9,zorder=4))
ax.add_patch(Circle((cx,CY-4.2),0.55,fc=VERM,ec='none',zorder=4))
ax.text(cx,CY-8.0,'13 + 12 repetitions',ha='center',va='center',fontsize=5.9,
        color=MUTED,zorder=5)
pie(2,'Recorded in MCAP; ROS 1\nbag where required')
# 4 SLAM
cab(3,4,'Processing'); cx=X[3]+w/2
for r_ in range(2):
    for c_ in range(3):
        ax.add_patch(FancyBboxPatch((cx-6.6+c_*4.6, CY-1.2-r_*4.8),3.6,3.4,
                     boxstyle="round,pad=0,rounding_size=0.5",
                     ec=BLUE,fc='white',lw=0.7,zorder=4))
ax.text(cx,CY+5.6,'six isolated containers',ha='center',va='center',fontsize=5.9,
        color=MUTED,zorder=5)
pie(3,'Six algorithms, executed\nsequentially on CPU')
# 5 salidas con trayectoria real
cab(4,5,'Outputs')
P = np.array(json.load(open(os.path.join(AQUI,'traj_exp2_pointlio.json'))))
sub = ax.inset_axes([(X[4]+4.4)/100,(BOT+12.4)/100,(w-8.8)/100,20.5/100])
sub.plot(P[:,0],P[:,1],color=BLUE,lw=0.7)
sub.scatter([P[0,0]],[P[0,1]],s=4,color=TEAL,zorder=5)
sub.set_xticks([]); sub.set_yticks([]); sub.set_aspect('equal')
for s in sub.spines.values(): s.set_color(LINE); s.set_linewidth(0.6)
ax.text(X[4]+w/2, TOP-8.4,'estimated trajectory',ha='center',va='center',
        fontsize=5.9,color=MUTED,zorder=5)
pie(4,'Trajectory (TUM) and\npoint cloud (PCD)')

# ---------------- fila 2: evaluacion ----------------
BY, BH = 4.0, 25.0
banda(x0, BY+BH+1.6, 5*w+4*g, 'TECHNICAL EVALUATION', VERM)
caja(x0, BY, 5*w+4*g, BH)
flecha((X[4]+w/2, BOT-0.3), (X[4]+w/2, BY+BH+1.4))

pasos = ['Rigid registration\nto the TLS\nreference (ICP)',
         'Declared filtering\nvoxel · outlier\nremoval · mask',
         'Bidirectional metrics\nChamfer · $P95$ · $P99$\ncoverage($\\tau$)',
         'Dimensional check\nplane-to-plane\ndistances',
         'Multicriteria synthesis\n$R_a$ · $Q_a$ · $C_a$\n ']
n = len(pasos); pw = (5*w+4*g-6.0)/n
for k,p in enumerate(pasos):
    px = x0+3.0+k*pw
    ax.add_patch(Circle((px+pw/2, BY+BH-7.0), 2.1, fc='white', ec=VERM, lw=0.8, zorder=4))
    ax.text(px+pw/2, BY+BH-7.0, str(k+1), ha='center', va='center', fontsize=6.0,
            color=VERM, fontweight='bold', zorder=5)
    tit, *det = p.split('\n')
    ax.text(px+pw/2, BY+BH-13.4, tit, ha='center', va='center', fontsize=6.4,
            fontweight='bold', color=INK, zorder=5)
    ax.text(px+pw/2, BY+BH-19.4, '\n'.join(det), ha='center', va='center',
            fontsize=6.1, color=MUTED, zorder=5, linespacing=1.32)
    if k < n-1:
        flecha((px+pw-1.0, BY+BH-7.0),(px+pw+1.0, BY+BH-7.0), col=LINE, lw=0.7, ms=5)

fig.savefig(os.path.join(AQUI,'fig01_methodology_pipeline_v3.pdf'))
fig.savefig('/tmp/fig01_v3.png', dpi=200)
print("ok")
