#!/bin/bash

chwon -R organilab:organilab /run /organilab
runuser -u organilab python manage.py migrate --settings=organilab.settings

if [ -z $DEVELOPMENT ]; then
  runuser -u organilab  celery worker -A organilab -l info -b &
  runuser -u organilab python manage.py runserver --settings=organilab.settings 0.0.0.0:80
else
  if [ -z $HOSTNAME ]; then
    sed -i 's/server_name organilab.org www.organilab.org;/server_name $HOSTNAME www.$HOSTNAME;/g'  /etc/nginx/sites-available/default
  fi
  supervisord -n
fi

