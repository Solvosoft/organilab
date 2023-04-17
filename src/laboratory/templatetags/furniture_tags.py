from django.utils.translation import gettext as _
from django import template
from django.utils.safestring import mark_safe

from laboratory.shelf_utils import get_dataconfig

register = template.Library()

@register.filter
def display_furniture(furniture):
    dataconfig=get_dataconfig(furniture.dataconfig)
    dev = '<div class="container" ><div class="row">'

    for col in dataconfig:
        if col:
            dev+='<div class="col ">'
            for data in col:
                dev+='<div class="row ">'
                for item in data:
                    dev+="""
<div class="input-group" >
    <div class="input-group-text" style="background-color: %s">
        <input type="radio" name="shelfselected"   class="form-check-input  shelf"   value="%s">
    </div>
    <div class="card"> 
        <div class="card-body">%s %s</div>
    </div>
    
</div>
"""%(item.color, item.pk, item.name, item.description)

                dev+='</div>'
            dev +='</div>'
    dev+='</div></div>'

    return mark_safe(dev)