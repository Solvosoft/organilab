from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _


def user_is_allowed_on_organization(user, organization):
    if organization is None:
        raise ObjectDoesNotExist('Organization not found')
    if not organization.users.filter(pk=user.pk).exists():
        raise PermissionDenied(_("User %(user)s not allowed on organization %(organization)r ")%{
            'user': user, 'organization': organization})