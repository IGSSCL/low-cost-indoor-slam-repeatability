# Cómo depositar, y qué falta por completar

Esta nota es para el autor, no para el lector del repositorio. Explica los cinco huecos
que quedan y el orden en que conviene cerrarlos.

JOBE aplica la **Opción C** de la política de datos de Elsevier: depositar y citar es
obligatorio, no recomendado. Mientras el manuscrito diga `[repository/DOI]`, el envío no
cumple.

---

## Lo que falta, en orden

### 1. Los digests de las imágenes Docker — el único irrecuperable

Los tags son mutables: `latest`, o incluso un tag de versión, puede repuntarse a otra
imagen después de publicado. El `sha256` no. Si las imágenes se borran, el dato se pierde
para siempre, así que es lo primero.

En la máquina donde viven las imágenes:

```bash
bash environment/record-digests.sh > /tmp/digests.md
```

y pegar el resultado en la tabla de `environment/docker-images.md`. Si alguna imagen
nunca se subió a un registro, el script lo dirá: en ese caso conviene subirla a Docker Hub
o al GitHub Container Registry antes del depósito, porque un Image ID local no le sirve a
un tercero.

### 2. Repositorio y commit de cada algoritmo

En `environment/algorithm-parameters.md`, la tabla de implementaciones necesita, por cada
uno de los seis: URL del repositorio, commit o release evaluado, y el archivo de
configuración usado. Es lo que permite a un revisor verificar que se evaluó la versión
que se dice.

### 3. Subir a GitHub y conectar Zenodo

```bash
cd repositorio
git init
git add .
git commit -m "Code and data for the JOBE submission"
git branch -M main
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

Después, en Zenodo: *GitHub* → activar el repositorio → volver a GitHub y crear un
**release** `v1.0.0`. Zenodo acuña el DOI automáticamente a partir del release, y lee
`.zenodo.json` y `CITATION.cff` para los metadatos.

Zenodo emite además un **DOI de concepto** que siempre apunta a la última versión. En el
artículo conviene citar ese, no el de la versión, para que la referencia siga siendo
válida si se corrige algo.

### 4. Reemplazar los tres marcadores

| Archivo | Marcador |
|---|---|
| `CITATION.cff` | `repository-code` y el `doi` de la publicación |
| `.zenodo.json` | el `identifier` de `related_identifiers` |
| El manuscrito | `[repository/DOI]` en *Data availability* |

El DOI del artículo no existe hasta la aceptación. Se deposita ahora con el marcador,
y se actualiza el registro de Zenodo cuando se acepte: se puede editar los metadatos sin
acuñar un DOI nuevo.

### 5. Decidir si el segundo DOI se justifica

Estaba previsto separar código y datos en dos registros. Como el repositorio pesa
alrededor de 1,3 MB en total y los datos no tienen sentido sin los scripts que los
producen, **un solo registro basta y es más fácil de citar**. Si de todas formas quieres
dos, el segundo sería para las nubes de punto completas, que son decenas de gigabytes y
no caben en el límite estándar de Zenodo — habría que pedir cuota ampliada.

---

## Lo que ya está resuelto

- **`external/` fuera.** Los 57 MB de herramientas de terceros con licencia propia no se
  redistribuyen; se citan en `environment/algorithm-parameters.md`.
- **`indice.py` fuera.** Era la versión anterior de `apendiceA.py`. Se verificó que
  `apendiceA.py` reproduce la Tabla 7 dígito a dígito (0,944 / 0,896 / 0,920), así que es
  el canónico y el otro no se incluye.
- **Rutas absolutas eliminadas.** Seis scripts tenían la ruta de la sesión escrita a mano;
  ahora usan `SLAM_DATA`, `SLAM_REPO`, `SLAM_OUT` y `SLAM_FIGDIR`, con valores por
  defecto sensatos.
- **Coste computacional externalizado.** Estaba incrustado en `apendiceA.py`; ahora vive
  en `data/runwise/computational.csv`, y se comprobó que el índice da exactamente lo
  mismo.
- **Bandas LOA de las medianas corregidas.** Los informes internos etiquetaban una banda
  a partir de la mediana, que es justo lo que el artículo dice que no se puede hacer.
  Ahora la columna se llama «rango numérico» y la asignación de banda aparece solo donde
  viene del P95.
- **Los siete scripts de análisis corren de punta a punta** desde el repositorio recién
  clonado y reproducen las tablas publicadas.
- **`requirements.txt` fijado** a numpy 2.2.6, scipy 1.15.3, matplotlib 3.10.9,
  pandas 2.3.3.
- **Licencias separadas**: MIT para el código, CC BY 4.0 para los datos.

---

## Comprobación antes de subir

```bash
cd src/analysis
for s in analisis.py analisis_filtrado.py analisis_trayectorias.py \
         analisis_dimensional.py pareadas.py apendiceA.py fase0.py; do
    python -W ignore "$s" > /dev/null && echo "ok  $s" || echo "FALLA  $s"
done
```

Los siete deben decir `ok`. Después, comparar `out/recalculos/0a_runwise.md` con las
Tablas 3 y 4 del artículo y `out/RESULTADOS_DIMENSIONAL.md` con la Tabla 5: las cifras
deben coincidir dígito a dígito.
