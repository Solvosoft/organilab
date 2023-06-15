from django.conf import settings
import logging

from django.db.models import Q
from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters import DateTimeFromToRangeFilter
from django_filters import FilterSet, CharFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from rest_framework import serializers
from sga.models import ReviewSubstance, SecurityLeaf
from academic.models import CommentProcedureStep, MyProcedure, Procedure
from django.utils import formats
from django_filters import DateTimeFromToRangeFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from academic.models import CommentProcedureStep
from sga.models import ReviewSubstance, SecurityLeaf

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
    comment= serializers.CharField(required=True)

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


class ReviewSubstanceFilterSet(FilterSet):
    class Meta:
        model = ReviewSubstance
        fields = {
            'substance__comercial_name': ['icontains'],
        }

    @property
    def qs(self):
        queryset = super().qs
        name = self.request.GET.get('creator__icontains')
        if name:
            queryset = queryset.annotate(
                fullname=Concat('substance__creator__first_name', Value(' '),
                                'substance__creator__last_name'))
            queryset = queryset.filter(Q(fullname__icontains=name) | Q(
                substance__creator__username__icontains=name)).distinct()
        return queryset


class ReviewSubstanceSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    comercial_name = serializers.SerializerMethodField()

    def get_creator(self, obj):
        name = None
        if obj.substance:
            if obj.substance.created_by:
                name = obj.substance.created_by.get_full_name()
                if not name:
                    name = obj.substance.created_by.username
        return name or ''

    def get_comercial_name(self, obj):
        if obj.substance:
            return obj.substance.comercial_name
        return ''

    def get_action(self, obj):
        obj_kwargs = {
            'org_pk': obj.substance.organization.pk
        }
        obj_kwargs.update({'pk': obj.substance.pk})
        detail_url = reverse('sga:detail_substance', kwargs=obj_kwargs)
        security_leaf_pdf_url = reverse('sga:security_leaf_pdf',
                                        kwargs={'org_pk': obj.substance.organization.pk,
                                                'substance': obj.substance.pk})
        action = ""

        if not obj.is_approved:
            obj_kwargs.update({'pk': obj.pk})
            approve_url = reverse('sga:accept_substance', kwargs=obj_kwargs)
            action += """ <button title='%s' type ='button' data-url='%s' class ='btn btn-info text-white btn_review'>
            <i class='icons fa fa-check'></i></button>""" % (_("Approve"), approve_url,)

        action += """<a class ='btn btn-warning' title='%s' href='%s'><i class='icons fa fa-eye'></i></a>""" \
                  % (_("Detail"), detail_url,)
        leaf = SecurityLeaf.objects.filter(substance=obj.substance)
        if leaf.exists():
            action += """<a class='btn  btn-md  btn-danger' title='%s' href='%s'><i class='icons fa fa-file-pdf-o'
             aria-hidden='true'></i></a>""" % (
            _("Generate PDF"), security_leaf_pdf_url,)
        return action

    class Meta:
        model = ReviewSubstance
        fields = ['creator', 'comercial_name', 'action']


class ReviewSubstanceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReviewSubstanceSerializer(), required=True)
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
        org_pk=self.context['view'].kwargs.get('org_pk')
        lab_pk=self.context['view'].kwargs.get('lab_pk')
        procedure_kwargs = {
            'lab_pk': lab_pk,
            'org_pk': org_pk,
            'pk': obj.pk,
        }
        action = ""
        url = reverse('academic:complete_my_procedure', kwargs=procedure_kwargs)
        action += """ <a title='%s' class="pe-2" href='%s'><i class="fa fa-edit text-success" aria-hidden="true"></i>
        </a>""" % (_("Edit"), url,)
        action += """ <a title='%s' class="pe-2 open_modal" onclick="get_procedure(%d)"><i class="fa fa-book"></i></a>
        """ % (_("Reserved"), obj.custom_procedure.pk)
        action += """ <a title='%s' class="pe-2" onclick="delete_my_procedure(%d)"><i class="fa fa-trash text-danger"
        aria-hidden="true"></i></a>""" % (_("Delete"),obj.custom_procedure.pk)

        return action

    class Meta:
        model = MyProcedure
        fields = ['name', 'custom_procedure','status','created_by', 'actions']

class MyProcedureFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.annotate(fullname=Concat('created_by__first_name', Value(' '), 'created_by__last_name'))
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(fullname__icontains=search) | Q(created_by__username__icontains=search) |
                Q(custom_procedure__title__icontains=search)).distinct()
        return queryset
    class Meta:
        model = MyProcedure
        fields = ['name','custom_procedure','status','created_by']

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
        org_pk=self.context['view'].kwargs.get('org_pk')
        lab_pk=self.context['view'].kwargs.get('lab_pk')
        procedure_kwargs = {
            'lab_pk': lab_pk,
            'org_pk': org_pk,
            'pk': obj.pk,
        }
        action = ""
        action += """<a href="%s" title="%s"><i class="fa fa-eye  fa-sm p-2"></i></a>"""%(reverse('academic:procedure_detail',kwargs=procedure_kwargs),_('View Steps'))
        action += """<a href="%s" title="%s"><i class="fa fa-plus text-success p-2"></i></a>"""%(reverse('academic:add_steps_wrapper',kwargs=procedure_kwargs),_('New Step'))
        action += """<a href="%s" title="%s"><i class="fa fa-edit  fa-sm p-2"></i></a>"""%(reverse('academic:procedure_update',kwargs=procedure_kwargs),_('Edit'))
        action += """<a delete_procedure(%d,%s) title="%s"><i class="fa fa-trash text-danger p-2"></i></a>"""%(obj.pk,obj.title,_('Remove'))

        return action

    class Meta:
        model = Procedure
        fields = ['title', 'description', 'actions']

class ProcedureFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)).distinct()
        return queryset
    class Meta:
        model = Procedure
        fields = ['title','description']

class ProcedureDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProcedureSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
