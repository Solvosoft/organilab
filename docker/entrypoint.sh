#!/bin/bash

cd /organilab
mkdir -p ~/.local/share/fonts /run/logs/ /run/supervisor/
fc-cache --really-force
chown -R organilab:organilab /organilab /run/supervisor/

# Migraciones y configuración inicial.
#
# Corre en CADA arranque de CADA contenedor, así que con más de una réplica son
# migraciones en paralelo sobre la misma base. Vale para docker-compose y para
# desarrollo, que es un contenedor de cada rol; no vale para un clúster.
#
# Donde haya un orquestador que sepa lanzar la instalación una sola vez (el
# bootstrap.job del AppPack, que además la protege con una compuerta), se pone
# ORGANILAB_BOOT_INSTALL=false y el arranque se limita a levantar el servicio.
# El default es `true` para no cambiarle el comportamiento a nadie.
#
# Las traducciones ya vienen compiladas de la imagen (etapa builder), así que
# aquí no se recompilan: eran dos `compilemessages` en cada arranque de cada
# réplica que producían exactamente los mismos .mo.
if [ "${ORGANILAB_BOOT_INSTALL:-true}" = "true" ]; then
  runuser -p -c "python manage.py organilab_install" organilab || exit 1
else
  echo "ORGANILAB_BOOT_INSTALL=false: se omite la instalación en el arranque."
fi

# Selector de servicio según SERVICE_TYPE
case "${SERVICE_TYPE}" in
  web)
    python /organilab/nginx_personalize.py
    supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
    ;;
  celery)
    exec runuser -p -c "celery -A organilab worker -l info -c ${CELERY_CONCURRENCY:-2}" organilab
    ;;
  beat)
    exec runuser -p -c "celery -A organilab beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=INFO --pidfile=/tmp/celerybeat.pid" organilab
    ;;
  all)
    python /organilab/nginx_personalize.py
    # Enable celery programs that are autostart=false by default
    sed -i '/\[program:celery_worker\]/,/\[program:/{s/autostart=false/autostart=true/}' /etc/supervisor/conf.d/supervisord.conf
    sed -i '/\[program:celery_beat\]/,/\[program:/{s/autostart=false/autostart=true/}' /etc/supervisor/conf.d/supervisord.conf
    supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
    ;;
  dev)
    runuser -p -c "celery -A organilab worker --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info -B" organilab &
    exec runuser -p -c "python manage.py runserver 0.0.0.0:8000" organilab
    ;;
  *)
    echo "ERROR: SERVICE_TYPE debe ser 'web', 'celery', 'beat', 'all' o 'dev'"
    echo "Ejemplo: SERVICE_TYPE=web"
    exit 1
    ;;
esac
