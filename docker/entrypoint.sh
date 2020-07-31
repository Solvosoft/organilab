#!/bin/bash

cd /organilab

mkdir -p /run/logs/
chown -R organilab:organilab /organilab
runuser -p  -c "python manage.py migrate" organilab

if [ -z "$DEVELOPMENT" ]; then
  if [ ! -z "$FVAHOSTNAME" ]; then
    sed -i 's/server_name organilab.org www.organilab.org;/server_name $FVAHOSTNAME www.$FVAHOSTNAME;/g'  /etc/nginx/sites-available/default
  fi
  supervisord -n
else
  runuser -p -c "celery worker -A organilab -l info -B" organilab &
  runuser -p -c "python manage.py runserver 0.0.0.0:8000" organilab
fi

