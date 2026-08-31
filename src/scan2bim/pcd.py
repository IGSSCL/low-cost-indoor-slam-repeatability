import numpy as np, sys, subprocess, os

def read_pcd_xyz(stream, voxel=0.02, chunk_pts=2_000_000):
    """Lee un PCD binario desde un stream y devuelve xyz voxelizado."""
    hdr, buf = {}, b''
    while True:
        b = stream.read(1)
        if not b: raise IOError('EOF en cabecera')
        buf += b
        if buf.endswith(b'\n'):
            line = buf.decode('ascii', 'replace').strip(); buf = b''
            if not line or line.startswith('#'): continue
            k, _, v = line.partition(' '); hdr[k] = v.strip()
            if k == 'DATA':
                break
    names = hdr['FIELDS'].split()
    sizes = [int(x) for x in hdr['SIZE'].split()]
    types = hdr['TYPE'].split()
    counts= [int(x) for x in hdr['COUNT'].split()]
    m = {'F':'f','U':'u','I':'i'}
    dt = np.dtype([(n, '%s%d'%(m[t], s), (c,) if c>1 else ())
                   for n,s,t,c in zip(names,sizes,types,counts)])
    npts = int(hdr['POINTS']); stride = dt.itemsize
    if hdr['DATA'].strip() == 'ascii':
        import pandas as pd
        ix = [names.index('x'), names.index('y'), names.index('z')]
        acc = []
        for ch in pd.read_csv(stream, sep=r'\s+', header=None, usecols=ix,
                              names=range(len(names)), chunksize=3_000_000,
                              dtype=np.float32, on_bad_lines='skip', engine='c'):
            xyz = ch.to_numpy(np.float32)
            xyz = xyz[np.isfinite(xyz).all(1)]
            if len(xyz):
                ij = np.floor(xyz/voxel).astype(np.int64)
                _, idx = np.unique(ij, axis=0, return_index=True)
                acc.append(xyz[idx])
        if not acc: return np.zeros((0,3), np.float32)
        xyz = np.concatenate(acc)
        ij = np.floor(xyz/voxel).astype(np.int64)
        _, idx = np.unique(ij, axis=0, return_index=True)
        return xyz[idx]
    acc = []
    left = npts
    while left > 0:
        k = min(chunk_pts, left)
        raw = stream.read(k*stride)
        got = len(raw)//stride
        if got == 0: break
        a = np.frombuffer(raw[:got*stride], dtype=dt)
        xyz = np.stack([a['x'], a['y'], a['z']], axis=1).astype(np.float32)
        xyz = xyz[np.isfinite(xyz).all(1)]
        if len(xyz):
            ij = np.floor(xyz/voxel).astype(np.int64)
            _, idx = np.unique(ij, axis=0, return_index=True)
            acc.append(xyz[idx])
        left -= got
    if not acc: return np.zeros((0,3), np.float32)
    xyz = np.concatenate(acc)
    ij = np.floor(xyz/voxel).astype(np.int64)
    _, idx = np.unique(ij, axis=0, return_index=True)
    return xyz[idx]

if __name__ == '__main__':
    zp, member, out, vox = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    p = subprocess.Popen(['unzip','-p',zp,member], stdout=subprocess.PIPE, bufsize=1024*1024)
    xyz = read_pcd_xyz(p.stdout, voxel=vox)
    p.stdout.close(); p.wait()
    np.save(out, xyz.astype(np.float32))
    print('%s -> %d puntos' % (member, len(xyz)))
