
from django import template
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from laboratory.models import Laboratory
from django.shortcuts import get_object_or_404

register = template.Library()

@register.simple_tag
def print_position(*args,**kwargs):
    
    shelf_position = ""
    varrow = args[0]
    varcol = args[1]
    varcount = args[3]
    
    if varrow < 26:
        shelf_position = chr(varrow+65)
    else:
        shelf_position = chr(varrow+39) + chr(varrow+39)
                            
    shelf_position = shelf_position + str(varcol+1)
    
    if varcount > 1:
        shelf_position = shelf_position + "S" + str(args[2]+1)
    
    return shelf_position

@register.simple_tag
def print_shelf(*args,**kwargs):
    
    shelf = ""
    row = args[0]
    col = args[1]
    varrow = int(row)
    varcol = int(col)
    
    if varrow < 26:
        shelf = chr(varrow+65)
    else:
        shelf = chr(varrow+39) + chr(varrow+39)
        
    shelf = shelf + str(varcol+1)
    
    return shelf

@register.simple_tag(takes_context=True)
def get_laboratory_name(context):
    request = context['request']
    lab_pk = request.session.get('lab_pk')
    if lab_pk is not None:
        return get_object_or_404(Laboratory, pk=lab_pk)
    else:
        # FIXME: find the way to redirect to select_lab
        return redirect(reverse('laboratory:select_lab'))
