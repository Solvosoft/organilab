from reservations_management.models import ReservedProducts
from laboratory.models import ShelfObject
from django.http import JsonResponse


def return_laboratory_of_shelf_id(request):
    labs = []
    if request.method == 'GET':
        values_input = request.GET.getlist("ids[]")
        for value in values_input:
            shelf_object = ShelfObject.objects.filter(id=value)
            print(shelf_object)
        return JsonResponse({'lab_ids': values_input})