from base64 import b64decode

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from pyEQL.chemical_formula import get_element_names

from laboratory.models import Object


class ReactiveMolecularFormulaAPIView(APIView):
    def get(self, request, lab_pk, format=None):
        try:
            name = b64decode(request.GET.get('name'))

            obj = Object.objects.filter(molecular_formula=name).first()
            if obj:
                obj_name = obj.name
            else:
                obj_name = get_element_names(name.decode())

            result = {
                'name': obj_name
            }
            status_code = status.HTTP_200_OK
        except Exception as e:
            result = {
                'name': "No se encontró la fórmula",
                'msg': str(e)
            }
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)