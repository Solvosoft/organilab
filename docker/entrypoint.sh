#!/bin/bash

runuser -u organilab -c "mkdir -p /run/logs/"
chown -R organilab:organilab /run /organilab
runuser -u organilab -c "python manage.py migrate"

if [ -z "$DEVELOPMENT" ]; then
  if [ ! -z "$FVAHOSTNAME" ]; then
    sed -i 's/server_name organilab.org www.organilab.org;/server_name $FVAHOSTNAME www.$FVAHOSTNAME;/g'  /etc/nginx/sites-available/default
  fi
  supervisord -n
else
  runuser -u organilab  -c "celery worker -A organilab -l info -b" &
  runuser -u organilab -c "python manage.py runserver 0.0.0.0:80"
fi

