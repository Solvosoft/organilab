
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponse
from laboratory import utils as utils_lab


STATUS_400 =  "{'detail' :'Not Found'}"
STATUS_500 =  "{'detail' :'error'}"

RESPONSE_VALUE= {400:STATUS_400,500:STATUS_500}

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
            if key in ('id','pk'):
                tabquery = 'pk'                
                
            if query_models is None:
                 query_models = Q (**{tabquery: value}) 
            else:
                 query_models |= Q  (**{tabquery: value}) 
                 
        if query_models is None:
            return queryset
        else:          
            return queryset.filter(query_models)
    
def get_response_code(code):
    try:
       return  HttpResponse(RESPONSE_VALUE[code],status=code, content_type='application/json')
    except (KeyError): 
         return  HttpResponse(RESPONSE_VALUE[500],status=500, content_type='application/json')

        
def get_valid_lab(lab_pk,user,perm):
    lab =  get_object_or_404(Laboratory, pk=lab_pk)
    perm = utils_lab.check_lab_group_has_perm(user,lab,perm)
    return( lab, perm)

