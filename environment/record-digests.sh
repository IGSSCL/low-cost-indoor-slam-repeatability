#!/usr/bin/env bash
# Registra el digest sha256 inmutable de cada imagen de algoritmo.
#
# Un tag se puede repuntar despues de publicado; el digest no. Ejecutar en la maquina
# donde viven las imagenes y pegar la salida en docker-images.md.
#
#     bash record-digests.sh                    # todas las imagenes locales
#     bash record-digests.sh fastlio2 pointlio  # solo las que coincidan con esos patrones
#
# Si una imagen nunca se subio a un registro no tendra RepoDigest. En ese caso se
# reporta el Image ID, que identifica la imagen localmente pero no permite a un tercero
# recuperarla: conviene subirla a un registro publico antes del deposito.

set -u

listar() {
    if [ "$#" -gt 0 ]; then
        for patron in "$@"; do
            docker images --format '{{.Repository}}:{{.Tag}}' | grep -i -- "$patron" || true
        done
    else
        docker images --format '{{.Repository}}:{{.Tag}}' | grep -v '^<none>' || true
    fi
}

printf '| Algorithm | Image | Tag | Digest (`sha256:`) |\n'
printf '|---|---|---|---|\n'

listar "$@" | sort -u | while read -r ref; do
    [ -z "$ref" ] && continue
    repo="${ref%:*}"
    tag="${ref##*:}"
    digest=$(docker image inspect "$ref" --format '{{range .RepoDigests}}{{println .}}{{end}}' 2>/dev/null \
             | head -1 | sed 's/.*@sha256://')
    if [ -z "$digest" ]; then
        id=$(docker image inspect "$ref" --format '{{.Id}}' 2>/dev/null | sed 's/^sha256://')
        digest="sin RepoDigest — Image ID ${id:0:12} — subir a un registro antes del deposito"
    fi
    printf '| | `%s` | `%s` | `%s` |\n' "$repo" "$tag" "$digest"
done

printf '\nCompletar la primera columna con el nombre del algoritmo.\n'
