#!/usr/bin/env python3
"""Registro v2 SLAM -> TLS, robusto a la inclinacion del marco de salida (ICT49, P2-P3).

Problema (HALLAZGO_ICT49_INCLINACION.md): FAST-LIO2, LIO-LIVOX, KISS-ICP y en parte
HDMapping-LIO entregan el mapa en el marco inicial del sensor, inclinado hasta ~45 grados.
El registro v1 (`geo.register`) solo barre la guinada y el ICP cae en minimos locales.

Solucion: antes del registro v1 se NIVELA cada mapa con su propia geometria, sin mirar el
TLS. Para cada direccion candidata u (inclinacion 0-70 grados respecto del +z del mapa) se
proyectan los puntos sobre u y se mide cuan concentrado queda el histograma de alturas
(bins de 2 cm): los pisos, techos y losas producen picos agudos solo cuando u es la
vertical verdadera. Busqueda gruesa cada 2 grados y fina cada 0,25 grados alrededor del
optimo. Despues se aplica `geo.register` sin cambios (centroide + 24 guinadas + ICP
multiescala). T_v2 = T_icp @ R_nivel.

Por par escribe una fila en out/map_quality_v2.jsonl (publicada como data/runwise/map_quality.jsonl) con el mismo esquema que
resultados_con_filtrado.jsonl (metricas crudas + lim_*), mas:
  nivel_incl_deg (inclinacion estimada del marco), T_v1 y registro_inliers_v1.

Uso:  python reg_v2.py auto [presupuesto_s]   |   python reg_v2.py todo
      python reg_v2.py paso EXP RUN ALG
"""
import os, sys, json, time, zipfile, shutil
import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SLAM_REPO") or os.path.abspath(os.path.join(AQUI, "..", ".."))
# SLAM_DATA: folder holding "EXP 1/Nubes de puntos", "EXP 2/Nubes de punto" (the zipped
# reconstructions) and the TLS references tls_e1.npy / tls_e2.npy. Not in this repository.
DATA = os.environ.get("SLAM_DATA") or os.path.abspath(os.path.join(REPO, ".."))
V1 = os.path.join(REPO, "data", "v1_unlevelled")       # pairs and registration of v1
OUTDIR = os.environ.get("SLAM_OUT") or os.path.join(REPO, "out")
os.makedirs(OUTDIR, exist_ok=True)
sys.path.insert(0, AQUI)
import geo                                   # noqa: E402
import limpieza                              # noqa: E402
from geo import load_voxel, register, crop_to, metrics   # noqa: E402

CACHE = os.environ.get("V2CACHE") or os.path.join(os.path.expanduser("~"), "v2_cache")
OUT = os.path.join(OUTDIR, "map_quality_v2.jsonl")   # = data/runwise/map_quality.jsonl
VOX = 0.01
EXPS = {"EXP1": (os.path.join(DATA, "tls_e1.npy"), os.path.join(DATA, "EXP 1", "Nubes de puntos")),
        "EXP2": (os.path.join(DATA, "tls_e2.npy"), os.path.join(DATA, "EXP 2", "Nubes de punto"))}
os.makedirs(CACHE, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------ mascara vectorizada
def mascara_observada(P, ref, celda=0.25):
    """Equivalente vectorizado de limpieza.mascara_observada (verificado en ICT49)."""
    m = np.floor(ref / celda).astype(np.int64).min(0)
    kk = lambda a: ((a[:, 0] + 2) << 42) | ((a[:, 1] + 2) << 21) | (a[:, 2] + 2)
    o = np.unique(np.floor(ref / celda).astype(np.int64) - m, axis=0)
    dil = np.unique(np.concatenate([kk(o + np.array([dx, dy, dz]))
                                    for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]))
    q = np.floor(P / celda).astype(np.int64) - m
    return np.isin(kk(q), dil)


limpieza.mascara_observada = mascara_observada


# ------------------------------------------------------------------ nivelacion
def _dirs(tmax, paso, centro=None, radio=None):
    """Direcciones unitarias en un casquete: alrededor de +z (o de `centro`)."""
    U = []
    if centro is None:
        for th in np.arange(0, tmax + 1e-9, paso):
            n = max(1, int(round(2 * np.pi * np.sin(np.radians(th)) / np.radians(paso))))
            for ph in np.linspace(0, 2 * np.pi, n, endpoint=False):
                U.append((np.sin(np.radians(th)) * np.cos(ph), np.sin(np.radians(th)) * np.sin(ph), np.cos(np.radians(th))))
        return np.array(U)
    # rejilla local alrededor de `centro`
    c = centro / np.linalg.norm(centro)
    a = np.cross(c, [1, 0, 0] if abs(c[0]) < 0.9 else [0, 1, 0]); a /= np.linalg.norm(a)
    b = np.cross(c, a)
    for dx in np.arange(-radio, radio + 1e-9, paso):
        for dy in np.arange(-radio, radio + 1e-9, paso):
            v = c + np.tan(np.radians(dx)) * a + np.tan(np.radians(dy)) * b
            U.append(v / np.linalg.norm(v))
    return np.array(U)


def _puntaje(P, U, bin_m=0.02, chunk=150):
    s = np.empty(len(U))
    for i in range(0, len(U), chunk):
        H = P @ U[i:i + chunk].T                       # n x k alturas
        B = np.floor((H - H.min(0)) / bin_m).astype(np.int64)
        nb = int(B.max()) + 1
        k = B.shape[1]
        cnt = np.bincount((B + np.arange(k) * nb).ravel(), minlength=nb * k).reshape(k, nb)
        s[i:i + chunk] = (cnt.astype(np.float64) ** 2).sum(1) / len(P) ** 2
    return s


def nivelar(P, seed=0, n=150_000):
    """Devuelve (R, inclinacion_deg): R lleva la vertical estimada del mapa a +z."""
    rng = np.random.default_rng(seed)
    S = P if len(P) <= n else P[rng.choice(len(P), n, replace=False)]
    S = S - S.mean(0)
    U = _dirs(70, 2.0)
    u = U[np.argmax(_puntaje(S, U))]
    U2 = _dirs(None, 0.25, centro=u, radio=2.5)
    u = U2[np.argmax(_puntaje(S, U2))]
    # rotacion minima u -> z
    z = np.array([0, 0, 1.0]); v = np.cross(u, z); s = np.linalg.norm(v); c = float(u @ z)
    if s < 1e-9:
        return np.eye(3), 0.0
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
    return R, float(np.degrees(np.arccos(np.clip(c, -1, 1))))


# ------------------------------------------------------------------ pasos
def clave(e, r, a):
    return os.path.join(CACHE, f"{e}_r{r}_{a}")


def filas_v1():
    return [json.loads(l) for l in open(os.path.join(V1, "map_quality.jsonl"))]


def hechos():
    s = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                r = json.loads(l); s.add((r["exp"], r["run"], r["algoritmo"]))
            except Exception:
                pass
    return s


def zip_de(e, r):
    nd = EXPS[e][1]
    return [f for f in os.listdir(nd) if f.lower().endswith(".zip")
            and "".join(c for c in f.split("_")[0] if c.isdigit()) == r][0]


def paso_a(e, r, a):
    nd = EXPS[e][1]
    z = zipfile.ZipFile(os.path.join(nd, zip_de(e, r)))
    nm = [n for n in z.namelist() if n.lower().endswith(".pcd") and not n.startswith("__MACOSX")
          and os.path.basename(n).replace(".pcd", "").split("_mapa_")[-1] == a][0]
    tmp = clave(e, r, a) + ".pcd"
    with z.open(nm) as s, open(tmp, "wb") as o:
        shutil.copyfileobj(s, o, 1 << 22)
    P, n = load_voxel(tmp, VOX)
    os.remove(tmp)
    np.save(clave(e, r, a) + ".npy", P.astype(np.float32))
    json.dump({"n_raw": int(n), "n_voxel": int(len(P))}, open(clave(e, r, a) + ".meta.json", "w"))
    log(f"[A] {e} run{r} {a}: {n:,} -> {len(P):,} voxeles")


def paso_b(e, r, a):
    tls = np.load(EXPS[e][0]).astype(np.float64)
    est = np.load(clave(e, r, a) + ".npy").astype(np.float64)
    R, incl = nivelar(est)
    L = np.eye(4); L[:3, :3] = R
    T, rms, inl = register(est @ R.T, tls)
    T = T @ L
    ea = est @ T[:3, :3].T + T[:3, 3]
    ec = crop_to(ea, tls, 1.0)
    np.save(clave(e, r, a) + ".crop.npy", ec.astype(np.float32))
    json.dump({"registro_rms_m": rms, "registro_inliers": inl, "T": np.round(T, 6).tolist(),
               "nivel_incl_deg": incl, "n_tras_recorte": int(len(ec)),
               "frac_fuera_del_TLS": 1.0 - len(ec) / max(len(ea), 1)},
              open(clave(e, r, a) + ".reg.json", "w"))
    log(f"[B] {e} run{r} {a}: nivel {incl:.1f} deg | rms {rms*100:.2f} cm | inliers {inl:.3f}")


def paso_c(e, r, a):
    tls = np.load(EXPS[e][0]).astype(np.float64)
    ec = np.load(clave(e, r, a) + ".crop.npy").astype(np.float64)
    m = metrics(ec, tls) if len(ec) >= 1000 else {"error": "sin solape con el TLS tras el registro"}
    json.dump(m, open(clave(e, r, a) + ".cru.json", "w"))
    log(f"[C] {e} run{r} {a}: crudo listo")


def paso_d(e, r, a):
    tls = np.load(EXPS[e][0]).astype(np.float64)
    ec = np.load(clave(e, r, a) + ".crop.npy").astype(np.float64)
    fila = {"exp": e, "run": r, "algoritmo": a, "zip": zip_de(e, r), "voxel_m": VOX,
            "registro": "v2_nivelado"}
    fila.update(json.load(open(clave(e, r, a) + ".meta.json")))
    fila.update(json.load(open(clave(e, r, a) + ".reg.json")))
    fila.update(json.load(open(clave(e, r, a) + ".cru.json")))
    if len(ec) >= 1000:
        for k, v in limpieza.metricas_limpias(ec, tls).items():
            fila["lim_" + k] = v
    v1 = {(x["exp"], str(x["run"]), x["algoritmo"]): x for x in filas_v1()}.get((e, r, a), {})
    fila["T_v1"] = v1.get("T"); fila["registro_inliers_v1"] = v1.get("registro_inliers")
    with open(OUT, "a") as f:
        f.write(json.dumps(fila) + "\n")
    for s in (".npy", ".crop.npy", ".reg.json", ".cru.json", ".meta.json"):
        try:
            os.remove(clave(e, r, a) + s)
        except OSError:
            pass
    p95 = fila.get("lim_p95_exactitud_m")
    log(f"[D] {e} run{r} {a}: inliers v1 {fila['registro_inliers_v1']:.2f} -> v2 {fila['registro_inliers']:.2f}"
        + (f" | P95acc {p95*100:.1f} cm" if p95 is not None else ""))


PASOS = [(".npy", paso_a), (".reg.json", paso_b), (".cru.json", paso_c), (None, paso_d)]


def siguiente(e, r, a):
    for suf, f in PASOS:
        if suf is None or not os.path.exists(clave(e, r, a) + suf):
            return f


def pendientes():
    h = hechos()
    return [(x["exp"], str(x["run"]), x["algoritmo"]) for x in filas_v1()
            if (x["exp"], str(x["run"]), x["algoritmo"]) not in h]


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if modo == "paso":
        p = tuple(sys.argv[2:5])
        while p not in hechos():
            siguiente(*p)(*p)
    elif modo == "todo":
        for p in pendientes():
            while p not in hechos():
                siguiente(*p)(*p)
        log("FIN")
    elif modo == "auto":
        pres = float(sys.argv[2]) if len(sys.argv) > 2 else 100
        t0 = time.time()
        orden = {"D-LIO": 0, "FAST-LIO2_Denso": 1, "KISS-ICP": 2, "POINT-LIO": 3, "HDMapping-LIO": 4, "LIO-LIVOX": 5}
        pend = sorted(pendientes(), key=lambda p: (not os.path.exists(clave(*p) + ".npy"), orden.get(p[2], 9)))
        if not pend:
            log("FIN"); sys.exit(0)
        for p in pend:
            while p not in hechos():
                if time.time() - t0 > pres:
                    log(f"PAUSA quedan {len(pendientes())}"); sys.exit(0)
                siguiente(*p)(*p)
        log(f"PAUSA quedan {len(pendientes())}")
