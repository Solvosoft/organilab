from ..models import AuthenticateDataRequest


def reciba_notificacion(data):
    """
      Recibe la notificación del BCCR

      :params data: Es un diccionario con los siguientes atributos

          * **id_solicitud:**  Id de la solicitud del BCCR
          * **documento:** Documento firmado
          * **fue_exitosa:** si fue exitosa la firma
          * **codigo_error:** código de error
          * **hash_docfirmado:** Hash del documento ya firmado
          * **hash_id:**  id del hash con que se genero el hash_docfirmado puede ser 1. Sha256, 2. Sha384  3. Sha512

      No requiere retornar nada

      """

    request = AuthenticateDataRequest.objects.filter(
        id_transaction=data['id_solicitud']).first()
    if request is None:
         return

    request.status = data['codigo_error']
    request.received_notification = True
    request.sign_document = data['documento']
    #request.hash_docsigned = data['hash_docfirmado']
    #request.hash_id_docsigned = data['hash_id']
    request.save()


def valide_servicio(data):
    return True

