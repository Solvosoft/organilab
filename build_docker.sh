#!/bin/sh

# This script help to run docker development environment to make docker environment test
# To make
DO_MANUALES=false
DO_CLENUP=true
DO_CHANGEPASS=false
if $DO_CLENUP; then
    docker-compose -f docker/docker-compose.yml down -v  --remove-orphans
fi

if $DO_MANUALES; then
    cp docker/organilab-manuales.env docker/organilab.env
else
    cp docker/organilab-sitio.env docker/organilab.env
fi

docker-compose -f docker/docker-compose.yml up -d postgresdb
sleep 5
source docker/organilab.env
PGPASSWORD=`echo $POSTGRES_PASSWORD` /usr/bin/pg_restore --clean --create --host "127.0.0.1" --port "5431" --username "$DBUSER"  --role "$DBUSER" --dbname "$DBNAME" --verbose backups/organilab.backup

docker-compose -f docker/docker-compose.yml up -d


if $DO_CHANGEPASS; then
   docker cp src/auth_and_perms/management/commands/update_profile.py organilab:/organilab/auth_and_perms/management/commands/update_profile.py
   docker-compose -f docker/docker-compose.yml exec organilab python manage.py update_profile --noinput
fi
