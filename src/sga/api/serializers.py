import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from sga.models import SGAComplement, PrudenceAdvice, DangerIndication, \
    BuilderInformation, \
    RecipientSize, Substance, SubstanceObservation, SecurityLeaf, ReviewSubstance, \
    DisplayLabel

logger = logging.getLogger('organilab')


class DangerIndicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return "(%s) %s" % (obj.code, obj.description)

    def get_id(self, obj):
        return obj.code

    class Meta:
        model = DangerIndication
        fields = ['id', 'name']


class PrudenceAdviceSerializer(serializers.ModelSerializer):
    def get_name(self, obj):
        return obj.code + ": " + obj.name

    class Meta:
        model = PrudenceAdvice
        fields = ['id', 'name']


class SGAComplementSerializer(serializers.ModelSerializer):
    prudence_advice = PrudenceAdviceSerializer(many=True)
    danger_indication = DangerIndicationSerializer(many=True)

    class Meta:
        model = SGAComplement
        fields = "__all__"


class BuilderInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuilderInformation
        fields = ['name', 'address', 'phone', 'commercial_information']


class RecipientSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipientSize
        fields = ['width', 'height']


class SubstanceSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    cas_id_number = serializers.CharField(source='cas_id')
    created_by = serializers.SerializerMethodField()

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
        context = {
            'org_pk': self.context['view'].organization.pk,
            'substance': obj
        }
        return render_to_string(
            'sga/substance/actions.html',
            request=self.context['request'],
            context=context
        )

    class Meta:
        model = Substance
        fields = ['pk', 'creation_date', 'created_by', 'comercial_name', 'agrochemical',
                  'uipa_name', 'cas_id_number', 'actions']


class SubstanceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=SubstanceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class SubstanceObservationSerializer(serializers.Serializer):
    pk = serializers.PrimaryKeyRelatedField(
        queryset=SubstanceObservation.objects.using(settings.READONLY_DATABASE))

    def validate_pk(self, value):
        attr = super().validate(value)
        organization_id = self.context.get("organization_id")
        if attr.substance.organization_id != organization_id:
            logger.debug(
                f'SubstanceObservationSerializer --> attr.substance.organization_id ({attr.substance.organization_id}) != organization_id ({organization_id})')
            raise serializers.ValidationError(
                _("Substance observation doesn't exists in this organization"))
        return attr


class SubstanceObservationDescriptionSerializer(SubstanceObservationSerializer):
    description = serializers.CharField()


class ReviewSubstanceSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    comercial_name = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        name = None
        if obj.created_by:
            name = obj.created_by.get_full_name()
            if not name:
                name = obj.created_by.username
        return name or ''

    def get_comercial_name(self, obj):
        if obj.substance:
            return obj.substance.comercial_name
        return ''

    def get_actions(self, obj):
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
            action += """ <a title='%s'  data-url='%s' class ='text-success btn_review'>
            <i class='icons fa fa-check'></i></a>""" % (_("Approve"), approve_url,)

        action += """<a class ='text-warning m-1' title='%s' href='%s'>
        <i class='icons fa fa-eye'></i></a>""" \
                  % (_("Detail"), detail_url,)
        leaf = SecurityLeaf.objects.filter(substance=obj.substance)
        if leaf.exists():
            action += """<a class='text-danger m-1' title='%s' href='%s'>
            <i class='icons fa fa-file-pdf-o'
             aria-hidden='true'></i></a>""" % (
                _("Generate PDF"), security_leaf_pdf_url,)
        return action

    class Meta:
        model = ReviewSubstance
        fields = ['creation_date', 'created_by', 'comercial_name', 'actions']


class ReviewSubstanceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReviewSubstanceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class DisplayLabelSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        name = None
        if obj.created_by:
            name = obj.created_by.get_full_name()
            if not name:
                name = obj.created_by.username
        return name or ''

    def get_actions(self, obj):
        obj_kwargs = {
            'org_pk': obj.substance.organization.pk
        }
        action = "actions"
        return action

    class Meta:
        model = DisplayLabel
        fields = ['creation_date', 'created_by', 'name', 'actions']


class DisplayLabelDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=DisplayLabelSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
