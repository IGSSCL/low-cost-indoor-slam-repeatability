# -*- coding: utf-8 -*-
"""Figura 2: plataforma de adquisicion y procesamiento. Vectorial.
Salida: fig02_platform_runtime_v3.pdf"""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon

AQUI = os.path.dirname(os.path.abspath(__file__))
BLUE, VERM, TEAL = '#0072B2', '#D55E00', '#009E73'
INK, MUTED, LINE = '#1a1a1a', '#5f5f5f', '#c9ced4'

plt.rcParams.update({'font.size':6.5,'text.color':INK,'pdf.fonttype':42})
fig = plt.figure(figsize=(6.30, 3.80))
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis('off')

def caja(x,y,w,h,ec=LINE,fc='white',lw=0.7,r=1.3,z=2,ls='solid'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",
                 ec=ec,fc=fc,lw=lw,zorder=z,linestyle=ls))
def cabecera(x,y,w,txt,col,h=5.0):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=1.1",
                 ec='none',fc=col,zorder=3))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',color='white',fontsize=6.5,
            fontweight='bold',zorder=4)
def flecha(p0,p1,col=BLUE,lw=1.0,ms=7,ls='-'):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle='-|>',mutation_scale=ms,lw=lw,
                 color=col,zorder=6,shrinkA=0,shrinkB=0,linestyle=ls))

# ---- cadena principal: cinco bloques ----
w, g, x0 = 17.6, 2.2, 1.0
X = [x0+i*(w+g) for i in range(5)]
TOP, BOT = 92.0, 44.0
tit = ['LiDAR sensor','Acquisition unit','Middleware','SLAM processing','Outputs']
for i in range(5):
    caja(X[i], BOT, w, TOP-BOT-5.0)
    cabecera(X[i], TOP-5.0, w, f'{i+1}.  {tit[i]}', BLUE if i<2 else TEAL)
for i in range(4):
    flecha((X[i]+w+0.2, (TOP+BOT)/2-3), (X[i+1]-0.2, (TOP+BOT)/2-3))

def texto(i, lineas, y0=None, fs=6.2):
    y = (y0 if y0 is not None else TOP-12.0)
    for t,st in lineas:
        ax.text(X[i]+w/2, y, t, ha='center', va='center', fontsize=fs,
                color=INK if st=='b' else MUTED,
                fontweight='bold' if st=='b' else 'normal', zorder=5, linespacing=1.3)
        y -= 4.6 if st=='b' else 4.2

# 1 sensor
cx = X[0]+w/2; cy = 76
ax.add_patch(Rectangle((cx-4.6,cy-4.4),9.2,5.2,fc='none',ec=BLUE,lw=0.9,zorder=4))
ax.add_patch(Polygon([[cx-3.1,cy+0.8],[cx-2.2,cy+4.0],[cx+2.2,cy+4.0],[cx+3.1,cy+0.8]],
             closed=True,fc='none',ec=BLUE,lw=0.9,zorder=4))
texto(0,[('Livox Mid-360','b'),('LiDAR + internal IMU','n'),
         ('360° × 59° field of view','n'),('handheld tripod mount','n')], y0=64)
# 2 unidad de adquisicion
cx = X[1]+w/2; cy = 76
ax.add_patch(Rectangle((cx-5.4,cy-2.0),10.8,6.4,fc='none',ec=BLUE,lw=0.9,zorder=4))
ax.add_patch(Polygon([[cx-7.0,cy-2.6],[cx+7.0,cy-2.6],[cx+5.6,cy-2.0],[cx-5.6,cy-2.0]],
             closed=True,fc='none',ec=BLUE,lw=0.9,zorder=4))
texto(1,[('Portable workstation','b'),('Ubuntu 24.04 · ROS 2 Jazzy','n'),
         ('livox_ros_driver2','n'),('Intel i7 · 24 GB · CPU only','n')], y0=64)
# 3 middleware
cx = X[2]+w/2; cy = 76
ax.add_patch(FancyBboxPatch((cx-5.0,cy-3.4),10.0,7.0,
             boxstyle="round,pad=0,rounding_size=0.8",fc='none',ec=BLUE,lw=0.9,zorder=4))
for k in range(3):
    ax.plot([cx-3.2,cx+3.2],[cy-1.4+k*1.9]*2,color=BLUE,lw=0.5,zorder=5)
texto(2,[('Recording','b'),('MCAP as native format','n'),
         ('ROS 1 bag where an','n'),('implementation needs it','n')], y0=64)
# 4 SLAM
cx = X[3]+w/2; cy = 76
for r_ in range(2):
    for c_ in range(3):
        ax.add_patch(FancyBboxPatch((cx-6.2+c_*4.3, cy-2.6-r_*4.0),3.4,3.0,
                     boxstyle="round,pad=0,rounding_size=0.4",ec=BLUE,fc='white',
                     lw=0.7,zorder=4))
ax.text(cx, cy+3.0,'six Docker containers',ha='center',va='center',fontsize=5.9,
        color=MUTED,zorder=5)
texto(3,[('Six algorithms','b'),('FAST-LIO2 · POINT-LIO','n'),
         ('D-LIO · HDMapping-LIO','n'),('LIO-LIVOX · KISS-ICP','n')], y0=64)
# 5 salidas
texto(4,[('Trajectory (TUM)','b'),('timestamp, position,\nquaternion','n'),
         ('Point cloud (PCD)','b'),('one map per capture','n')], y0=78)
texto(4,[('13 + 12 repetitions','b')], y0=57)

# ---- rama de referencia externa ----
BY, BH = 6.0, 30.0
caja(x0, BY, w*2+g, BH, ec=VERM, ls=(0,(4,2)))
ax.text(x0+(w*2+g)/2, BY+BH-6.0,'External geometric reference', ha='center',
        va='center', fontsize=6.6, fontweight='bold', color=VERM, zorder=5)
cx = x0+(w*2+g)/2; cy = BY+BH-15.0
ax.add_patch(Rectangle((cx-2.6,cy-1.0),5.2,4.0,fc='none',ec=VERM,lw=0.9,zorder=4))
ax.add_patch(Circle((cx,cy+1.0),1.1,fc='none',ec=VERM,lw=0.8,zorder=5))
for dx in (-2.2,0,2.2):
    ax.plot([cx+dx*0.5,cx+dx],[cy-1.0,cy-5.4],color=VERM,lw=0.7,zorder=4)
ax.text(cx, BY+5.2,'Trimble X9 TLS · 6 and 16 stations\ncloud-to-cloud refinement, no targets',
        ha='center', va='center', fontsize=6.2, color=MUTED, zorder=5, linespacing=1.35)

xr = x0+2*(w+g)
caja(xr, BY, w, BH, ec=TEAL)
ax.text(xr+w/2, BY+BH-6.0,'Rigid registration', ha='center', va='center',
        fontsize=6.6, fontweight='bold', color=TEAL, zorder=5)
ax.text(xr+w/2, BY+BH-16.0,'ICP, reported per pair\nwith RMS and inlier fraction',
        ha='center', va='center', fontsize=6.2, color=MUTED, zorder=5, linespacing=1.35)

xc = x0+3*(w+g)
caja(xc, BY, 2*w+g, BH, ec=TEAL)
ax.text(xc+(2*w+g)/2, BY+BH-6.0,'Geometric comparison', ha='center', va='center',
        fontsize=6.6, fontweight='bold', color=TEAL, zorder=5)
ax.text(xc+(2*w+g)/2, BY+BH-17.0,
        'Trajectory metrics  ·  map geometric quality\ndimensional verification  ·  multicriteria synthesis',
        ha='center', va='center', fontsize=6.2, color=MUTED, zorder=5, linespacing=1.5)

flecha((x0+2*w+g+0.2, BY+BH/2),(xr-0.2, BY+BH/2), col=VERM, ls=(0,(3,2)))
flecha((xr+w+0.2, BY+BH/2),(xc-0.2, BY+BH/2), col=TEAL)
flecha((X[4]+w/2, BOT-0.3),(X[4]+w/2, BY+BH+0.4), col=TEAL)

# ---- leyenda ----
ly = 2.2
for k,(col,ls,lab) in enumerate([(BLUE,'-','Data flow'),(TEAL,'-','Evaluation flow'),
                                 (VERM,(0,(3,2)),'Reference flow')]):
    lx = 24 + k*23
    ax.add_patch(FancyArrowPatch((lx,ly),(lx+5,ly),arrowstyle='-|>',mutation_scale=6,
                 lw=1.0,color=col,linestyle=ls,zorder=6,shrinkA=0,shrinkB=0))
    ax.text(lx+6.4, ly, lab, ha='left', va='center', fontsize=6.2, color=INK, zorder=6)

fig.savefig(os.path.join(AQUI,'fig02_platform_runtime_v3.pdf'))
fig.savefig('/tmp/fig02_v3.png', dpi=200)
print("ok")
