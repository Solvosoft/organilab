from django import template
from sga.models import RecipientSize

register = template.Library()


@register.simple_tag
def permissionsUser():
    return 'Permissions Test'
