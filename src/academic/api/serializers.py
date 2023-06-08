from django.db.models import Q
from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from rest_framework import serializers
from sga.models import ReviewSubstance, SecurityLeaf


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