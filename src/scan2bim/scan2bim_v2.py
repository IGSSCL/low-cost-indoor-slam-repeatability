#!/usr/bin/env python3
"""Rugosidad y separacion entre losas con el registro v2 (ICT49, P3).

Solo cambian, entre las corridas usadas en S6 (Exp. 1: 1, 8, 13; Exp. 2: 3, 9, 11), los
pares cuyo registro v2 difiere del v1. Para ellos se recalcula la banda de +-35 cm en
torno a los planos del TLS con la T v2 y se aplican las mismas funciones de
`agrega.py` (rug) y `alturas.py` (pico). Escribe en out/ las versiones v2 publicadas en data/derived/.
"""
import os, sys, json, glob
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SLAM_REPO") or os.path.abspath(os.path.join(AQUI, "..", ".."))
DATA = os.environ.get("SLAM_DATA") or os.path.abspath(os.path.join(REPO, ".."))
S2B = AQUI
V1 = os.path.join(REPO, "data", "v1_unlevelled")
REF = os.path.join(REPO, "data", "reference")
OUTDIR = os.environ.get("SLAM_OUT") or os.path.join(REPO, "out")
os.makedirs(OUTDIR, exist_ok=True)
sys.path.insert(0, S2B)
os.chdir(S2B)
from bandas import leer_banda          # noqa: E402

RUNS = {"EXP1": ["1", "8", "13"], "EXP2": ["3", "9", "11"]}


def rug(P, z0, w=0.05, celda=0.5, nmin=40):
    Q = P[np.abs(P[:, 2] - z0) < w]
    if len(Q) < 5000: return None
    ij = np.floor(Q[:, :2] / celda).astype(np.int64); key = ij[:, 0] * 100000 + ij[:, 1]
    o = np.argsort(key); key = key[o]; z = Q[o, 2]
    b = np.flatnonzero(np.diff(key)) + 1; sig = []
    for a, c in zip(np.r_[0, b], np.r_[b, len(z)]):
        if c - a < nmin: continue
        s = z[a:c]; sig.append(1.4826 * np.median(np.abs(s - np.median(s))))
    if len(sig) < 20: return None
    return 1000 * float(np.median(sig)), len(sig)


def pico(z, z0, w=0.35):
    s = z[np.abs(z - z0) < w]
    if len(s) < 50: return None
    h, e = np.histogram(s, bins=np.arange(z0 - w, z0 + w + 0.002, 0.002))
    c = (e[:-1] + e[1:]) / 2
    return float(s[np.abs(s - c[h.argmax()]) < 0.02].mean())


def zip_y_miembro(e, run, alg):
    import subprocess
    Z = os.path.join(DATA, "EXP 1", "Nubes de puntos", f"{run}_mapa 3d.zip") if e == "EXP1" \
        else os.path.join(DATA, "EXP 2", "Nubes de punto", f"Exp{run}_2.zip")
    miem = [l.split()[-1] for l in subprocess.run(["unzip", "-l", Z], capture_output=True, text=True).stdout.splitlines()
            if l.strip().endswith(".pcd")]
    cand = [m for m in miem if m.endswith(f"_{alg}.pcd") or m == f"{alg}.pcd"]
    return Z, cand[0]


if __name__ == "__main__":
    V2 = [json.loads(l) for l in open(os.path.join(REPO, "data", "runwise", "map_quality.jsonl"))]
    cambios = []
    for r in V2:
        if r["run"] not in RUNS[r["exp"]] or r["registro_inliers"] < 0.05 or r.get("T_v1") is None: continue
        A, B = np.array(r["T_v1"]), np.array(r["T"]); d = np.linalg.inv(A) @ B
        rot = np.degrees(np.arccos(np.clip((np.trace(d[:3, :3]) - 1) / 2, -1, 1)))
        if rot > 0.5 or np.linalg.norm(A[:3, 3] - B[:3, 3]) > 0.05:
            cambios.append(r)
    print("pares a recalcular:", [(r["exp"], r["run"], r["algoritmo"]) for r in cambios], flush=True)
    R = {"EXP1": json.load(open(os.path.join(V1, "roughness_exp1.json"))),
         "EXP2": json.load(open(os.path.join(V1, "roughness_exp2.json")))}
    H = json.load(open(os.path.join(V1, "slab_separation.json")))
    log = []
    for r in cambios:
        e, run, alg = r["exp"], r["run"], r["algoritmo"]
        g = json.load(open(os.path.join(REF, f"scenario_geometry_exp{'1' if e == 'EXP1' else '2'}.json")))
        Z, m = zip_y_miembro(e, run, alg)
        Q = leer_banda(Z, m, np.array(r["T"]), np.array(g["lo"]), np.array(g["hi"]), [g["z_suelo"], g["z_cielo"]])
        a, b = rug(Q, g["z_suelo"]), rug(Q, g["z_cielo"])
        ps, pc = pico(Q[:, 2], g["z_suelo"]), pico(Q[:, 2], g["z_cielo"])
        # indice de la corrida en el orden de glob ('11' < '3' < '9', '1' < '13' < '8')
        idx = sorted(RUNS[e]).index(run)
        ent = R[e].get(alg)
        antes = (ent["inferior"][idx], ent["superior"][idx]) if ent and len(ent["inferior"]) > idx else None
        if a and b and ent and len(ent["inferior"]) > idx:
            ent["inferior"][idx], ent["superior"][idx] = a[0], b[0]
        true = g["z_cielo"] - g["z_suelo"]
        sep = None
        if ps is not None and pc is not None:
            sep = round(pc - ps, 4)
            for x in H[e]["algoritmos"].get(alg, []):
                if x["run"] == run:
                    x["sep_m"] = sep; x["err_mm"] = round((sep - true) * 1000, 1)
        log.append({"exp": e, "run": run, "algoritmo": alg, "rug_antes_mm": antes,
                    "rug_v2_mm": (a[0] if a else None, b[0] if b else None),
                    "sep_v2_m": sep, "err_sep_v2_mm": None if sep is None else round((sep - true) * 1000, 1)})
        print(log[-1], flush=True)
    json.dump(R["EXP1"], open(os.path.join(OUTDIR, "roughness_exp1.json"), "w"))
    json.dump(R["EXP2"], open(os.path.join(OUTDIR, "roughness_exp2.json"), "w"))
    json.dump(H, open(os.path.join(OUTDIR, "slab_separation.json"), "w"), indent=1)
    json.dump(log, open(os.path.join(OUTDIR, "scan2bim_v2_changes.json"), "w"), indent=1)
    print("FIN")
