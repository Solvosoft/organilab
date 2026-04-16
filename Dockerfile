# ============ STAGE 1: BUILDER ============
FROM python:3.13-trixie AS builder

ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libxslt-dev libxml2-dev libffi-dev libpq-dev \
    python3-setuptools python3-cffi gettext && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /organilab

COPY requirements.txt .
RUN pip install --no-cache-dir pip setuptools gunicorn && \
    pip install --no-cache-dir -r requirements.txt

COPY src /organilab
RUN python manage.py compilemessages -l es --settings=organilab.settings && \
    mkdir -p /run/static/ && \
    STATIC_ROOT=/run/static/ python manage.py collectstatic --noinput --settings=organilab.settings

# ============ STAGE 2: RUNTIME ============
FROM python:3.13-slim-trixie

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV REQUESTS_CA_PATH=/certs/ca_nacional_de_CR.pem
ENV REQUESTS_CERT_PATH=/certs/bccr_agent.pem
ENV REQUESTS_KEY_PATH=/certs/bccr_agent_key.pem
ENV MEDIA_ROOT=/organilab/media/
ENV STATIC_ROOT=/run/static/
ENV STUB_SCHEME='https'
ENV STUB_HOST="firmadorexterno.bccr.fi.cr"

ARG UID=1000
ARG GUID=1000
ENV USER="organilab"
ENV SYSTEMGROUP="organilab"

# Runtime dependencies only (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libxml2 \
    libxslt1.1 \
    libffi8 \
    shared-mime-info \
    fontconfig \
    nginx \
    supervisor \
    gettext && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid $GUID $SYSTEMGROUP && \
    useradd --uid $UID --gid $GUID --system --no-create-home $USER && \
    mkdir -p /run/logs/ /run/static/ /run/supervisor/

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Nginx configuration
RUN echo "daemon off;" >> /etc/nginx/nginx.conf && \
    sed -i 's/user www-data;/user organilab;/g' /etc/nginx/nginx.conf && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

COPY docker/nginx-app.conf /etc/nginx/sites-available/default
COPY docker/supervisor-app.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx_personalize.py /organilab/nginx_personalize.py

# Copy application and static files with correct ownership
COPY --from=builder --chown=organilab:organilab /organilab /organilab
COPY --from=builder --chown=organilab:organilab /run/static/ /run/static/
COPY --chown=organilab:organilab docs/capacitacion/ /run/docs/capacitacion/

WORKDIR /organilab

# Entrypoint
COPY --chown=organilab:organilab docker/entrypoint.sh /run/entrypoint.sh
RUN chmod +x /run/entrypoint.sh && \
    chown -R organilab:organilab /run/logs/ /run/supervisor/ && \
    sed -i 's/proxy_set_header X-Forwarded-Proto $scheme;/proxy_set_header X-Forwarded-Proto https;/g' /etc/nginx/proxy_params

EXPOSE 80 8000

CMD ["/run/entrypoint.sh"]
