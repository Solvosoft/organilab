#!/bin/bash

docker run -d --rm --name organilab-mail -p 8025:8025 -p  1025:1025 -d mailhog/mailhog
docker run -d --rm --name organilab-rabbitmq -e RABBITMQ_DEFAULT_VHOST=organilabvhost -p 5672:5672 -d rabbitmq:3

echo "Esperando el inicio de rabbitmq ..." && sleep 20
cd src/
celery -A organilab worker -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler 
cd ../
docker rm -f organilab-mail
docker rm -f organilab-rabbitmq
