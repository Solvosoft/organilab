
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponse
from laboratory import utils as utils_lab
from laboratory import shelf_utils
import json

STATUS_304 =  {'detail' : _('Not Modified')}
STATUS_400 =  {'detail' : _('Not Found')}
STATUS_500 =  {'detail' : _('error')}

RESPONSE_VALUE= {304:STATUS_304,400:STATUS_400,500:STATUS_500}

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
            # check if is FK, to check it
            
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

def list_shelf_dataconfig(dataconfig=None):
        listed=[]
        try :
            if dataconfig:
                dataconfig = json.loads(dataconfig) 
                for irow, row in enumerate(dataconfig):
                    for icol, col in enumerate(row):
                        if col:
                            val = None
                            if type(col) == str:
                                val = col.split(",")
                            elif type(col) == int:
                                val = [col]
                            elif type(col) == list:
                                val = col
                            else:
                                continue
                            for ival in val:
                                listed.append(ival)
        except ValueError:
             return False                     
        return listed 
        
def get_valid_lab(lab_pk,user,perm):
    lab =  get_object_or_404(Laboratory, pk=lab_pk)
    perm = utils_lab.check_lab_group_has_perm(user,lab,perm)
    return( lab, perm)



    
    
    


