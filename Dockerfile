# Use an official Python runtime as a parent image
FROM python:3.10-bullseye
ENV PYTHONUNBUFFERED 1
ENV REQUESTS_CA_PATH=/certs/ca_nacional_de_CR.pem
ENV REQUESTS_CERT_PATH=/certs/bccr_agent.pem
ENV REQUESTS_KEY_PATH=/certs/bccr_agent_key.pem
ENV STUB_SCHEME='https'
ENV STUB_HOST="firmadorexterno.bccr.fi.cr"


ARG UID=1000
ENV USER="organilab"
RUN useradd -u $UID -ms /bin/bash $USER

RUN mkdir -p /run/logs/ /run/static/
WORKDIR /organilab

RUN apt-get update && \
    apt-get install -y  libxslt-dev libxml2-dev libffi-dev libpq-dev libpq5 python3-setuptools python3-cffi libcairo2 nginx supervisor gettext rsyslog

ADD requirements.txt /organilab

RUN pip install --upgrade --trusted-host pypi.python.org --no-cache-dir pip requests setuptools gunicorn && \
pip install --trusted-host pypi.python.org --no-cache-dir -r requirements.txt

RUN  apt-get remove libxslt-dev libxml2-dev libffi-dev libpq-dev -y && \
     apt-get -y autoremove && \
     apt-get -y clean   && \
     rm -rf /var/lib/apt/lists/*

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN sed -i 's/user www-data;/user organilab;/g' /etc/nginx/nginx.conf

COPY docker/nginx-app.conf /etc/nginx/sites-available/default
COPY docker/supervisor-app.conf /etc/supervisor/conf.d/
COPY docker/nginx_personalize.py /organilab/nginx_personalize.py
ADD src /organilab

RUN python manage.py compilemessages -l es --settings=organilab.settings
RUN python manage.py collectstatic  --noinput --settings=organilab.settings

ADD docker/entrypoint.sh /run/
RUN chown -R organilab:organilab /run/

RUN chmod +x /run/entrypoint.sh
RUN sed -i 's/proxy_set_header X-Forwarded-Proto $scheme;/proxy_set_header X-Forwarded-Proto https;/g' /etc/nginx/proxy_params

EXPOSE 80 8000

CMD ["/run/entrypoint.sh"]
