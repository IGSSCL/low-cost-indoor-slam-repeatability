#!/usr/bin/env python3
"""Validacion hold-out espacial del registro SLAM -> TLS (PLAN_MEJORAS_ICT49, 2.4 / D2).

Pregunta: cuanto del error reportado es optimismo del registro, dado que el ICP minimiza
la misma distancia que despues se mide.

Diseno
------
1. El TLS de cada experimento se divide en celdas XY de CELL m (por defecto 2,5 m). Con una
   semilla fija, el 30 % de las celdas ocupadas es la region de EVALUACION y el 70 % la de
   REGISTRO. La particion es la misma para todos los pares de un experimento.
2. Entre ambas regiones se deja un margen de BUF m (0,5 m): los puntos de registro a menos
   de BUF de una celda de evaluacion no se usan para registrar.
3. Registro completo v2 (nivelacion previa + `geo.register`, semilla 0) -> T_full.
   T_full se usa SOLO para asignar cada punto SLAM a una celda; el margen absorbe su error.
4. Registro hold-out: mismo `geo.register`, pero solo con los puntos SLAM y TLS de la region
   de registro -> T_hold. Ningun punto de la region de evaluacion entra en el ajuste.
5. Metricas en la region de evaluacion, con las definiciones del articulo (limpieza.py):
   exactitud SLAM->TLS sobre la nube filtrada (ROR) y enmascarada (region observada),
   completitud TLS->SLAM contra la nube sin filtrar. Se calculan dos veces sobre la MISMA
   region: con T_full (dentro de muestra) y con T_hold (fuera de muestra).
   La diferencia entre ambas es el optimismo del registro.

Uso
---
  python holdout.py todo                  # procesa todo en un solo proceso (equipo de proceso)
  python holdout.py auto [presupuesto_s]  # avanza por pasos hasta agotar el presupuesto (entornos
                                          # con limite de duracion por comando); relanzar hasta "FIN"
  python holdout.py paso EXP RUN ALG      # un par completo
Variables: SLAM_DATA (nubes y TLS), SLAM_OUT, HOCACHE (cache temporal), CELL, BUF, FRAC, SEED.
Salida: out/holdout_v2.jsonl, publicada como data/registration/holdout.jsonl (una linea por par, reanudable).
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
from geo import load_voxel, register, crop_to          # noqa: E402
from limpieza import ror                                # noqa: E402
from reg_v2 import nivelar                              # noqa: E402

CACHE = os.environ.get("HOCACHE") or os.path.join(os.path.expanduser("~"), "ho_cache")
OUT = os.path.join(OUTDIR, "holdout_v2.jsonl")   # = data/registration/holdout.jsonl
CELL = float(os.environ.get("CELL", "2.5"))
BUF = float(os.environ.get("BUF", "0.5"))
FRAC = float(os.environ.get("FRAC", "0.30"))
SEED = int(os.environ.get("SEED", "0"))
VOX = 0.01
QCAP = 800_000
TAUS = (0.02, 0.05)
EXPS = {"EXP1": (os.path.join(DATA, "tls_e1.npy"), os.path.join(DATA, "EXP 1", "Nubes de puntos")),
        "EXP2": (os.path.join(DATA, "tls_e2.npy"), os.path.join(DATA, "EXP 2", "Nubes de punto"))}
os.makedirs(CACHE, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- particion
def particion(tls):
    """Celdas de evaluacion (set) y funcion que clasifica puntos: 0 registro, 1 evaluacion,
    2 margen (descartado del registro)."""
    o = tls[:, :2].min(0)
    c = np.floor((tls[:, :2] - o) / CELL).astype(np.int64)
    celdas = np.unique(c, axis=0)
    rng = np.random.default_rng(SEED)
    n_ev = int(round(FRAC * len(celdas)))
    ev = celdas[rng.choice(len(celdas), n_ev, replace=False)]
    _EV["o"], _EV["ev"] = o, ev

    def clasifica(P):
        q = (P[:, :2] - o) / CELL
        ci = np.floor(q).astype(np.int64)
        k = _pertenece(ci, ev)
        lab = np.where(k, 1, 0).astype(np.int8)
        # margen: puntos de registro a menos de BUF de una celda de evaluacion vecina
        f = q - ci                                   # posicion fraccional dentro de la celda
        b = BUF / CELL
        cerca = np.zeros(len(P), bool)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                vec = _pertenece(ci + np.array([dx, dy]), ev)
                dxm = np.where(dx == -1, f[:, 0], np.where(dx == 1, 1 - f[:, 0], 0.0))
                dym = np.where(dy == -1, f[:, 1], np.where(dy == 1, 1 - f[:, 1], 0.0))
                cerca |= vec & (np.hypot(dxm, dym) < b)
        lab[(lab == 0) & cerca] = 2
        return lab
    return len(celdas), n_ev, clasifica


_EV = {}


def cerca_eval(P):
    """True para puntos en una celda de evaluacion o en una de sus 8 vecinas."""
    o, ev = _EV["o"], _EV["ev"]
    ci = np.floor((P[:, :2] - o) / CELL).astype(np.int64)
    m = np.zeros(len(P), bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            m |= _pertenece(ci + np.array([dx, dy]), ev)
    return m


def _pertenece(ci, ev):
    key = lambda a: (a[:, 0] + (1 << 20)) * (1 << 21) + (a[:, 1] + (1 << 20))
    return np.isin(key(ci), key(ev))


# ---------------------------------------------------------------- mascara observada rapida
def mascara_observada(P, ref, celda=0.25):
    """Equivalente vectorizado de limpieza.mascara_observada (TLS ocupado a 25 cm, dilatado
    un voxel en 26 direcciones)."""
    m = np.floor(ref / celda).astype(np.int64).min(0)
    kk = lambda a: ((a[:, 0] + 2) << 42) | ((a[:, 1] + 2) << 21) | (a[:, 2] + 2)
    o = np.unique(np.floor(ref / celda).astype(np.int64) - m, axis=0)
    dil = np.unique(np.concatenate([kk(o + np.array([dx, dy, dz]))
                                    for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]))
    q = np.floor(P / celda).astype(np.int64) - m
    return np.isin(kk(q), dil)


# ---------------------------------------------------------------- metricas en la region
def metricas(est_raw, keep_ror, T, gt, gt_tree, lab_gt, clasifica, rng_seed=11):
    rng = np.random.default_rng(rng_seed)
    if est_raw.dtype == np.float32:          # nubes grandes: trabajar en float32 (memoria)
        ea = est_raw @ T[:3, :3].T.astype(np.float32) + T[:3, 3].astype(np.float32)
    else:
        ea = est_raw @ T[:3, :3].T + T[:3, 3]
    ec_mask = np.all((ea >= gt.min(0) - 1.0) & (ea <= gt.max(0) + 1.0), 1)   # crop_to
    ec = ea[ec_mask]
    # exactitud: nube filtrada (ROR calculado una vez) + region observada + celdas de evaluacion
    ef = ea[ec_mask & keep_ror]
    del ea
    ef = ef[mascara_observada(ef, gt)]
    ef = ef[clasifica(ef) == 1]
    gq = gt[lab_gt == 1]
    if len(ef) < 1000 or len(gq) < 1000:
        return {"error": "region de evaluacion vacia"}
    eq = ef if len(ef) <= QCAP else ef[rng.choice(len(ef), QCAP, replace=False)]
    gq = gq if len(gq) <= QCAP else gq[rng.choice(len(gq), QCAP, replace=False)]
    d_eg, _ = gt_tree.query(eq, k=1)
    if len(ec) > 8_000_000:
        # Memoria: para nubes muy grandes el arbol de completitud se construye solo con los
        # puntos a menos de una celda (2,5 m) de la region de evaluacion. Es exacto para toda
        # distancia menor que 2,5 m, que cubre todas las tolerancias y percentiles reportados.
        ec = ec[cerca_eval(ec)]
    d_ge, _ = cKDTree(ec).query(gq, k=1)
    mg = np.concatenate([d_eg, d_ge])
    r = {"n_eval_est": int(len(ef)), "n_eval_tls": int((lab_gt == 1).sum()),
         "dbi_m": float(0.5 * (d_eg.mean() + d_ge.mean())),
         "mediana_m": float(np.median(mg)),
         "p95_exactitud_m": float(np.percentile(d_eg, 95)),
         "p99_m": float(np.percentile(mg, 99))}
    for t in TAUS:
        r[f"cov@{t}"] = float((d_ge <= t).mean())
    return r


# ---------------------------------------------------------------- pasos
def clave(e, r, a):
    return os.path.join(CACHE, f"{e}_r{r}_{a}")


def pares():
    R = [json.loads(l) for l in open(os.path.join(V1, "map_quality.jsonl"))]
    return [(r["exp"], str(r["run"]), r["algoritmo"], r["registro_inliers"], r["T"]) for r in R]


def hechos():
    if not os.path.exists(OUT):
        return set()
    s = set()
    for l in open(OUT):
        try:
            r = json.loads(l); s.add((r["exp"], r["run"], r["algoritmo"]))
        except Exception:
            pass
    return s


def paso_a(e, r, a):
    """Extrae y voxeliza la nube SLAM."""
    nd = EXPS[e][1]
    zn = [f for f in os.listdir(nd) if f.lower().endswith(".zip")
          and "".join(c for c in f.split("_")[0] if c.isdigit()) == r][0]
    z = zipfile.ZipFile(os.path.join(nd, zn))
    nm = [n for n in z.namelist() if n.lower().endswith(".pcd") and not n.startswith("__MACOSX")
          and os.path.basename(n).replace(".pcd", "").split("_mapa_")[-1] == a][0]
    tmp = clave(e, r, a) + ".pcd"
    with z.open(nm) as s, open(tmp, "wb") as o:
        shutil.copyfileobj(s, o, 1 << 22)
    P, n = load_voxel(tmp, VOX)
    os.remove(tmp)
    np.save(clave(e, r, a) + ".npy", P.astype(np.float32))
    log(f"[A] {e} run{r} {a}: {n:,} -> {len(P):,} voxeles")


def paso_b(e, r, a):
    """Registro completo (como el articulo) y registro hold-out."""
    tls = np.load(EXPS[e][0]).astype(np.float64)
    est = np.load(clave(e, r, a) + ".npy").astype(np.float64)
    nc, ne, clasifica = particion(tls)
    # Registro v2 (ICT49): nivelacion previa del mapa con su propia geometria, sin mirar
    # el TLS, y despues geo.register. La nivelacion se calcula una vez con la nube completa
    # del SLAM (no usa el TLS, asi que no filtra informacion de la region de evaluacion).
    # Memoria: el registro solo usa submuestras (<= 300.000 puntos); para las nubes muy
    # grandes (> 8 M voxeles) se trabaja con una submuestra fija de 8 M para no agotar la RAM.
    if len(est) > 8_000_000:
        est = est[np.random.default_rng(7).choice(len(est), 8_000_000, replace=False)]
    R, _ = nivelar(est)
    L = np.eye(4); L[:3, :3] = R
    est_l = est @ R.T
    T_full, rms_f, inl_f = register(est_l, tls)
    T_full = T_full @ L
    lab_est = clasifica(est @ T_full[:3, :3].T + T_full[:3, 3])
    lab_tls = clasifica(tls)
    T_hold, rms_h, inl_h = register(est_l[lab_est == 0], tls[lab_tls == 0])
    T_hold = T_hold @ L
    json.dump({"T_full": T_full.tolist(), "rms_full": rms_f, "inl_full": inl_f,
               "T_hold": T_hold.tolist(), "rms_hold": rms_h, "inl_hold": inl_h,
               "celdas": nc, "celdas_eval": ne,
               "frac_est_registro": float((lab_est == 0).mean()),
               "frac_tls_registro": float((lab_tls == 0).mean())},
              open(clave(e, r, a) + ".reg.json", "w"))
    log(f"[B] {e} run{r} {a}: rms full {rms_f*100:.2f} cm / hold {rms_h*100:.2f} cm")


def paso_c(e, r, a):
    """ROR sobre la nube alineada con T_full (el filtro no depende del registro de forma
    apreciable: la diferencia entre T_full y T_hold es centimetrica y la celda es de 10 cm)."""
    reg = json.load(open(clave(e, r, a) + ".reg.json"))
    tls = np.load(EXPS[e][0]).astype(np.float64)
    est = np.load(clave(e, r, a) + ".npy").astype(np.float64)
    T = np.array(reg["T_full"])
    ea = est @ T[:3, :3].T + T[:3, 3]
    keep = np.zeros(len(ea), bool)
    idx = np.where(np.all((ea >= tls.min(0) - 1.0) & (ea <= tls.max(0) + 1.0), 1))[0]
    # ror devuelve la nube filtrada; reconstruimos la mascara por claves de voxel
    from limpieza import _claves, _OFF
    k = _claves(ea[idx], 0.10); ks = np.sort(k)
    n = np.zeros(len(k), dtype=np.int16)
    for dx, dy, dz in _OFF:
        n += np.isin(k + ((dx << 42) | (dy << 21) | dz), ks)
    keep[idx[n >= 3]] = True
    np.save(clave(e, r, a) + ".ror.npy", keep)
    log(f"[C] {e} run{r} {a}: ROR elimina {1 - keep[idx].mean():.2%}")


def paso_d(e, r, a):
    """Metricas en la region de evaluacion con T_full y con T_hold."""
    reg = json.load(open(clave(e, r, a) + ".reg.json"))
    tls = np.load(EXPS[e][0]).astype(np.float64)
    est = np.load(clave(e, r, a) + ".npy")
    if len(est) <= 8_000_000:
        est = est.astype(np.float64)
    keep = np.load(clave(e, r, a) + ".ror.npy")
    _, _, clasifica = particion(tls)
    lab_tls = clasifica(tls)
    tree = cKDTree(tls)
    out = {"exp": e, "run": r, "algoritmo": a, "cell_m": CELL, "buf_m": BUF, "frac_eval": FRAC,
           "seed": SEED, **{k: v for k, v in reg.items() if not k.startswith("T_")},
           "T_full": reg["T_full"], "T_hold": reg["T_hold"]}
    Tf, Th = np.array(reg["T_full"]), np.array(reg["T_hold"])
    out["full"] = metricas(est, keep, Tf, tls, tree, lab_tls, clasifica)
    out["hold"] = metricas(est, keep, Th, tls, tree, lab_tls, clasifica)
    dT = np.linalg.inv(Tf) @ Th
    out["dT_tras_cm"] = float(np.linalg.norm(dT[:3, 3]) * 100)
    out["dT_rot_deg"] = float(np.degrees(np.arccos(np.clip((np.trace(dT[:3, :3]) - 1) / 2, -1, 1))))
    with open(OUT, "a") as f:
        f.write(json.dumps(out) + "\n")
    for s in (".npy", ".reg.json", ".ror.npy"):
        try:
            os.remove(clave(e, r, a) + s)
        except OSError:
            pass
    f_, h_ = out["full"], out["hold"]
    if "error" in f_ or "error" in h_:
        log(f"[D] {e} run{r} {a}: {f_.get('error') or h_.get('error')}")
    else:
        log(f"[D] {e} run{r} {a}: P95acc {f_['p95_exactitud_m']*100:.2f} -> {h_['p95_exactitud_m']*100:.2f} cm | "
            f"Dbi {f_['dbi_m']*100:.2f} -> {h_['dbi_m']*100:.2f} cm | dT {out['dT_tras_cm']:.1f} cm {out['dT_rot_deg']:.3f} deg")


PASOS = [(".npy", paso_a), (".reg.json", paso_b), (".ror.npy", paso_c), (None, paso_d)]


def siguiente(e, r, a):
    for suf, f in PASOS:
        if suf is None or not os.path.exists(clave(e, r, a) + suf):
            return f


def pendientes():
    h = hechos()
    return [(e, r, a) for e, r, a, inl, _ in pares() if inl >= 0.05 and (e, r, a) not in h]


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if modo == "paso":
        e, r, a = sys.argv[2:5]
        while (e, r, a) not in hechos():
            siguiente(e, r, a)(e, r, a)
    elif modo == "todo":
        for e, r, a in pendientes():
            while (e, r, a) not in hechos():
                siguiente(e, r, a)(e, r, a)
        log("FIN")
    elif modo == "auto":
        pres = float(sys.argv[2]) if len(sys.argv) > 2 else 150
        t0 = time.time()
        # orden: primero los pares ya empezados, despues los mas livianos
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
