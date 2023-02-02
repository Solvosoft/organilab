
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def yesno(value):
    if value:
        return mark_safe("""<i class="fa fa-check-circle text-success" aria-hidden="true"></i>""")
    return mark_safe("""<i class="fa fa-times-circle text-danger" aria-hidden="true"></i> """)