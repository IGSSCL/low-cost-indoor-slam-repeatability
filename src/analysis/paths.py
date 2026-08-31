# -*- coding: utf-8 -*-
"""Resolucion de rutas para los scripts de analisis.

Los scripts de este directorio se escribieron para leer y escribir junto a si mismos.
En el repositorio las entradas viven en data/ con nombres en ingles y las salidas deben
ir a un directorio de trabajo. `raiz()` devuelve ese directorio de trabajo (out/ en la
raiz del repositorio) y, la primera vez que se invoca, deja alli una copia de cada
archivo de entrada con el nombre historico que los scripts esperan.

Se copia en lugar de enlazar para que funcione igual en Windows, Linux y macOS. Son
alrededor de 1 MB en total. La raiz del repositorio se deduce de la ubicacion de este
archivo y puede forzarse con la variable de entorno SLAM_REPO; el directorio de trabajo,
con SLAM_OUT.
"""
import os
import shutil

ENTRADAS = {
    'resultados.jsonl':              ('data', 'runwise', 'map_quality_raw.jsonl'),
    'resultados_con_filtrado.jsonl': ('data', 'runwise', 'map_quality.jsonl'),
    'trayectorias.jsonl':            ('data', 'runwise', 'trajectories.jsonl'),
    'dimensional.jsonl':             ('data', 'runwise', 'dimensional.jsonl'),
    'indice_completo.json':          ('data', 'derived', 'multicriteria_full.json'),
}


def repo():
    """Raiz del repositorio."""
    r = os.environ.get('SLAM_REPO')
    if r and os.path.isdir(r):
        return os.path.abspath(r)
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def raiz():
    """Directorio de trabajo, con las entradas ya dispuestas bajo su nombre historico."""
    out = os.environ.get('SLAM_OUT') or os.path.join(repo(), 'out')
    os.makedirs(out, exist_ok=True)
    for nombre, partes in ENTRADAS.items():
        origen = os.path.join(repo(), *partes)
        destino = os.path.join(out, nombre)
        if not os.path.exists(origen):
            continue
        if not os.path.exists(destino) or os.path.getmtime(origen) > os.path.getmtime(destino):
            shutil.copyfile(origen, destino)
    return out
