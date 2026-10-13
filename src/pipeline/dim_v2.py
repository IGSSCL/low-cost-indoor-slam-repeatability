#!/usr/bin/env python3
"""Verificacion dimensional con el registro v2 (ICT49, P3).

Solo recalcula los pares cuyo registro cambio entre v1 y v2 (rotacion > 0,5 grados o
traslacion > 5 cm); el resto conserva la fila de dimensional.jsonl, porque con la misma T
el resultado es identico. Escribe out/dimensional_v2.jsonl con las 147 filas.

Uso: python dim_v2.py auto [presupuesto_s]
"""
import os, sys, json, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import reg_v2 as v                                   # noqa: E402  (rutas, cache, load)
from geo import load_voxel, crop_to                   # noqa: E402
from dimensional import compara, resumen             # noqa: E402

SAL = os.path.join(v.OUTDIR, "dimensional_v2.jsonl")              # = data/runwise/dimensional.jsonl
NUEVO = os.path.join(v.OUTDIR, "dimensional_v2_recalculados.jsonl")


def cambiados():
    out = []
    for l in open(v.OUT):
        r = json.loads(l)
        if r["registro_inliers"] < 0.05 or r.get("T_v1") is None:
            continue
        A, B = np.array(r["T_v1"]), np.array(r["T"])
        d = np.linalg.inv(A) @ B
        rot = np.degrees(np.arccos(np.clip((np.trace(d[:3, :3]) - 1) / 2, -1, 1)))
        if rot > 0.5 or np.linalg.norm(A[:3, 3] - B[:3, 3]) > 0.05:
            out.append((r["exp"], r["run"], r["algoritmo"], r["T"]))
    return out


def hechos():
    s = set()
    if os.path.exists(NUEVO):
        for l in open(NUEVO):
            r = json.loads(l); s.add((r["exp"], r["run"], r["algoritmo"]))
    return s


def paso(e, r, a, T):
    k = v.clave(e, r, a)
    tls = np.load(v.EXPS[e][0]).astype(np.float64)
    if not os.path.exists(k + ".dimcrop.npy"):
        if not os.path.exists(k + ".npy"):
            v.paso_a(e, r, a)
        E = np.load(k + ".npy").astype(np.float64)
        T = np.array(T)
        ec = crop_to(E @ T[:3, :3].T + T[:3, 3], tls, 1.0)
        np.save(k + ".dimcrop.npy", ec.astype(np.float32))
        os.remove(k + ".npy")
        v.log(f"[dimA] {e} run{r} {a}: {len(ec):,} puntos")
        return
    ec = np.load(k + ".dimcrop.npy").astype(np.float64)
    dims = compara(ec, tls); s = resumen(dims)
    fila = {"exp": e, "run": r, "algoritmo": a, **s, "dimensiones": dims, "registro": "v2_nivelado"}
    with open(NUEVO, "a") as f:
        f.write(json.dumps(fila) + "\n")
    os.remove(k + ".dimcrop.npy")
    v.log(f"[dimB] {e} run{r} {a}: n={s.get('n_dimensiones', 0)} mediana={s.get('error_abs_mediano_m', 0)*1000:.1f} mm")


def ensamblar():
    nuevos = {(r["exp"], r["run"], r["algoritmo"]): r for r in map(json.loads, open(NUEVO))} if os.path.exists(NUEVO) else {}
    with open(SAL, "w") as f:
        for l in open(os.path.join(v.V1, "dimensional.jsonl")):
            r = json.loads(l)
            f.write(json.dumps(nuevos.get((r["exp"], r["run"], r["algoritmo"]), r)) + "\n")
    v.log(f"dimensional_v2.jsonl ensamblado ({len(nuevos)} filas recalculadas)")


if __name__ == "__main__":
    pres = float(sys.argv[2]) if len(sys.argv) > 2 else 100
    t0 = time.time()
    lista = [c for c in cambiados() if tuple(c[:3]) not in hechos()]
    v.log(f"pendientes {len(lista)}")
    for c in lista:
        while tuple(c[:3]) not in hechos():
            if time.time() - t0 > pres:
                v.log("PAUSA"); sys.exit(0)
            paso(*c)
    ensamblar(); v.log("FIN")
