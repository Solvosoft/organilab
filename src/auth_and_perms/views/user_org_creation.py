from datetime import timedelta
from functools import partial
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import qrcode.image.svg
from auth_and_perms.forms import (
    CreationUserOrganization,
    AddProfileForm,
    AddProfileDigitalSignatureForm,
)
from auth_and_perms.models import (
    RegistrationUser,
    UserTOTPDevice,
    Profile,
    ProfilePermission,
    Rol,
)
from laboratory.models import OrganizationStructure, UserOrganization
from django.utils.translation import gettext_lazy as _


def register_user_to_platform(request):
    form = CreationUserOrganization()
    if request.method == "POST":
        form = CreationUserOrganization(request.POST)
        if form.is_valid():
            instance = form.save()
            instance.active = False
            instance.save()
            RegistrationUser.objects.create(
                user=instance,
                registration_method=form.cleaned_data["validation_method"],
                expired_date=now() + timedelta(days=5),
                organization_name=form.cleaned_data["organization_name"],
            )
            if form.cleaned_data["validation_method"] == "1":
                device = TOTPDevice(user=instance, name=instance.username)
                device.save()
                code = UserTOTPDevice(
                    code=f"{instance.pk}{device.pk}", user=instance, totp_device=device
                )
                code.save()
                return redirect(
                    reverse(
                        "auth_and_perms:user_org_creation_totp", args=(instance.pk,)
                    )
                )
            else:
                return redirect(
                    reverse(
                        "auth_and_perms:create_profile_by_digital_signature",
                        args=(instance.pk,),
                    )
                )

            return redirect(form.cleaned_data["next"] or "/")
    context = {"form": form}
    return render(
        request, "auth_and_perms/create_user_organization.html", context=context
    )


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

    group, _x = Group.objects.get_or_create(name="RegisterOrganization")
    rol = Rol.objects.create(name=_("Organization Management"))
    ct = ContentType.objects.filter(
        app_label=organization._meta.app_label, model=organization._meta.model_name
    ).first()
    pp, none = ProfilePermission.objects.get_or_create(
        profile=profile, content_type=ct, object_id=organization.pk
    )
    rol.permissions.add(*[x for x in group.permissions.all()])
    pp.rol.add(rol)
    organization.rol.add(rol)
    set_profile_administrator(profile, rol)


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
    user.active = True
    user.save()


#    UserOrganization.objects.create(user=user, organization=org, status=True, type_in_organization=user_type)


@transaction.atomic
def create_profile_otp(request, pk):
    user = get_object_or_404(User, pk=pk)
    device = TOTPDevice.objects.get(user__pk=pk)
    form = partial(AddProfileForm, user)
    if request.method == "POST":
        form = form(
            data=request.POST,
            initial={"otp_device": "otp_totp.totpdevice/%d" % device.pk},
        )
        if form.is_valid():
            reguser = RegistrationUser.objects.filter(
                user=user,
                registration_method=1,
                expired_date__gte=now(),
            ).first()
            if reguser:
                create_user_organization(
                    user, reguser.organization_name, form.cleaned_data
                )
                reguser.delete()
                return render(
                    request,
                    "auth_and_perms/create_user_success.html",
                )
            else:
                messages.error(
                    request,
                    _(
                        "You have no creation process, maybe it was expired, please try to register again"
                    ),
                )
                return redirect(reverse("auth_and_perms:register_user_to_platform"))
    else:
        form = form(
            initial={
                "otp_device": "otp_totp.totpdevice/%d" % device.pk,
                "email": user.username,
            }
        )
    context = {"form": form, "user": user.pk}
    return render(
        request, "auth_and_perms/create_user_organization_totp.html", context=context
    )


@transaction.atomic
def create_profile_by_digital_signature(request, pk):

    user = get_object_or_404(User, pk=pk)

    form = AddProfileDigitalSignatureForm
    if request.method == "POST":
        form = form(data=request.POST)
        if form.is_valid():
            reguser = RegistrationUser.objects.filter(
                user=user,
                registration_method=2,
                expired_date__gte=now(),
            ).first()
            if reguser:
                create_user_organization(
                    user, reguser.organization_name, form.cleaned_data
                )
                reguser.delete()
                return render(
                    request,
                    "auth_and_perms/create_user_success.html",
                )
            else:
                messages.error(
                    request,
                    _(
                        "You have no creation process, maybe it was expired, please try to register again"
                    ),
                )
                return redirect(reverse("auth_and_perms:register_user_to_platform"))
    else:
        form = form()
    context = {"form": form, "user": user.pk}
    return render(
        request,
        "auth_and_perms/create_user_organization_digital_signature.html",
        context=context,
    )


def show_QR_img(request, pk):
    device = TOTPDevice.objects.get(user__pk=pk)
    img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)
    response = HttpResponse(content_type="image/svg+xml")
    img.save(response)
    return response
