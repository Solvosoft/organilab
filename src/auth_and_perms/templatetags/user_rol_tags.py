from django import template

from auth_and_perms.models import ProfilePermission

register = template.Library()

@register.simple_tag()
def check_user_rol(user, rol):
    result = False
    profile = user.profile
    pp = ProfilePermission.objects.filter(profile=profile)
    if pp.exists():
        pp = pp.first()
        if rol in pp.rol.all():
            result = True
    return result