from django import template
from sga.models import RecipientSize, DisplayLabel

register = template.Library()


@register.simple_tag
def get_personal_template(substance):
    result = None
    template = DisplayLabel.objects.filter(label__substance__pk=substance).first()
    if template:
        result = template.pk
    return result


@register.simple_tag
def permissionsUser():
    return "Permissions Test"
