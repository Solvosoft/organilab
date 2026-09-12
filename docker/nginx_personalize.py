import os
import re
with open('/etc/nginx/sites-enabled/default', 'r') as arch:
    fva_conf = arch.read()


def bucket_for(longest):
    """Tamano de bucket que aloja una clave de `longest` caracteres.

    Se calcula en vez de fijarlo: la constante 128 arreglaba el dominio de hoy
    y volvia a romper con el siguiente mas largo. El +32 es la sobrecarga por
    entrada -- por eso el default de 64 ya se queda corto con un dominio de 50.
    La potencia de dos es lo que nginx espera.
    """
    size = 64
    while size < longest + 32:
        size *= 2
    return size


nginx_host=os.getenv('NGINX_HOST', None)
nginx_access_log=os.getenv('NGINX_ACCESS_LOG', None)
nginx_error_log=os.getenv('NGINX_ERROR_LOG', None)
if nginx_host:
    fva_conf=fva_conf.replace("server_name _;", "server_name %s;"%nginx_host)
    # El MISMO problema que el de los maps pero en otra tabla y con otro
    # mensaje: un `server_name` largo desborda `server_names_hash_bucket_size`
    # y nginx aborta con `could not build server_names_hash`. Son fallos
    # INDEPENDIENTES sobre el mismo dominio, asi que arreglar solo el del map
    # mueve el error en vez de quitarlo.
    fva_conf = "server_names_hash_bucket_size %d;\n" % bucket_for(len(nginx_host)) + fva_conf
if nginx_error_log:
    fva_conf=fva_conf.replace("error_log /run/logs/nginx-error.log;", "error_log %s;"%nginx_error_log)
if nginx_access_log:
    fva_conf = fva_conf.replace("access_log /run/logs/nginx-access.log;", "access_log %s;" % nginx_access_log)

if os.getenv('ALLOWED_HOSTS', ''):
    # El bucket por defecto (64 bytes) no admite un nombre de host largo: nginx
    # aborta el arranque con "could not build map_hash, you should increase
    # map_hash_bucket_size". Y aborta ENTERO -- gunicorn sigue vivo, asi que el
    # contenedor parece arrancado mientras nginx esta en FATAL y no responde
    # nada. Medido con organilab.solvomanager.devautodeploy.solvosoft.com.
    #
    # Va al PRINCIPIO del archivo, no aqui junto a los maps: nginx fija este
    # valor al cerrar el PRIMER bloque `map`, y el de `$client_ip` ahora vive
    # en nginx-app.conf, mas arriba. Declararlo despues de un `map` se rechaza
    # con `"map_hash_bucket_size" directive is duplicate` aunque aparezca UNA
    # sola vez en todo el archivo: el mensaje se lee como si estuviera
    # repetido y lo que esta es fuera de orden. Verificado con `nginx -t`.
    fva_conf = "map_hash_bucket_size %d;\n" % bucket_for(
        max(len(h) for h in os.getenv('ALLOWED_HOSTS', '').split(','))
    ) + fva_conf

    MAPTEXT="""
map $host $default_host_match {
    %s 1;
    default 0;
}
    """%( " 1;\n    ".join([c for c in os.getenv('ALLOWED_HOSTS', '').split(',')]))

    HOST_MATCH_TEXT="""
 if ($default_host_match = 0) {
        return 404;
 }
"""
    start_text="# start maps"
    end_text="# end maps"
    fva_conf=fva_conf[0:fva_conf.find(start_text)+len(start_text)]+MAPTEXT+fva_conf[fva_conf.find(end_text):]

    start_host_match="# host match"
    end_host_match="# end host match"
    fva_conf=fva_conf[0:fva_conf.find(start_host_match)+len(start_host_match)]+HOST_MATCH_TEXT+fva_conf[fva_conf.find(end_host_match):]


with open('/etc/nginx/sites-enabled/default', 'w') as arch:
     arch.write(fva_conf)


# Update mimetypes
filename = "/etc/nginx/mime.types"
with open(filename, "r") as f:
    data = f.read()

data_new = re.sub(
    r"(application/javascript\s+js;)",
    r"application/javascript   js mjs;",
    data
)

with open(filename, "w") as f:
    f.write(data_new)
