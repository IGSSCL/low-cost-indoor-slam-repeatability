# -*- coding: utf-8 -*-
"""Indice multicriterio completo: subindices por experimento, TOPSIS, VIKOR, sensibilidad."""
import json,os,numpy as np
from paths import raiz, repo
AQUI = raiz()
ALG=['POINT-LIO','FAST-LIO2','HDMapping-LIO','D-LIO','LIO-LIVOX','KISS-ICP']
RUNS={'EXP1':[str(i) for i in range(1,14)],'EXP2':[str(i) for i in range(1,13)]}
EP, DELTA = 3.15, 0.25
M={(r['exp'],r['run'],r['algoritmo'].replace('_Denso','')):r for r in
   map(json.loads,open(os.path.join(AQUI,'resultados_con_filtrado.jsonl'),encoding='utf-8'))}
T={(x['exp'],x['run'],x['algoritmo']):x for x in
   map(json.loads,open(os.path.join(AQUI,'trayectorias.jsonl'),encoding='utf-8'))}
DIM={(x['exp'],x['run'],x['algoritmo'].replace('_Denso','')):x for x in
     map(json.loads,open(os.path.join(AQUI,'dimensional.jsonl'),encoding='utf-8'))}
def okp(e,r,a):
    x=M.get((e,r,a)); return x is not None and x.get('registro_inliers',0)>=0.05
def med(e,a,k,src='M'):
    o=[]
    for r in RUNS[e]:
        if not okp(e,r,a): continue
        x=(M if src=='M' else DIM if src=='D' else T).get((e,r,a))
        if x and k in x: o.append(x[k])
    return float(np.median(o)) if o else np.nan
def cvL(e,a):
    v=[T[(e,r,a)]['L_10hz_m'] for r in RUNS[e] if (e,r,a) in T and okp(e,r,a)]
    return float(np.std(v,ddof=1)/np.mean(v)*100) if len(v)>2 else np.nan
SR={'EXP1':{a:1.0 for a in ALG},
    'EXP2':{'POINT-LIO':11/12,'FAST-LIO2':1.0,'HDMapping-LIO':1.0,'D-LIO':1.0,'LIO-LIVOX':10/12,'KISS-ICP':1.0}}
# Coste computacional por algoritmo: reloj de pared (s), coste de CPU acumulado
# (core-segundos = duracion x carga media) y memoria residente maxima (MB).
# Medido por el contenedor de cada algoritmo; mediana sobre las repeticiones.
# Externalizado a data/runwise/computational.csv para que sea inspeccionable.
import csv as _csv
_EFFCSV=os.path.join(repo(),'data','runwise','computational.csv')
EFF={'EXP1':{},'EXP2':{}}
for _r in _csv.DictReader(open(_EFFCSV,encoding='utf-8')):
    EFF[_r['experiment'].replace('Exp ','EXP')][_r['algorithm']]=(
        float(_r['wall_clock_s']), float(_r['cpu_core_s']), float(_r['peak_rss_mb']))

def nrm(c,mm):
    c=np.array(c,float); lo,hi=np.nanmin(c),np.nanmax(c)
    return np.ones_like(c)*0.5 if hi-lo<1e-15 else ((c-lo)/(hi-lo) if mm else (hi-c)/(hi-lo))
def sub(cols): return dict(zip(ALG,np.mean(cols,axis=0)))
def Q(e): return sub([nrm([med(e,a,'lim_chamfer_mean_m') for a in ALG],False),
                      nrm([med(e,a,'lim_p95_exactitud_m') for a in ALG],False),
                      nrm([med(e,a,'lim_p99_m') for a in ALG],False),
                      nrm([med(e,a,'lim_coverage@0.02') for a in ALG],True),
                      nrm([med(e,a,'error_abs_mediano_m','D') for a in ALG],False)])
def R(e):
    # Ra recoge solo comportamiento atribuible al algoritmo.
    #  - Se retiro la dispersion de la velocidad de marcha: se estima de la propia
    #    trayectoria de cada algoritmo, de modo que mezcla la conducta del operador con
    #    el ruido de estimacion y el estudio no puede separarlos. Se conserva como
    #    covariable experimental en el analisis de sensibilidad a la velocidad.
    #  - El termino vertical entra en AMBOS escenarios. En el multinivel se mide contra
    #    la altura de entrepiso del TLS (EP); en el monoplanta, contra la excursion
    #    esperable de la mano (DELTA), porque la ruta no cambia de nivel. El orden
    #    resultante es insensible a DELTA entre 0 y 1 m.
    c=[nrm([cvL(e,a) for a in ALG],False),
       nrm([med(e,a,'cierre_m','T') for a in ALG],False),
       nrm([abs(med(e,a,'dZ_m','T')-(EP if e=='EXP2' else DELTA)) for a in ALG],False)]
    return sub(c)
def C(e):
    t=[EFF[e][a][0] for a in ALG]; c=[EFF[e][a][1] for a in ALG]; m=[EFF[e][a][2] for a in ALG]
    return sub([nrm(t,False),nrm(c,False),nrm(m,False)])
def topsis(Mx,w):
    X=Mx/np.sqrt((Mx**2).sum(0)); V=X*w
    ip,im=V.max(0),V.min(0)
    dp=np.sqrt(((V-ip)**2).sum(1)); dm=np.sqrt(((V-im)**2).sum(1))
    return dm/(dp+dm)
def vikor(Mx,w,v=0.5):
    f_,f0=Mx.max(0),Mx.min(0)
    d=np.where(f_-f0==0,1,f_-f0)
    S=(w*(f_-Mx)/d).sum(1); Rr=(w*(f_-Mx)/d).max(1)
    def rescale(x): return (x-x.min())/(x.max()-x.min()) if x.max()>x.min() else np.zeros_like(x)
    return v*rescale(S)+(1-v)*rescale(Rr)
if __name__=="__main__":
    out={}
    for e in ('EXP1','EXP2'): out[e]=dict(R=R(e),Q=Q(e),C=C(e))
    AG={k:{a:0.5*(out['EXP1'][k][a]+out['EXP2'][k][a]) for a in ALG} for k in ('R','Q','C')}
    Mx=np.array([[AG['R'][a],AG['Q'][a],AG['C'][a]] for a in ALG])
    w=np.array([0.30,0.50,0.20])
    Sa={a:float(Mx[i]@w) for i,a in enumerate(ALG)}
    tp=topsis(Mx,w); vk=vikor(Mx,w)
    res=dict(por_exp={e:{k:{a:round(out[e][k][a],3) for a in ALG} for k in 'RQC'} for e in out},
             agregado={k:{a:round(AG[k][a],3) for a in ALG} for k in 'RQC'},
             Sa={a:round(Sa[a],3) for a in ALG},
             TOPSIS={a:round(float(tp[i]),3) for i,a in enumerate(ALG)},
             VIKOR={a:round(float(vk[i]),3) for i,a in enumerate(ALG)},
             SR_exp2={a:round(SR['EXP2'][a],4) for a in ALG})
    esc={'Base':(.30,.50,.20),'Uniform':(1/3,1/3,1/3),'Balanced':(.40,.40,.20),'Efficiency':(.30,.30,.40)}
    res['escenarios']={n:{a:round(float(Mx[i]@np.array(ww)),3) for i,a in enumerate(ALG)} for n,ww in esc.items()}
    for e in ('EXP1','EXP2'):
        S={a:0.30*out[e]['R'][a]+0.50*out[e]['Q'][a]+0.20*out[e]['C'][a] for a in ALG}
        res.setdefault('Sa_por_exp',{})[e]={a:round(S[a],3) for a in ALG}
    json.dump(res,open(os.path.join(AQUI,'indice_completo.json'),'w'),indent=1)
    for k in ('Sa','TOPSIS','VIKOR'):
        print(k,':', ' > '.join(sorted(ALG,key=lambda a:-res[k][a] if k!='VIKOR' else res[k][a])))
    print('Sa:',res['Sa']); print('escenarios:',res['escenarios'])
    print('Sa por exp:',res['Sa_por_exp'])
