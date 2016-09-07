
from django import template

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