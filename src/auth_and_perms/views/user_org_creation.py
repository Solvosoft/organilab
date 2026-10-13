from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import qrcode.image.svg
from auth_and_perms.forms import RolListForm
from auth_and_perms.models import (
    Profile,
    ProfilePermission,
    Rol,
)
from laboratory.models import OrganizationStructure, UserOrganization
from django.utils.translation import gettext_lazy as _


def set_profile_administrator(profile, rol):
    ct = ContentType.objects.filter(
        app_label=profile._meta.app_label, model=profile._meta.model_name
    ).first()
    pp, none = ProfilePermission.objects.get_or_create(
        profile=profile, content_type=ct, object_id=profile.pk
    )
    pp.rol.add(rol)


def set_rol_administrator_on_org(
    profile, organization, type_in_organization=UserOrganization.ADMINISTRATOR
):
    UserOrganization.objects.create(
        organization=organization,
        user=profile.user,
        type_in_organization=type_in_organization,
    )

    if organization.parent is None:
        group, _x = Group.objects.get_or_create(name="RegisterOrganization")
        rol = Rol.objects.create(name=_("Organization Management"))
        ct = ContentType.objects.filter(
            app_label=organization._meta.app_label, model=organization._meta.model_name
        ).first()
        pp, _created = ProfilePermission.objects.get_or_create(
            profile=profile, content_type=ct, object_id=organization.pk
        )
        rol.permissions.add(*[x for x in group.permissions.all()])
        pp.rol.add(rol)
        organization.rol.add(rol)
        set_profile_administrator(profile, rol)
    else:
        root_org = organization.root
        rol = Rol.objects.filter(
            name=_("Organization Management"), organizationstructure=root_org
        ).first()
        if rol:
            ct = ContentType.objects.filter(
                app_label=organization._meta.app_label,
                model=organization._meta.model_name,
            ).first()
            pp, _created = ProfilePermission.objects.get_or_create(
                profile=profile, content_type=ct, object_id=organization.pk
            )
            pp.rol.add(rol)


def create_user_organization(
    user, organization, data, user_type=UserOrganization.LABORATORY_USER
):
    profile = Profile.objects.create(
        user=user,
        phone_number=data["phone_number"],
        id_card=data["id_card"],
        job_position=data["job_position"],
        language=data["language"],
    )
    if isinstance(organization, str):
        org = OrganizationStructure.objects.create(name=organization)
    else:
        org = organization
    set_rol_administrator_on_org(profile, org, type_in_organization=user_type)
    for group_name in ["Profile", "PendingTasks", "SGAView"]:
        group = Group.objects.filter(name=group_name).first()
        if group:
            user.groups.add(group)
    user.active = True
    user.save()


def show_QR_img(request, pk):
    device = TOTPDevice.objects.get(user__pk=pk)
    img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)
    response = HttpResponse(content_type="image/svg+xml")
    img.save(response)
    return response


@login_required()
@permission_required("auth_and_perms.view_profile", raise_exception=True)
def get_users(request):
    return render(
        request, "auth_and_perms/user_list.html", context={"form": RolListForm()}
    )
