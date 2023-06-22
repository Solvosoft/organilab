import logging

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters import DateTimeFromToRangeFilter
from django_filters import FilterSet, CharFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from rest_framework import serializers

from academic.models import CommentProcedureStep
from academic.models import MyProcedure, Procedure
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure

logger = logging.getLogger('organilab')


class ProcedureStepCommentFilterSet(FilterSet):
    creator_at = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(
            attrs={'placeholder': formats.get_format('DATETIME_INPUT_FORMATS')[0]}))
    creator = CharFilter(field_name='creator', method='filter_user')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(creator__first_name__icontains=value) | Q(
            creator__last_name__icontains=value) | Q(
            creator__username__icontains=value))

    class Meta:
        model = CommentProcedureStep
        fields = ['creator', 'creator_at', 'comment']


class ProcedureStepCommentSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField(required=False)
    creator_at = serializers.DateTimeField(required=False, format=formats.get_format('DATETIME_INPUT_FORMATS')[0])
    comment = serializers.CharField(required=True)

    def get_creator(self, obj):
        try:
            if not obj:
                return _("No user found")
            if not obj.creator:
                return _("No user found")

            name = obj.creator.get_full_name()
            if not name:
                name = obj.creator.username
            return name
        except AttributeError:
            return _("No user found")

    class Meta:
        model = CommentProcedureStep
        fields = '__all__'


class ProcedureStepCommentDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProcedureStepCommentSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class MyProcedureSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    custom_procedure = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.name:
            return obj.name
        return ''

    def get_custom_procedure(self, obj):
        if obj.custom_procedure:
            return obj.custom_procedure.title
        return ''

    def get_status(self, obj):
        if obj.status:
            return _(obj.status)
        return ''

    def get_created_by(self, obj):
        try:
            if not obj:
                return _("No user found")
            if not obj.created_by:
                return _("No user found")

            name = obj.created_by.get_full_name()
            if not name:
                name = obj.created_by.username
            return name
        except AttributeError:
            return _("No user found")

    def get_actions(self, obj):
        org_pk = self.context['view'].kwargs.get('org_pk')
        lab_pk = self.context['view'].kwargs.get('lab_pk')
        procedure_kwargs = {
            'lab_pk': lab_pk,
            'org_pk': org_pk,
            'pk': obj.pk,
        }
        action = ""
        url = reverse('academic:complete_my_procedure', kwargs=procedure_kwargs)
        action += """ <a title='%s' class="pe-2" href='%s'><i class="fa fa-edit text-success" aria-hidden="true"></i>
        </a>""" % (_("Edit"), url,)
        action += """ <a title='%s' class="pe-2 open_modal" data-url="%s" onclick="get_procedure(this)"><i class="fa fa-book"></i></a>
        """ % (_("Reserved"), reverse('academic:get_procedure', kwargs={'org_pk':org_pk,'pk':obj.custom_procedure.pk}))
        action += """ <a title='%s' class="pe-2" onclick="delete_my_procedure(%d)"><i class="fa fa-trash text-danger"
        aria-hidden="true"></i></a>""" % (_("Delete"), obj.custom_procedure.pk)

        return action

    class Meta:
        model = MyProcedure
        fields = ['name', 'custom_procedure', 'status', 'created_by', 'actions']


class MyProcedureDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=MyProcedureSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ProcedureSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_title(self, obj):
        if obj.title:
            return obj.title
        return ''

    def get_description(self, obj):
        if obj.description:
            return obj.description
        return ''

    def get_actions(self, obj):
        org_pk = self.context['view'].kwargs.get('org_pk')
        procedure_kwargs = {
            'org_pk': org_pk,
            'pk': obj.pk,
        }
        action = ""
        action += """<a href="%s" title="%s"><i class="fa fa-eye  fa-sm p-2"></i></a>""" % (
        reverse('academic:procedure_detail', kwargs=procedure_kwargs), _('View Steps'))
        action += """<a href="%s" title="%s"><i class="fa fa-plus text-success p-2"></i></a>""" % (
        reverse('academic:add_steps_wrapper', kwargs=procedure_kwargs), _('New Step'))
        action += """<a href="%s" title="%s"><i class="fa fa-edit  fa-sm p-2"></i></a>""" % (
        reverse('academic:procedure_update', kwargs=procedure_kwargs), _('Edit'))
        action += """<a onclick="delete_procedure(%d,'%s')" title="%s">
        <i class="fa fa-trash text-danger p-2"></i>
        </a>""" % (obj.pk, str(obj.title), _('Remove'))

        return action

    class Meta:
        model = Procedure
        fields = ['title', 'description', 'actions']


class ProcedureDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProcedureSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ValidateUserAccessOrgSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))
