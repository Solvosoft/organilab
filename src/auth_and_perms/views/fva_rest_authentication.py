# encoding: utf-8

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''
@date: 16/6/2018
@author: Luis Zarate Montero
@contact: luis.zarate@solvosoft.com
@license: GPLv3
'''
import requests
from django.http.response import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pyfva.clientes.autenticador import ClienteAutenticador
from django.conf import settings
import logging
from django.views.decorators.http import require_http_methods
import json
from django.utils import timezone
from django.contrib.auth import authenticate, login

#from corebase import logger
from ..models import AuthenticateDataRequest, AuthorizedApplication


@csrf_exempt
@require_http_methods(["POST"])
def login_with_bccr(request):
    '''
    Esta vista permite iniciar el proceso de autenticación mediante firma digital, es llamada después de solicitarle
    la identificación al usuario.
    Se encarga de llamar al servicio de autenticación del BCCR con la identificación del usuario y responderle a la vista
    de procesamiento de firma los valores necesarios para que el flujo continue

    :param request: POST -- se debe enviar el campo **Identificacion** el cual contiene el número de identificación del
        usuario a identificar en el formato soportado por el BCCR.

    :return: JSON -- Se retorna un objeto JSON con los siguientes campos

        - FueExitosaLaSolicitud: La solicitud se procesó sin problemas (True, False)
        - TiempoMaximoDeFirmaEnSegundos: Tiempo máximo en que la vista debe mostrarse al usuario, por defecto 240,
        - TiempoDeEsperaParaConsultarLaFirmaEnSegundos: Cada cuantos segundos debe preguntar si la autenticación ya se realizó
        - CodigoDeVerificacion:  Código de verificación de la transacción que debe mostrarse al usuario
        - IdDeLaSolicitud: Código de identificación de la solicitud, usado para consultar el estado de la transacción
        - DebeMostrarElError: Debe mostrar un mensaje al usuario, generalmente usado cuando existen errores
        - DescripcionDelError: Mensaje de error a mostrar si se habilita la opción DebeMostrarElError
        - ResumenDelDocumento: Resumen del documento a firmar

    '''
    identification = request.POST.get('Identificacion', '')
    if identification:
        authclient = ClienteAutenticador(settings.DEFAULT_BUSSINESS,
                                         settings.DEFAULT_ENTITY)
        if authclient.validar_servicio():
            data = authclient.solicitar_autenticacion(identification)
            try:
                if int(data['id_solicitud']) > 0:
                    app = AuthorizedApplication.objects.all().first()
                    headers = {"Authorization": "Token %s" % (app.token),
                               'Content-type': 'application/json', "charset": "utf-8",
                               'Accept': 'application/json'}
                    response = requests.post(app.notification_url+str(data['id_solicitud']), headers=headers)
                    response.raise_for_status()
            except Exception as e:
                pass

        else:
            #logger.warning({'message':"Auth BCCR not available", 'location': __file__})
            data = authclient.DEFAULT_ERROR

        obj = AuthenticateDataRequest.objects.create(
            identification=identification,
            request_datetime=timezone.now(),
            code=data['codigo_verificacion'] or 'N/D',
            status=data['codigo_error'],
            #status_text=data['texto_codigo_error'],
            #expiration_datetime=timezone.now(
            #) - timezone.timedelta(int(data['tiempo_maximo'])),
            id_transaction=int(data['id_solicitud']),
            duration=data['tiempo_maximo']
        )

        request.session['authenticatedata'] = obj.pk

        success = data['codigo_error'] == settings.DEFAULT_SUCCESS_BCCR
        return JsonResponse({
            'FueExitosaLaSolicitud': success,
            'TiempoMaximoDeFirmaEnSegundos': 240,
            'TiempoDeEsperaParaConsultarLaFirmaEnSegundos': 2,
            'CodigoDeVerificacion': data['codigo_verificacion'],
            'IdDeLaSolicitud': data['id_solicitud'],
            'DebeMostrarElError': not success,
            'DescripcionDelError': data['texto_codigo_error'],
            'ResumenDelDocumento': data['resumen'] if "resumen" in data else ""

        })

    return Http404()


def check_signature_window_status_register(request):
    '''
    Verifica si un proceso de firma ya se realizó con éxito, esta vista es llamada por dfva_html para saber cuando el usuario
    ya está autenticado o para saber si existe algún error que deba mostrarse al usuario.
    Esta vista supone que se llama mediante JSONP

    :param request: GET -- Debe ingresarse vía GET los siguientes parámetros

        - callback: Función a llamar después para retornar los datos solicitados
        - IdDeLaSolicitud: Id de transacción usado para verificar el estado de la transacción

    :return: JSON -- Retorna un string con el formato nombre_función(parámetros), la función es la que se ingresa por
        callback y los parámetros son:

            - DebeMostrarElError: Debe mostrar un mensaje al usuario, generalmente usado cuando existen errores
            - DescripcionDelError:   Mensaje de error a mostrar si se habilita la opción DebeMostrarElError
            - FueExitosa: La transacción fue exitosa (no quiere decir que se haya firmado, solo que el proceso de consulta fue exitoso)
            - SeRealizo: True si ya se realizó el proceso de firma por el usuario o si existe un error a mostrar al usaurio
    '''
    callback = request.GET.get('callback')
    pk = request.GET.get('IdDeLaSolicitud', '')
    authdata = AuthenticateDataRequest.objects.filter(
        id_transaction=pk).first()

    sessionkey = None
    if 'authenticatedata' in request.session:
        sessionkey = request.session['authenticatedata']

    if authdata is None or authdata.pk != sessionkey:
        return HttpResponse(
            "%s(%s)" % (
                callback,
                json.dumps(
                    {"ExtensionData": {},
                     "DebeMostrarElError": True,
                     "DescripcionDelError": "Transacción inexistente",
                     "FueExitosa": False,
                     "SeRealizo": True}
                )
            )
        )

    status = authdata.status == settings.DEFAULT_SUCCESS_BCCR
    realizada = authdata.received_notification
    if status and realizada:
        request.session.pop('authenticatedata')
    return HttpResponse(
        "%s(%s)" % (
            callback,
            json.dumps(
                {"ExtensionData": {},
                 "DebeMostrarElError": not status,
                 "DescripcionDelError": "La autenticación fue exitosa",
                 "FueExitosa": status,
                 "SeRealizo": realizada}
            )
        )
    )
