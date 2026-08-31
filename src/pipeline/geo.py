"""Pipeline geometrico SLAM vs TLS con registro explicito y trazabilidad.
Sustituye a evaluate_3d_maps_batch.py. numpy+scipy, sin open3d, memoria acotada."""
import numpy as np, os, json
from scipy.spatial import cKDTree

# ---------- lectura PCD por bloques con cuantizacion a voxel ----------
def _hdr(path):
    with open(path,'rb') as f: h=f.read(8192)
    i=h.find(b'DATA binary\n')
    if i<0:
        j=h.find(b'DATA ascii\n')
        if j<0: raise ValueError("PCD no soportado (ni binary ni ascii): "+path)
        i=j+11; fmt='ascii'
    else:
        i+=12; fmt='binary' 
    L={}
    for l in h[:i].split(b'\n'):
        if l and not l.startswith(b'#'):
            p=l.split()
            if p: L[p[0].decode()]=p[1:]
    n=int(L['POINTS'][0])
    sizes=[int(x) for x in L['SIZE']]; counts=[int(x) for x in L['COUNT']]
    names=[x.decode() for x in L['FIELDS']]
    off=0; xo=None
    for nm,s,c in zip(names,sizes,counts):
        if nm=='x': xo=off
        off+=s*c
    if xo is None: raise ValueError("sin campo x: "+path)
    return i,n,off,xo,len(names),names.index('x'),fmt

def _flush(parts, cap=12):
    if len(parts)>=cap:
        k=np.unique(np.concatenate(parts)); parts.clear(); parts.append(k)

def _pack(P, v, parts):
    P=P[np.isfinite(P).all(1)].astype(np.float64)
    if len(P):
        q=np.floor(P/v).astype(np.int64)+(1<<20)
        parts.append(np.unique((q[:,0]<<42)|(q[:,1]<<21)|q[:,2])); _flush(parts)

def _unpack(parts, v):
    k=np.unique(np.concatenate(parts)); parts.clear()
    out=np.empty((len(k),3),dtype=np.float32)
    for c,sh in enumerate((42,21,0)):
        out[:,c]=(((k>>sh)&0x1FFFFF).astype(np.float64)-(1<<20)+0.5)*v
    del k
    return out

def load_voxel(path, v=0.01, chunk=3_000_000):
    """Devuelve centros de voxel ocupados (float64 Nx3) y el n de puntos original."""
    i,n,stride,xo,nf,xi,fmt=_hdr(path)
    parts=[]
    if fmt=='ascii':
        rem=b''
        with open(path,'rb') as f:
            f.seek(i)
            while True:
                buf=f.read(1<<25)
                if not buf: break
                buf=rem+buf; k=buf.rfind(b'\n')
                if k<0: rem=buf; continue
                rem=buf[k+1:]
                a=np.fromstring(buf[:k].decode('ascii','ignore'),dtype=np.float64,sep=' ')
                a=a[:len(a)//nf*nf].reshape(-1,nf)
                _pack(a[:,xi:xi+3],v,parts)
        if rem.strip():
            a=np.fromstring(rem.decode('ascii','ignore'),dtype=np.float64,sep=' ')
            a=a[:len(a)//nf*nf].reshape(-1,nf)
            if len(a): _pack(a[:,xi:xi+3],v,parts)
        if not parts: return np.zeros((0,3)),n
        return _unpack(parts,v), n
    with open(path,'rb') as f:
        f.seek(i); done=0
        while done<n:
            m=min(chunk,n-done)
            b=np.frombuffer(f.read(m*stride),dtype=np.uint8)
            m=len(b)//stride
            if m==0: break
            P=b[:m*stride].reshape(m,stride)[:,xo:xo+12].copy().view(np.float32).reshape(-1,3)
            P=P[np.isfinite(P).all(1)].astype(np.float64)
            if len(P):
                q=np.floor(P/v).astype(np.int64)+(1<<20)
                k=(q[:,0]<<42)|(q[:,1]<<21)|q[:,2]
                parts.append(np.unique(k)); _flush(parts)
            done+=m
    if not parts: return np.zeros((0,3)),n
    return _unpack(parts,v), n

# ---------- registro ----------
def _icp(src, tgt_tree, tgt, T, max_corr, iters=30, tol=1e-5):
    prev=None
    for _ in range(iters):
        S=src@T[:3,:3].T+T[:3,3]
        d,j=tgt_tree.query(S,k=1,distance_upper_bound=max_corr)
        m=np.isfinite(d)
        if m.sum()<50: break
        A=S[m]; B=tgt[j[m]]
        ca,cb=A.mean(0),B.mean(0)
        H=(A-ca).T@(B-cb)
        U,_,Vt=np.linalg.svd(H); R=Vt.T@U.T
        if np.linalg.det(R)<0: Vt[2]*=-1; R=Vt.T@U.T
        dT=np.eye(4); dT[:3,:3]=R; dT[:3,3]=cb-R@ca
        T=dT@T
        rms=float(np.sqrt((d[m]**2).mean()))
        if prev is not None and abs(prev-rms)<tol: prev=rms; break
        prev=rms
    S=src@T[:3,:3].T+T[:3,3]
    d,_=tgt_tree.query(S,k=1,distance_upper_bound=max_corr)
    m=np.isfinite(d)
    return T, float(np.sqrt((d[m]**2).mean())) if m.any() else np.inf, float(m.mean())

def register(src, tgt, yaw_steps=24, seed=0):
    """Grueso: centroide + barrido de yaw. Fino: ICP multiescala. Devuelve T, rms, inliers."""
    rng=np.random.default_rng(seed)
    def sub(P,k):
        return P if len(P)<=k else P[rng.choice(len(P),k,replace=False)]
    s0,t0=sub(src,60000),sub(tgt,60000)
    tree0=cKDTree(t0)
    cs,ct=s0.mean(0),t0.mean(0)
    best=(None,np.inf)
    for a in np.linspace(0,2*np.pi,yaw_steps,endpoint=False):
        c,s=np.cos(a),np.sin(a)
        R=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
        T=np.eye(4); T[:3,:3]=R; T[:3,3]=ct-R@cs
        S=s0@R.T+T[:3,3]
        d,_=tree0.query(S,k=1,distance_upper_bound=3.0)
        sc=np.where(np.isfinite(d),d,3.0).mean()
        if sc<best[1]: best=(T,sc)
    T=best[0]
    for mc in (3.0,1.0,0.4,0.15):
        k=120000 if mc>0.5 else 300000
        s1,t1=sub(src,k),sub(tgt,k)
        T,rms,inl=_icp(s1,cKDTree(t1),t1,T,mc)
    return T,rms,inl

# ---------- metricas ----------
def metrics(est, gt, taus=(0.01,0.02,0.03,0.05,0.075,0.10,0.15,0.20), qcap=2_000_000, seed=11):
    # Tope de puntos de CONSULTA (los objetivos siempre completos). Muestreo aleatorio
    # insesgado: con n>=2e6 el error estandar de media y percentiles es despreciable.
    rng=np.random.default_rng(seed)
    est_q = est if len(est)<=qcap else est[rng.choice(len(est),qcap,replace=False)]
    gt_q  = gt  if len(gt) <=qcap else gt[rng.choice(len(gt),qcap,replace=False)]
    d_eg,_=cKDTree(gt).query(est_q,k=1)
    d_ge,_=cKDTree(est).query(gt_q,k=1)
    merged=np.concatenate([d_eg,d_ge])
    out={"n_est":len(est),"n_gt":len(gt),"n_consulta_est":len(est_q),"n_consulta_gt":len(gt_q),
         "precision_mean_m":float(d_eg.mean()),"recall_mean_m":float(d_ge.mean()),
         "chamfer_mean_m":float(0.5*(d_eg.mean()+d_ge.mean())),
         "chamfer_sum_m":float(d_eg.mean()+d_ge.mean()),
         "rmse_m":float(np.sqrt((merged**2).mean())),
         "median_m":float(np.median(merged)),
         "p95_m":float(np.percentile(merged,95)),
         "p99_m":float(np.percentile(merged,99)),
         "max_m":float(merged.max())}
    for t in taus:
        a=float((d_eg<=t).mean()); c=float((d_ge<=t).mean())
        out[f"accuracy@{t}"]=a; out[f"coverage@{t}"]=c
        out[f"fscore@{t}"]=float(2*a*c/max(a+c,1e-12))
    return out

def crop_to(P, ref, margin=1.0):
    lo,hi=ref.min(0)-margin, ref.max(0)+margin
    return P[np.all((P>=lo)&(P<=hi),1)]

def evaluate(est_path, tls_vox, voxel=0.01, margin=1.0, seed=0):
    est,n_raw=load_voxel(est_path,voxel)
    import gc; gc.collect()
    rec={"archivo":os.path.basename(est_path),"n_raw":n_raw,"n_voxel":len(est),"voxel_m":voxel}
    if len(est)<1000:
        rec["error"]="nube vacia o ilegible"; return rec
    T,rms,inl=register(est.astype(np.float64,copy=False),np.asarray(tls_vox,dtype=np.float64),seed=seed)
    est_a=(est.astype(np.float64)@T[:3,:3].T+T[:3,3])
    est_c=crop_to(est_a,tls_vox,margin)
    rec.update({"registro_rms_m":rms,"registro_inliers":inl,
                "T":np.round(T,6).tolist(),
                "n_tras_recorte":len(est_c),
                "frac_fuera_del_TLS":1.0-len(est_c)/max(len(est_a),1)})
    if len(est_c)<1000:
        rec["error"]="sin solape con el TLS tras el registro"; return rec
    ec64=np.asarray(est_c,dtype=np.float64); g64=np.asarray(tls_vox,dtype=np.float64)
    rec.update(metrics(ec64,g64))
    # Segunda pasada con filtrado automatico declarado (ver limpieza.py). Se guarda con
    # prefijo 'lim_' para poder comparar crudo vs filtrado sin volver a procesar.
    try:
        from limpieza import metricas_limpias
        for k,v in metricas_limpias(ec64,g64).items(): rec["lim_"+k]=v
    except Exception as e:
        rec["lim_error"]=f"{type(e).__name__}: {e}"
    return rec
