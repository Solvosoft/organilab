from django.db.models import Q
from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet, CharFilter
from rest_framework import serializers
from sga.models import ReviewSubstance, SecurityLeaf
from academic.models import CommentProcedureStep
from django.utils import formats
from django_filters import DateTimeFromToRangeFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget


class ProcedureStepCommentFilterSet(FilterSet):
    creator_at = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(attrs={'placeholder': formats.get_format('DATETIME_INPUT_FORMATS')[0]}))
    creator = CharFilter(field_name='creator', method='filter_user')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(creator__first_name__icontains=value) | Q(creator__last_name__icontains=value) | Q(
            creator__username__icontains=value))

    class Meta:
        model = CommentProcedureStep
        fields = ['creator', 'creator_at', 'comment']


class ProcedureStepCommentSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField(required=False)
    creator_at = serializers.DateTimeField(required=False, format=formats.get_format('DATETIME_INPUT_FORMATS')[0])

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
            queryset = queryset.annotate(fullname=Concat('substance__creator__first_name', Value(' '), 'substance__creator__last_name'))
            queryset = queryset.filter(Q(fullname__icontains=name) | Q(substance__creator__username__icontains=name)).distinct()
        return queryset


class ReviewSubstanceSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    comercial_name = serializers.SerializerMethodField()

    def get_creator(self, obj):
        if obj.substance:
            name = obj.substance.creator.get_full_name()
            if not name:
                name = obj.substance.creator.username
            return name
        return ''

    def get_comercial_name(self, obj):
        if obj.substance:
            return obj.substance.comercial_name
        return ''

    def get_action(self, obj):
        obj_kwargs = {
            'organilabcontext': 'academic',
            'org_pk': obj.substance.organization.pk
        }
        obj_kwargs.update({'pk': obj.substance.pk})
        detail_url = reverse('academic:detail_substance', kwargs=obj_kwargs)
        security_leaf_pdf_url = reverse('academic:security_leaf_pdf', kwargs={'org_pk': obj.substance.organization.pk,
                                                                     'substance': obj.substance.pk})
        action = ""

        if not obj.is_approved:
            obj_kwargs.update({'pk': obj.pk})
            approve_url = reverse('academic:accept_substance', kwargs=obj_kwargs)
            action += """ <button title='%s' type ='button' data-url='%s' class ='btn btn-info text-white btn_review'>
            <i class='icons fa fa-check'></i></button>""" % (_("Approve"), approve_url,)

        action += """<a class ='btn btn-warning' title='%s' href='%s'><i class='icons fa fa-eye'></i></a>""" \
                  % (_("Detail"), detail_url,)
        leaf = SecurityLeaf.objects.filter(substance=obj.substance)
        if leaf.exists():
            action += """<a class='btn  btn-md  btn-danger' title='%s' href='%s'><i class='icons fa fa-file-pdf-o'
             aria-hidden='true'></i></a>""" % (_("Generate PDF"), security_leaf_pdf_url,)
        return action

    class Meta:
        model = ReviewSubstance
        fields = ['creator', 'comercial_name', 'action']


class ReviewSubstanceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReviewSubstanceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)