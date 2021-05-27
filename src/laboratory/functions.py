from reservations_management.models import ReservedProducts
from laboratory.models import ShelfObject
from django.http import JsonResponse

def return_laboratory_of_shelf_id(request):
    labs = []
    if request.method == 'GET':
        shelf_objects_ids = request.GET.getlist("ids[]")
        for shelf_objects_id in shelf_objects_ids:
            lab_id_queryset = ShelfObject.objects.filter(id=shelf_objects_id).values('shelf__furniture__labroom__laboratory__id')
            for lab_id in lab_id_queryset:
                labs.append(lab_id['shelf__furniture__labroom__laboratory__id'])
        return JsonResponse({'lab_ids': labs})