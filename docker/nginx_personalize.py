import os

with open('/etc/nginx/sites-enabled/default', 'r') as arch:
    fva_conf = arch.read()

nginx_host=os.getenv('NGINX_HOST', None)
nginx_access_log=os.getenv('NGINX_ACCESS_LOG', None)
nginx_error_log=os.getenv('NGINX_ERROR_LOG', None)
if nginx_host:
    fva_conf=fva_conf.replace("server_name _;", "server_name %s;"%nginx_host)
if nginx_error_log:
    fva_conf=fva_conf.replace("error_log /run/logs/nginx-error.log;", "error_log %s;"%nginx_error_log)
if nginx_access_log:
    fva_conf = fva_conf.replace("access_log /run/logs/nginx-access.log;", "access_log %s;" % nginx_access_log)

if os.getenv('ALLOWED_HOSTS', ''):
    MAPTEXT="""
map $proxy_add_x_forwarded_for $client_ip {
  "~^([^,]+)" $1;
  default     "";
}
map $http_host $default_host_match {
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


