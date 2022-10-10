from django import template
from sga.models import RecipientSize, PersonalTemplateSGA

register = template.Library()


@register.simple_tag
def get_personal_template(substance):
    result= None
    template = PersonalTemplateSGA.objects.filter(label__substance__pk=substance).first()
    if template:
        result=template.pk

    return result

@register.simple_tag
def permissionsUser():
    return 'Permissions Test'
