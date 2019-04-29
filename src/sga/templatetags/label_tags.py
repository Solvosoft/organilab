from django import template
from sga.models import RecipientSize

register = template.Library()


@register.assignment_tag
def permissionsUser():
    return 'Permissions Test'
