#!/bin/bash

cd /organilab
mkdir -p ~/.local/share/fonts /run/logs/ /run/supervisor/
fc-cache --really-force
chown -R organilab:organilab /organilab /run/supervisor/

# Migraciones y configuración inicial
runuser -p -c "python manage.py migrate" organilab
runuser -p -c "python manage.py init_checks" organilab
runuser -p -c "python manage.py load_urlname_permissions" organilab

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
  dev)
    runuser -p -c "celery -A organilab worker --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info -B" organilab &
    exec runuser -p -c "python manage.py runserver 0.0.0.0:8000" organilab
    ;;
  *)
    echo "ERROR: SERVICE_TYPE debe ser 'web', 'celery', 'beat' o 'dev'"
    echo "Ejemplo: SERVICE_TYPE=web"
    exit 1
    ;;
esac
