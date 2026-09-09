#!/bin/bash
#
# Instalador de un tenant, pensado para correr como job de Swarm
# (bootstrap.job / lifecycle.upgrade del AppPack), no como entrypoint.
#
#   /run/install.sh              -> instalación nueva
#   /run/install.sh --upgrade    -> tras cambiar de imagen
#
# Por qué existe en vez de invocar `python manage.py organilab_install` directo:
# el job de Swarm corre como ROOT (la imagen no declara USER), y el instalador
# escribe en MEDIA (los pictogramas SGA). Sin reentrar como `organilab`, esos
# archivos quedarían con dueño root dentro de un volumen que la web y los
# workers montan como uid 1000, y la aplicación no podría tocarlos después.
set -euo pipefail

cd /organilab

# El origen del bind puede venir recién creado por Swarm, que lo crea como root.
mkdir -p "${MEDIA_ROOT:-/organilab/media/}"
chown -R organilab:organilab "${MEDIA_ROOT:-/organilab/media/}"

exec runuser -p -c "python manage.py organilab_install $*" organilab
