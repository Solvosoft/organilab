
from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404

from laboratory import utils as utils_lab


# models
from laboratory.models import (Laboratory,
                               LaboratoryRoom, 
                               Furniture,
                               Shelf,
                               ShelfObject,
                               Object
                                )


def filters_params_api(queryset,params,model):
    query_models = None
    for key in params:
        if hasattr(model, key):
            value = params.get(key)
            tabquery= "%s__contains"%key 
            
            if query_models is None:
                 query_models = Q (**{tabquery: value}) 
            else:
                 query_models |= Q  (**{tabquery: value}) 
                 
        if query_models is None:
            return queryset
        else:          
            print (query_models)
            return queryset.filter(query_models)
    
    
def get_valid_lab(lab_pk,user,perm):
    lab =  get_object_or_404(Laboratory, pk=lab_pk)
    perm = utils_lab.check_lab_group_has_perm(user,lab,perm)
    
    if (perm):
        return lab
    return HttpResponse(status=403)
