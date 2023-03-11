from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from auth_and_perms.models import ProfilePermission, Profile, Rol
from laboratory.models import OrganizationStructureRelations, Laboratory
from laboratory.utils import get_profile_by_organization

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
    profile = ProfilePermission.objects.filter(profile_id=user,
                                               content_type__app_label=lab._meta.app_label,
                                               content_type__model = lab._meta.model_name,
                                               object_id=lab.pk).first()
    roles = []
    if profile:
        for rol in profile.rol.filter(organizationstructure=org):
            datatext="""data-org="%d" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" """%(
                org.pk, user, lab._meta.app_label,  lab._meta.model_name, lab.pk
            )
            roles.append(
                """<span class="applyasrole" data-roleid="%d" style="border-radius: 50px; background: %s; padding: 10px;" title="%s" %s>%s</span>"""%(
                    rol.pk,
                    rol.color.replace('[', '').replace(']', '').replace("'", '').strip(),
                    rol.name,
                    datatext,
                    rol.name[0]
                )
            )
        return " ".join(roles)

def get_related_contenttype_objects(org):
    yield {
        'str': 'General',
        'obj': None
    }
    for lab in org.laboratory_set.all():
        yield {
            'str': str(lab),
            'obj': lab
        }
    for obj in OrganizationStructureRelations.objects.filter(organization=org):
        yield {
            'str': str(obj.content_object),
            'obj': obj.content_object
        }

@register.simple_tag()
def get_organization_table(org):
    profiles = get_profile_by_organization(org.pk)

    # users = set(ProfilePermission.objects.filter(
    #     content_type__app_label=org._meta.app_label,
    #     content_type__model=org._meta.model_name,
    #     object_id=org.pk).values_list('profile_id', flat=True))
    header = "<thead><tr><th>User</th>"
    header2 = "<tr><th></th>"
    body = "<tbody>"

    objects = []
    for obj in get_related_contenttype_objects(org):
        header+='<th>%s</th>'%obj['str']
        dataobj = ''
        if obj['obj']:
            dataobj='data-appname="%s" data-model="%s" data-objectid="%s" '%(obj['obj']._meta.app_label, obj['obj']._meta.model_name, obj['obj'].pk)
        else:
            dataobj = 'data-appname="%s" data-model="%s" ' % ('auth_and_perms', 'profile')

        header2 += '<th><button class="btn btn-sm btn-success applybycontenttype" data-org="%d" %s>+</button></th>'%(org.pk, dataobj)
        objects.append(obj['obj'])
    header+="<th>Apply All</th></tr>"
    header2+="<th></th></tr>"
    header+=header2
    header+="</thead>"
    for profile in profiles:
        body +='<tr data-id="%d"><td>%s</td>'%(profile.user.pk, str(profile))
        for object in objects:
            object = object or profile # in general we use
            role = get_roles(profile.pk, object, org)
            if role:
                body+="<td>%s</td>"%str(role)
            else:
                body+='<td><span class="applyasrole" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" data-org="%d">+</span></td>'%(
                    profile.pk, object._meta.app_label, object._meta.model_name, object.pk, org.pk)
        body+='<td><button class="btn btn-sm btn-success applybyuser" data-org="%d" data-user="%s">+</button></td></tr>'%(org.pk, profile.pk)
    body +="</tbody>"
    return mark_safe(header+body)


@register.simple_tag(takes_context=True)
def has_perm_in_org(context, org_pk,  permission):
    if context['request'].user.is_superuser:
        return True
    app_label, codename = permission.split(".")
    profile_in = ProfilePermission.objects.filter(profile=context['request'].user.profile,
                                                  content_type__app_label='laboratory',
                                                  content_type__model="organizationstructure",
                                                  object_id=org_pk)
    if not profile_in.exists():
        labs = set(Laboratory.objects.filter(
            Q(organization=org_pk)|Q(pk__in=
                OrganizationStructureRelations.objects.filter(
                    organization=org_pk,
                    content_type__app_label='laboratory',
                    content_type__model="laboratory",
                ).values_list('object_id', flat=True)
            )
        ).values_list('pk', flat=True))
        profile_in = ProfilePermission.objects.filter(profile=context['request'].user.profile,
                                                      content_type__app_label='laboratory',
                                                      content_type__model="laboratory",
                                                      object_id__in=labs)


    rols = profile_in.values_list('rol', flat=True)
    rolsquery = Rol.objects.filter(
        pk__in=rols,
        permissions__content_type__app_label=app_label,
        permissions__codename=codename
    )

    return rolsquery.exists()
