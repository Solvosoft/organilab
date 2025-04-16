# Use an official Python runtime as a parent image
FROM python:3.11-bookworm
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
ENV REQUESTS_CA_PATH=/certs/ca_nacional_de_CR.pem
ENV REQUESTS_CERT_PATH=/certs/bccr_agent.pem
ENV REQUESTS_KEY_PATH=/certs/bccr_agent_key.pem
ENV MEDIA_ROOT=/organilab/media/
ENV STATIC_ROOT=/run/static/
ENV STUB_SCHEME='https'
ENV STUB_HOST="firmadorexterno.bccr.fi.cr"
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

ARG UID=1000
ARG GUID=1000
ENV USER="organilab"
ENV SYSTEMGROUP="organilab"

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y  libxslt-dev libxml2-dev libffi-dev libpq-dev libpq5 python3-setuptools python3-cffi libcairo2 nginx supervisor gettext

RUN addgroup --system --gid $GUID $SYSTEMGROUP  && \
    useradd --uid $UID  --gid $GUID --system --no-create-home $USER && \
    mkdir -p /run/logs/ /run/static/

WORKDIR /organilab

ADD requirements.txt /organilab

RUN pip install --upgrade --trusted-host pypi.python.org --no-cache-dir pip requests setuptools gunicorn && \
pip install --trusted-host pypi.python.org --no-cache-dir -r requirements.txt

RUN  apt-get remove --purge build-essential libxslt-dev libxml2-dev libffi-dev  libpq-dev exim4* openssh-server gcc \
     libbluetooth3  default-libmysqlclient-dev mercurial subversion -y && \
     apt-get -y autoremove --purge  && \
     apt-get -y clean   && \
     rm -rf /var/lib/apt/lists/*

RUN echo "daemon off;" >> /etc/nginx/nginx.conf && \
    sed -i 's/user www-data;/user organilab;/g' /etc/nginx/nginx.conf

COPY docker/nginx-app.conf /etc/nginx/sites-available/default
COPY docker/supervisor-app.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx_personalize.py /organilab/nginx_personalize.py
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log
ADD src /organilab

RUN python manage.py compilemessages -l es --settings=organilab.settings && \
    python manage.py collectstatic  --noinput --settings=organilab.settings

ADD docker/entrypoint.sh /run/
RUN chown -R organilab:organilab /run/ && \
    chmod +x /run/entrypoint.sh &&\
    sed -i 's/proxy_set_header X-Forwarded-Proto $scheme;/proxy_set_header X-Forwarded-Proto https;/g' /etc/nginx/proxy_params

EXPOSE 80 8000

CMD ["/run/entrypoint.sh"]
