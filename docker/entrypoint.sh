#!/bin/bash

cd /organilab
mkdir -p ~/.local/share/fonts
fc-cache --really-force

mkdir -p /run/logs/
mkdir -p /run/supervisor/
chown -R organilab:organilab /organilab
chown -R organilab:organilab /run/supervisor/

runuser -p  -c "python manage.py migrate" organilab
runuser -p  -c "python manage.py init_checks" organilab
runuser -p  -c "python manage.py load_urlname_permissions"  organilab



if [ -z "$DEVELOPMENT" ]; then
  python /organilab/nginx_personalize.py
  supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
else
  runuser -p -c "celery -A organilab worker  --scheduler django_celery_beat.schedulers:DatabaseScheduler  -l info -B" organilab &
  runuser -p -c "python manage.py runserver 0.0.0.0:8000" organilab
fi

