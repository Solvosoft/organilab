from django.contrib.auth.models import User
from djgentelella.groute import register_lookups
from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework.authentication import SessionAuthentication
from laboratory.utils import get_users_from_organization


class GPaginatorMoreElements(GPaginator):
    page_size = 100

@register_lookups(prefix="risk_users", basename="risk_users")
class UserseslLookup(BaseSelect2View):
    model = User
    fields = ['user__first_name', 'user__last_name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': [],
    }
    permission_classes = (AnyPermissionByAction,)
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= User.objects.filter(pk__in=get_users_from_organization(self.organization))
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = self.request.GET.get("org_pk", None)

        return super().list(request, *args, **kwargs)

