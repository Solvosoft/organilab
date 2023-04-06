from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from django.http import Http404

def user_is_allowed_on_organization(user, organization):
    if organization is None:
        raise Http404('Organization not found')
    if not organization.users.filter(user=user).exists():
        raise HttpResponseForbidden(_("User %(user)s not allowed on organization %r ")%(user, organization))