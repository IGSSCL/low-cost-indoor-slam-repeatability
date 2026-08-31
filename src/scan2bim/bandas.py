import numpy as np, sys, subprocess, json
sys.path.insert(0,'.')
import pcd as P

def leer_banda(zp, member, M, lo, hi, planos, w=0.35):
    """Lee el PCD completo y guarda, SIN voxelizar, solo los puntos cerca de los planos."""
    p = subprocess.Popen(['unzip','-p',zp,member], stdout=subprocess.PIPE, bufsize=4*1024*1024)
    st = p.stdout
    hdr, buf = {}, b''
    while True:
        b = st.read(1)
        if not b: raise IOError('EOF')
        buf += b
        if buf.endswith(b'\n'):
            line = buf.decode('ascii','replace').strip(); buf=b''
            if not line or line.startswith('#'): continue
            k,_,v = line.partition(' '); hdr[k]=v.strip()
            if k=='DATA': break
    names=hdr['FIELDS'].split(); sizes=[int(x) for x in hdr['SIZE'].split()]
    types=hdr['TYPE'].split(); counts=[int(x) for x in hdr['COUNT'].split()]
    m={'F':'f','U':'u','I':'i'}
    dt=np.dtype([(n,'%s%d'%(m[t],s),(c,) if c>1 else ()) for n,s,t,c in zip(names,sizes,types,counts)])
    R=M[:3,:3].T; t=M[:3,3]
    out=[]
    def procesa(xyz):
        xyz=xyz[np.isfinite(xyz).all(1)]
        if not len(xyz): return
        Q=(xyz.astype(np.float64)@R)+t
        sel=np.all((Q>=lo)&(Q<=hi),axis=1)
        if not sel.any(): return
        Q=Q[sel]
        keep=np.zeros(len(Q),bool)
        for z0 in planos: keep |= np.abs(Q[:,2]-z0)<w
        if keep.any(): out.append(Q[keep])
    if hdr['DATA'].strip()=='ascii':
        import pandas as pd
        ix=[names.index('x'),names.index('y'),names.index('z')]
        for ch in pd.read_csv(st,sep=r'\s+',header=None,usecols=ix,names=range(len(names)),
                              chunksize=3_000_000,dtype=np.float32,on_bad_lines='skip',engine='c'):
            procesa(ch.to_numpy(np.float32))
    else:
        npts=int(hdr['POINTS']); stride=dt.itemsize; left=npts
        while left>0:
            k=min(2_000_000,left); raw=st.read(k*stride); got=len(raw)//stride
            if got==0: break
            a=np.frombuffer(raw[:got*stride],dtype=dt)
            procesa(np.stack([a['x'],a['y'],a['z']],axis=1))
            left-=got
    st.close(); p.wait()
    return np.concatenate(out) if out else np.zeros((0,3))
