
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from djgentelella.groute import register_lookups
from djgentelella.permission_management import AnyPermissionByAction, \
    AllPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer, \
    ValidateLabOrgObjectSerializer, ValidateOrganizationSerializer, \
    UserAccessOrgLabValidateSerializer
from auth_and_perms.models import Rol, Profile
from laboratory.models import Object, Catalog, Provider, ShelfObject, EquipmentType, \
    Laboratory
from laboratory.shelfobject.serializers import ValidateUserAccessShelfSerializer, \
    ValidateUserAccessShelfTypeSerializer
from laboratory.shelfobject.utils import get_available_containers_for_selection, \
    get_containers_for_cloning
from laboratory.utils import get_pk_org_ancestors, get_users_from_organization
from laboratory.utils_base_unit import get_related_units
from risk_management.models import Regent, Buildings


class GPaginatorMoreElements(GPaginator):
    page_size = 100

@register_lookups(prefix="rol", basename="rolsearch")
class RolGModelLookup(BaseSelect2View):
    model = Rol
    fields = ['name']

@register_lookups(prefix="organization_rols", basename="organization_rols")
class OrganizationRolslLookup(BaseSelect2View):
    model = Rol
    org= None
    fields = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(pk__in=self.org.rol.values_list('pk',flat=True))
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="object", basename="objectsearch")
class ObjectGModelLookup(BaseSelect2View):
    model = Object
    fields = ['code', 'name']


@register_lookups(prefix="objectorgsearch", basename="objectorgsearch")
class ObjectGModelLookup(BaseSelect2View):
    model = Object
    fields = ['code', 'name']
    org_pk = None
    shelf = None
    shelfobjet_type = None
    serializer = None
    authentication_classes = [SessionAuthentication]
    perms ={
        'list': ["laboratory.view_object"],
    }
    permission_classes = (AnyPermissionByAction,)


    def get_queryset(self):
        if self.shelf and self.shelf.limit_only_objects and self.shelfobjet_type:
            return self.shelf.available_objects_when_limit.filter(type=self.shelfobjet_type)

        queryset = super().get_queryset()

        if self.org_pk and self.shelfobjet_type:
            organizations = get_pk_org_ancestors(self.org_pk.pk)
            queryset = queryset.filter(organization__in=organizations, type=self.shelfobjet_type)
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):

        self.serializer = ValidateUserAccessShelfTypeSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            self.shelf = self.serializer.validated_data['shelf']
            self.shelfobjet_type = self.serializer.validated_data['objecttype']
            self.org_pk = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="userbase", basename="userbase")
class UserLookup(BaseSelect2View):
    model = User
    fields = ['username']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


@register_lookups(prefix="catalogunit", basename="catalogunit")
class CatalogUnitLookup(BaseSelect2View):
    model = Catalog
    fields = ['description']
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_catalog"],
    }
    permission_classes = (AnyPermissionByAction,)
    serializer = None
    shelf = None

    def get_queryset(self):
        queryset = super().get_queryset().filter(key="units")
        if self.shelf:
            if self.shelf.measurement_unit:
                subunit = self.shelf.measurement_unit
                return get_related_units(subunit, queryset)
            else:
                return queryset
        else:
            return queryset.none()

    def list(self, request, *args, **kwargs):

        self.serializer = ValidateUserAccessShelfSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            self.shelf = self.serializer.validated_data['shelf']
            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="catalogunitIncDec", basename="catalogunitIncDec")
class CatalogUnitIncreaseDecrease(BaseSelect2View):
    model = Catalog
    fields = ['description']
    authentication_classes = [SessionAuthentication]

    perms = {
        'list': ["laboratory.view_catalog"],
    }

    permission_classes = (AllPermissionByAction,)
    serializer = None
    shelf = None
    shelfobject = None

    def get_queryset(self):
        queryset = super().get_queryset().filter(key="units")
        if self.shelf:
            if self.shelfobject:
                return get_related_units(self.shelfobject.measurement_unit, queryset)
            else:
                return queryset
        else:
            return self.model.objects.none()

    def list(self, request, *args, **kwargs):

        self.serializer = ValidateUserAccessShelfSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            self.shelf = self.serializer.validated_data['shelf']
            self.shelfobject = self.serializer.validated_data['shelfobject']

            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="available-container-search", basename="available-container-search")
class AvailableContainerLookup(BaseSelect2View):
    model = ShelfObject
    fields = ['object__name',
              'object__code',
              'object__materialcapacity__capacity_measurement_unit__description']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {"list": ["laboratory.view_shelfobject"]}
    permission_classes = (AllPermissionByAction,)
    serializer = None
    laboratory = None
    shelf = None

    def get_text_display(self, obj):
        text_display = f"[" + _("Shelf") + f" {obj.shelf.name}] - {obj.object.code} {obj.object.name}"
        if hasattr(obj.object, 'materialcapacity'):
            text_display += f" - {obj.object.materialcapacity.capacity} {obj.object.materialcapacity.capacity_measurement_unit.description}"
        return text_display

    def get_queryset(self):
        if self.laboratory and self.shelf:
            queryset = get_available_containers_for_selection(self.laboratory.pk, self.shelf.pk)
        else:
            queryset = ShelfObject.objects.none()
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            self.laboratory = self.serializer.validated_data['laboratory']
            self.shelf = self.serializer.validated_data['shelf']
            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="container-for-cloning-search", basename="container-for-cloning-search")
class ContainersForCloningLookup(BaseSelect2View):
    model = Object
    fields = ['name',
              'code',
              'materialcapacity__capacity_measurement_unit__description']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_object"],
    }
    permission_classes = (AnyPermissionByAction,)
    serializer = None
    org = None
    shelf = None

    def get_text_display(self, obj):
        text_display = f"{obj.code} {obj.name}"
        if hasattr(obj, 'materialcapacity'):
            text_display += f" - {obj.materialcapacity.capacity} {obj.materialcapacity.capacity_measurement_unit.description}"
        return text_display

    def get_queryset(self):
        if self.org and self.shelf:
            queryset = get_containers_for_cloning(self.org.pk, self.shelf.pk)
        else:
            queryset = Object.objects.none()
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            self.shelf= self.serializer.validated_data['shelf']
            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="shelfobject_status_search", basename="shelfobject_status_search")
class ShelfObject_StatusModelLookup(BaseSelect2View):
    model = Catalog
    fields = ['description']
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_catalog"],
    }

    permission_classes = (AnyPermissionByAction,)

    def get_queryset(self):
        queryset = super().get_queryset().filter(key='shelfobject_status')
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            self.org_pk = self.serializer.validated_data['organization']
            self.laboratory = self.serializer.validated_data['laboratory']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="provider", basename="provider")
class ProviderLookup(BaseSelect2View):
    model = Provider
    fields = ['name']
    ordering = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_provider"],
    }
    permission_classes = (AnyPermissionByAction,)
    laboratory, serializer = None, None

    def get_queryset(self):
        queryset = super().get_queryset()
        result = queryset.none()
        if self.laboratory:
            result = queryset.filter(laboratory=self.laboratory)
        return result

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.laboratory = self.serializer.validated_data['laboratory']
            return super().list(request, *args, **kwargs)

        return Response({
                'status': 'Bad request',
                'errors': self.serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="objectorgavailable", basename="objectorgavailable")
class ObjectAvailableLookup(BaseSelect2View):
    model = Object
    fields = ['code', 'name']
    org_pk = None
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_object",],
    }
    permission_classes = (AnyPermissionByAction,)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.org_pk:
            organizations = get_pk_org_ancestors(self.org_pk.pk)
            queryset = queryset.filter(organization__in=organizations)
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org_pk = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="object_providers", basename="object_providers")
class ObjectProvidersLookup(BaseSelect2View):
    model = Provider
    fields = ['name']
    org_pk = None
    obj = None
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_provider"]
    }
    permission_classes = (AnyPermissionByAction,)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.org_pk and self.obj and hasattr(self.obj,"equipmentcharacteristics"):
            queryset = queryset.filter(pk__in=self.obj.equipmentcharacteristics.providers.values_list('pk',flat=True))
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateLabOrgObjectSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org_pk = self.serializer.validated_data['organization']
            self.obj = self.serializer.validated_data['object']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="organization_roles", basename="organization_roles")
class OrganizationRolslLookup(BaseSelect2View):
    model = Rol
    org= None
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(pk__in=self.org.rol.values_list('pk',flat=True))
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)



@register_lookups(prefix="instrumentalfamily", basename="instrumentalfamily")
class InstrumentalFamilyLookup(BaseSelect2View):
    model = Catalog
    fields = ['description']
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_catalog"],
    }
    permission_classes = (AnyPermissionByAction,)

    serializer = None

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(key="instrumental_family")

    def list(self, request, *args, **kwargs):
        self.serializer = UserAccessOrgLabValidateSerializer(data=request.GET, context={'user': request.user})
        if self.serializer.is_valid():
            return super().list(request, *args, **kwargs)
        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="org_profiles", basename="org_profiles")
class OrganizationProfileslLookup(BaseSelect2View):
    model = Profile
    org= None
    fields = ['user__first_name', 'user__last_name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_Profile"],
    }
    permission_classes = (AnyPermissionByAction,)
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(pk__in=self.org.users.values_list('profile__pk',flat=True)).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_text_display(self, obj):
        name = obj.user.get_full_name()
        if not name:
            name = obj.username
        return name

@register_lookups(prefix="org_providers", basename="org_providers")
class OrganizationProviderslLookup(BaseSelect2View):
    model = Provider
    org= None
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    perms = {
        'list': ["laboratory.view_provider"],
    }
    permission_classes = (AnyPermissionByAction,)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(laboratory__organization=self.org).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="userorg", basename="userorg")
class UsersOrganizationsLookup(BaseSelect2View):
    model = User
    fields = ['first_name', 'last_name']
    org= None
    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    perms = {
        'list': ["laboratory.view_user"],
    }
    permission_classes = (AnyPermissionByAction,)
    org= None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(organizationstructure=self.org).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET, context={'user': request.user})

        if self.serializer.is_valid():
            self.org = self.serializer.validated_data['organization']
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_text_display(self, obj):
        name = obj.get_full_name()
        if not name:
            name = obj.username
        return name


@register_lookups(prefix="equipmenttype", basename="equipmenttype")
class EquipmentTypeLookup(BaseSelect2View):
    model = EquipmentType
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["laboratory.view_equipmenttype"],
    }
    permission_classes = (AnyPermissionByAction,)

    def list(self, request, *args, **kwargs):
        serializer = UserAccessOrgLabValidateSerializer(data=request.GET, context={'user': request.user})

        if serializer.is_valid():
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="risk_users", basename="risk_users")
class UserseslLookup(BaseSelect2View):
    model = User
    fields = ['first_name', 'last_name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': [],
    }
    permission_classes = ()
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset= User.objects.filter(pk__in=get_users_from_organization(self.organization))
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.organization = self.request.GET.get("org_pk", None)

        return super().list(request, *args, **kwargs)

@register_lookups(prefix="risk_regents", basename="risk_regents")
class RegentslLookup(BaseSelect2View):
    model = Regent
    fields = ['user']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': [],
    }
    permission_classes = ()
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset= Regent.objects.filter(user__pk__in=get_users_from_organization(self.organization))
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.organization = self.request.GET.get("org_pk", None)

        return super().list(request, *args, **kwargs)

@register_lookups(prefix="risk_building", basename="risk_building")
class BuildinglLookup(BaseSelect2View):
    model = Buildings
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': [],
    }
    permission_classes = ()
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset= Buildings.objects.filter(organization__pk=self.organization)
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.organization = self.request.GET.get("org_pk", None)
        print(request.GET)

        return super().list(request, *args, **kwargs)


@register_lookups(prefix="risk_laboratory", basename="risk_laboratory")
class RiskLaboratorylLookup(BaseSelect2View):
    model = Buildings
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': [],
    }
    permission_classes = ()
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset= Laboratory.objects.filter(organization__pk=self.organization)
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.organization = self.request.GET.get("org_pk", None)

        return super().list(request, *args, **kwargs)


@register_lookups(prefix="risk_structure", basename="risk_structure")
class RiskStructurelLookup(BaseSelect2View):
    model = Catalog
    fields = ['description']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    perms = {
        'list': ["risk_management.view_structure"],
    }
    permission_classes = (AnyPermissionByAction,)
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset= queryset.filter(key="structure_type")
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.organization = self.request.GET.get("org_pk", None)

        return super().list(request, *args, **kwargs)

