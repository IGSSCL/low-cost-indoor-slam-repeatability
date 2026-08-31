# -*- coding: utf-8 -*-
"""Verificacion dimensional: error en distancias entre planos, no en posiciones.

Por que distancias y no coordenadas: una distancia entre dos planos paralelos es invariante
bajo transformacion rigida, asi que NO hereda el error del registro mapa-TLS. Es tambien la
magnitud que un profesional AEC mide en obra -- ancho de vano, separacion entre muros, altura
libre -- de modo que el resultado se lee en el idioma del gremio y no en el de la robotica.

Metodo, sin intervencion de operador:
 1. En el TLS se detectan planos dominantes por histograma de coordenadas en cada eje.
    Un pico = un muro (X, Y) o un piso/cielo (Z).
 2. Se toman las distancias entre pares de planos consecutivos de al menos `dim_min`: son
    las "dimensiones". El minimo descarta separaciones de mobiliario.
 3. En el mapa SLAM ya registrado se localiza el pico mas cercano a cada plano del TLS y se
    mide la misma distancia. El error dimensional es la diferencia.

`tol_pico` es deliberadamente estrecho (12 cm). Con una tolerancia amplia el emparejamiento
puede tomar un plano fisico distinto, y eso produce errores de ~300 mm identicos en todos los
algoritmos -- firma inconfundible de un fallo de emparejamiento y no de reconstruccion.
"""
import numpy as np

def planos(P, eje, bins=2000, min_frac=0.004, sep_m=0.30):
    """Picos del histograma de coordenadas en `eje`. Devuelve posiciones en metros."""
    x=P[:,eje]
    h,b=np.histogram(x,bins=bins)
    c=(b[:-1]+b[1:])/2
    umbral=max(h.max()*0.10, len(x)*min_frac/bins*20)
    idx=[i for i in range(1,len(h)-1) if h[i]>=umbral and h[i]>=h[i-1] and h[i]>=h[i+1]]
    idx.sort(key=lambda i:-h[i])
    sel=[]
    for i in idx:
        if all(abs(c[i]-c[j])>=sep_m for j in sel): sel.append(i)
    return np.sort(c[sel]), h, c

def dimensiones(P, ejes=(0,1,2), max_por_eje=6):
    """Distancias entre planos consecutivos, por eje."""
    out=[]
    for e in ejes:
        p,_,_=planos(P,e)
        p=p[:max_por_eje]
        for i in range(len(p)-1):
            out.append((e,float(p[i]),float(p[i+1]),float(p[i+1]-p[i])))
    return out

def compara(est, gt, tol_pico=0.12, ejes=(0,1,2), dim_min=1.0):
    """Para cada dimension del TLS, mide la misma en el mapa SLAM. Devuelve lista de dict."""
    res=[]
    for e in ejes:
        pg,_,_=planos(gt,e)
        pe,_,_=planos(est,e)
        if len(pe)<2: continue
        for i in range(len(pg)-1):
            a,b=pg[i],pg[i+1]
            ca=pe[np.argmin(abs(pe-a))]; cb=pe[np.argmin(abs(pe-b))]
            if abs(ca-a)>tol_pico or abs(cb-b)>tol_pico or ca==cb: continue
            if (b-a)<dim_min: continue
            dg=float(b-a); de=float(cb-ca)
            res.append({"eje":"XYZ"[e],"dim_TLS_m":round(dg,4),"dim_SLAM_m":round(de,4),
                        "error_m":round(de-dg,4),"error_rel":round((de-dg)/dg,5)})
    return res

def resumen(res):
    if not res: return {}
    e=np.array([r["error_m"] for r in res])
    return {"n_dimensiones":len(res),"error_medio_m":float(e.mean()),
            "error_abs_mediano_m":float(np.median(abs(e))),
            "error_abs_medio_m":float(abs(e).mean()),"error_abs_p95_m":float(np.percentile(abs(e),95)),
            "error_abs_max_m":float(abs(e).max()),
            "sesgo_relativo":float(np.mean([r["error_rel"] for r in res])),
            "dentro_5mm":float((abs(e)<=0.005).mean()),"dentro_15mm":float((abs(e)<=0.015).mean()),
            "dentro_50mm":float((abs(e)<=0.050).mean())}
