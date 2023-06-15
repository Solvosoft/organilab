import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from sga.models import SGAComplement, PrudenceAdvice, DangerIndication, \
    BuilderInformation, \
    RecipientSize, Substance, SubstanceObservation

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
            if not obj.creator:
                return _("No user found")

            name = obj.creator.get_full_name()
            if not name:
                name = obj.creator.username
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
