from django.contrib.auth.models import User
from django.db.models import Q
from django_filters import FilterSet
from rest_framework import serializers
from rest_framework.reverse import reverse_lazy

from auth_and_perms.models import Rol, Profile, AuthenticateDataRequest
from auth_and_perms.templatetags.user_rol_tags import get_roles
from laboratory.models import OrganizationStructure, Laboratory


class RolSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)

    class Meta:
        model = Rol
        fields = ["name", "permissions"]


class ProfileAssociateOrganizationSerializer(serializers.Serializer):
    typeofcontenttype = serializers.CharField(required=True)
    user = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all(), required=True)
    organization = serializers.PrimaryKeyRelatedField(many=False,
                                                      queryset=OrganizationStructure.objects.all(),
                                                      required=True)
    laboratory = serializers.PrimaryKeyRelatedField(many=False,
                                                    queryset=Laboratory.objects.all(),
                                                    required=False)


class AuthenticateDataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticateDataRequest
        fields = '__all__'


class AuthenticateDataRequestNotifySerializer(serializers.Serializer):
    id_transaction = serializers.IntegerField()
    data = AuthenticateDataRequestSerializer()


class ContentTypeObjectToPermissionManager(serializers.Serializer):
    org = serializers.PrimaryKeyRelatedField(queryset=OrganizationStructure.objects.all())
    appname = serializers.CharField()
    model = serializers.CharField()
    objectid = serializers.IntegerField(required=False, allow_null=True)


class ProfilePermissionRolOrganizationSerializer(serializers.Serializer):
    rols = serializers.PrimaryKeyRelatedField(many=True, queryset=Rol.objects.all())
    as_conttentype = serializers.BooleanField(required=True)
    as_user = serializers.BooleanField(required=True)
    as_role = serializers.BooleanField(required=True)
    profile = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), allow_null=True, required=False)
    contenttypeobj = ContentTypeObjectToPermissionManager(allow_null=True)
    mergeaction = serializers.ChoiceField(choices=[
        ('append', reverse_lazy('Append')), ('sustract', reverse_lazy('Sustract')),
        ('full', reverse_lazy('Only roles selected'))
    ])


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationStructure
        fields = ['name', 'parent']


class ProfileFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(
                    user__username__icontains=search)
            )
        return queryset

    class Meta:
        model = Profile
        fields = {'user': ['exact']}


class ProfileSerializer(serializers.ModelSerializer):
    rols = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_rols(self, obj):
        contenttypeobj = self.context['view'].contenttypeobj
        org = self.context['view'].organization
        rol = get_roles(obj.pk, contenttypeobj, org)
        if not rol:
            datatext = """data-org="%d" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" """ % (
                org.pk, obj.pk, contenttypeobj._meta.app_label, contenttypeobj._meta.model_name, contenttypeobj.pk
            )

            rol = """
            <i %s class="fa fa-user-md" onclick="newuserrol(%s)" id="profile_%s" aria-hidden="true"></i>
            """ % (datatext, obj.pk, obj.pk)
        return rol

    def get_user(self, obj):
        return str(obj)

    def get_action(self, obj):
        contenttypeobj = self.context['view'].contenttypeobj
        org = self.context['view'].organization
        datatext = """ id="ndel_%s" data-org="%s" data-profile="%s" data-appname="%s" data-model="%s" data-objectid="%s" """ % (
            obj.pk, str(contenttypeobj), str(obj), contenttypeobj._meta.app_label, contenttypeobj._meta.model_name,
            contenttypeobj.pk
        )

        return """
        <i %s class="fa fa-trash mr-2" onclick="deleteuserlab(%s, %s)" aria-hidden="true"></i>
        """ % (datatext, obj.pk, org.pk)

    class Meta:
        model = Profile
        fields = ['user', 'rols', 'action']


class ProfileRolDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProfileSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class DeleteUserFromContenttypeSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(many=False, queryset=Profile.objects.all())
    app_label = serializers.CharField()
    model = serializers.CharField()
    object_id = serializers.IntegerField()
    organization = serializers.PrimaryKeyRelatedField(many=False, queryset=OrganizationStructure.objects.all())
    disable_user = serializers.BooleanField(default=False)
