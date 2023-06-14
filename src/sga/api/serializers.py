from rest_framework import serializers

from sga.models import SGAComplement, PrudenceAdvice, DangerIndication, BuilderInformation, \
    PersonalTemplateSGA, RecipientSize, Substance


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

    class Meta:
        model = Substance
        fields = ['comercial_name', 'uipa_name', 'cas_id_number']


class SubstanceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=SubstanceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)