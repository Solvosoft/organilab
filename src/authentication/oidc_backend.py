import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from auth_and_perms.models import Profile, ProfilePermission, Rol
from django.contrib.auth.models import User, Group

from laboratory.models import (
    UserOrganization,
    OrganizationStructure,
)

logger = logging.getLogger(__name__)


class OrganiLabOIDCBackend(OIDCAuthenticationBackend):

    def _get_username(self, claims):
        return (
            claims.get("username")
            or claims.get("email")
            or claims.get("sub", "")
        )[:150]

    def create_user(self, claims):
        email = claims.get("email", "")
        existing = self.UserModel.objects.filter(email__iexact=email)
        if existing.count() > 1:
            logger.error("OIDC: multiple users with email=%s, returning first", email)
        user = existing.first()
        if user:
            return user
        username = self._get_username(claims)
        try:
            user = self.UserModel.objects.create_user(username, email=email)
        except IntegrityError:
            logger.error("OIDC: username conflict for username=%s email=%s", username, email)
            user = self.UserModel.objects.filter(email__iexact=email).first()
            if not user:
                raise
            return user
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        self._update_profile(profile, claims)
        self._assign_default_org(profile)
        self._assign_default_groups(user)
        return user

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", user.first_name)
        user.last_name = claims.get("family_name", user.last_name)
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        self._update_profile(profile, claims)
        return user

    def _update_profile(self, profile, claims):
        phone = claims.get("phone_number", "")
        if phone:
            profile.phone_number = phone
        address = claims.get("address", {})
        if isinstance(address, dict):
            address = address.get("formatted", "")
        if address:
            profile.address = address
        profile.save()

    def get_userinfo(self, access_token, id_token, payload):
        userinfo = super().get_userinfo(access_token, id_token, payload)
        # WSO2 IS may include claims in ID token but not in userinfo endpoint.
        # Merge ID token payload as base, userinfo takes precedence.
        merged = dict(payload)
        merged.update(userinfo)
        logger.debug("OIDC merged claims (id_token + userinfo): %s", merged)
        return merged

    def verify_claims(self, claims):
        logger.debug("OIDC userinfo claims received: %s", list(claims.keys()))
        return bool(claims.get("email") or claims.get("sub"))

    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        if email:
            return self.UserModel.objects.filter(email__iexact=email)
        sub = claims.get("sub")
        logger.warning("OIDC: no email claim, falling back to sub=%s", sub)
        return self.UserModel.objects.none()

    def _assign_default_org(self, profile):
        org_pk = getattr(settings, "DEFAULT_ORG_PK", 0)
        organization = OrganizationStructure.objects.filter(pk=org_pk).first()
        if organization:
            UserOrganization.objects.get_or_create(
                user=profile.user,
                organization=organization,
                type_in_organization=UserOrganization.LABORATORY_USER,
                status=True,
            )

        rol_name = getattr(settings, "DEFAULT_ROL_NAME", "")
        if not org_pk or not rol_name:
            return

        org_ct = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )
        pp, _ = ProfilePermission.objects.get_or_create(
            profile=profile,
            content_type=org_ct,
            object_id=org_pk,
        )
        rol = Rol.objects.filter(name__iexact=rol_name).first()
        if rol and not pp.rol.filter(pk=rol.pk).exists():
            pp.rol.add(rol)

    def _assign_default_groups(self, user):
        groups = Group.objects.filter(name__in=["Profile", "PendingTasks"])
        for group in groups:
            user.groups.add(group)
