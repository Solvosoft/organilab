from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe

from auth_and_perms.models import ProfilePermission, Profile

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

def get_roles(user, lab, org):
    org_rols = list(org.rol.all().values_list('pk', flat=True))
    profile = ProfilePermission.objects.filter(profile_id=user,
                                               content_type=ContentType.objects.filter(
                                                app_label=lab._meta.app_label,
                                                model = lab._meta.model_name
                                               ).first(),

                                               object_id=lab.pk).first()
    if profile:
        roles=[]
        profile_rol_list = profile.rol.all().filter(pk__in=org_rols)
        for rol in profile_rol_list:
            roles.append(
                """<span data-profile="%d" data-roleid="%d" style="border-radius: 50px; background: %s; padding: 10px;" title="%s">%s</span>"""%(
                    profile.pk,
                    rol.pk,
                    rol.color.replace('[', '').replace(']', '').replace("'", '').strip(),
                    rol.name,
                    rol.name[0]
                )
            )
        return " ".join(roles)

@register.simple_tag()
def get_organization_table(org):

    users = set(ProfilePermission.objects.filter(object_id=org.pk).values_list('profile_id', flat=True))
    header = "<thead><tr><th>User</th>"
    header2 = "<tr><th></th>"
    body = "<tbody>"

    labs = []
    for lab in org.laboratory_set.all():
        header+='<th>%s</th>'%str(lab)
        header2 += '<th><button class="btn btn-sm btn-success" data-bs-toggle="modal" data-bs-target="#modal%s" data-id="%d" data-url=%s>+</button></th>'%(org.pk, lab.pk, reverse('auth_and_perms:add_rol_by_laboratory'))
        labs.append(lab)

    header+="<th>Apply All</th></tr>"
    header2+="<th></th></tr>"
    header+=header2
    header+="</thead>"
    for user in users:
        profile = Profile.objects.get(pk=user)
        body +='<tr data-id="%d"><td>%s</td>'%(profile.user.pk, str(profile))
        for lab in labs:
            role = get_roles(user, lab, org)
            if role:
                body+="<td>%s</td>"%str(role)
            else:
                body+='<td><span data-user="%d" data-appname="%s" data-model="%s" data-pk="%s">+</span></td>'%(user, lab._meta.app_label,
                                                                                                lab._meta.model_name,
                                                                                                               lab.pk)
        body+='<td><button class="btn btn-sm btn-success" data-bs-toggle="modal" data-bs-target="#modal%s">+</button></td></tr>'%(org.pk)
    body +="</tbody>"
    return mark_safe(header+body)