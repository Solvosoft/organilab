#!/bin/sh

docker build  -t organilab -f docker/Dockerfile .

#docker-compose run organilab python manage.py migrate
