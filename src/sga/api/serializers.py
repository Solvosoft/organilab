import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from sga.models import SGAComplement, PrudenceAdvice, DangerIndication, \
    BuilderInformation, \
    RecipientSize, Substance, SubstanceObservation, SecurityLeaf, ReviewSubstance, \
    DisplayLabel, WarningWord, HCodeCategory

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
    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    prudence_advice_help = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_code(self, obj):
        if obj.code:
            return obj.code
        return ''

    def get_name(self, obj):
        if obj.name:
            return obj.name
        return ''

    def get_prudence_advice_help(self, obj):
        if obj.prudence_advice_help:
            return obj.prudence_advice_help

    def get_actions(self, obj):
        action = ""

        action += """<a title='%s' class="pe-2" onclick="edit_prudence_advice('%d')">
        <i class="fa fa-edit text-warning" aria-hidden="true"></i>
        </a>""" % (_('Edit'), obj.pk)

        action += """<a title='%s' class="pe-2" onclick="delete_prudence_advice('%d')">
        <i class="fa fa-close text-danger" aria-hidden="true"></i>
        </a>""" % (_("Delete"), obj.pk)

        return action


    class Meta:
        model = PrudenceAdvice
        fields = ['id', 'code', 'name', 'prudence_advice_help', 'actions']


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


class WarningWordSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    weigth = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.name:
            return obj.name
        return ''

    def get_weigth(self, obj):
        if obj.weigth:
            return obj.weigth
        return 0

    def get_actions(self, obj):
        org_pk = self.context['view'].kwargs.get('org_pk')
        action = ""

        action += """<a title='%s' class="pe-2" onclick="edit_warning_word('%d')">
        <i class="fa fa-edit text-warning" aria-hidden="true"></i>
        </a>""" % (_('Edit'), obj.pk)

        action += """<a title='%s' class="pe-2" onclick="delete_warning_word(%d)">
        <i class="fa fa-close text-danger" aria-hidden="true"></i>
        </a>""" % (_("Delete"), obj.pk)

        return action

    class Meta:
        model = WarningWord
        fields = ['pk', 'name', 'weigth', 'actions']


class WarningWordDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=WarningWordSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class DangerIndicationSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    warning_words = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_code(self, obj):
        if obj.code:
            return obj.code
        return ''

    def get_description(self, obj):
        if obj.description:
            return obj.description
        return ''

    def get_warning_words(self, obj):
        if obj.warning_words:
            return obj.warning_words.name
        return ''

    def get_actions(self, obj):
        org_pk = self.context['view'].kwargs.get('org_pk')
        kwargs = {
            'org_pk': org_pk,
            'pk': obj.pk
        }
        edit_url = reverse('sga:update_danger_indication', kwargs=kwargs)
        action = ""
        action += """<a title='%s' class="pe-2" href='%s'>
                <i class="fa fa-edit text-warning" aria-hidden="true"></i>
                </a>""" % (_('Edit'), edit_url)

        action += """<a title='%s' class="pe-2"
                onclick="delete_danger_indication('%s')">
                <i class="fa fa-close text-danger" aria-hidden="true"></i>
                </a>""" % (_("Delete"), obj.pk)

        return action

    class Meta:
        model = DangerIndication
        fields = ['pk', 'code', 'description', 'warning_words', 'actions']


class DangerIndicationDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=DangerIndicationSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class PrudenceAdviceDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=PrudenceAdviceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

CHOICES = (
        ('mm', _('Milimeters')),
        ('cm', _('Centimeters')),
        ('inch', _('inch')),
    )
class RecipientSizeDataSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    height_unit = serializers.SerializerMethodField()
    width = serializers.SerializerMethodField()
    width_unit = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.name:
            return obj.name
        return ''

    def get_height(self, obj):
        if obj.height:
            return obj.height
        return 0

    def get_height_unit(self, obj):
        if obj.height_unit:
            return obj.get_height_unit_display()
        return ''

    def get_width_unit(self, obj):
        if obj.width_unit:
            return obj.get_width_unit_display()
        return ''

    def get_width(self, obj):
        if obj.width:
            return obj.width
        return 0

    def get_actions(self, obj):
        action = ""

        action += """<a title='%s' class="text-center pe-2" onclick="edit_recipient_size('%d')">
        <i class="fa fa-edit" aria-hidden="true"></i>
        </a>""" % (_('Edit'), obj.pk)

        action += """<a title='%s' class=" text-center pe-2" onclick="delete_recipient_size('%d')">
        <i class="fa fa-trash text-danger" aria-hidden="true"></i>
        </a>""" % (_("Delete"), obj.pk)

        return action


    class Meta:
        model = RecipientSize
        fields = ['name', 'height', 'height_unit', 'width', 'width_unit', 'actions']


class RecipientSizeDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=RecipientSizeDataSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class RecipientSizeSerializer(serializers.ModelSerializer):
    height = serializers.FloatField(min_value=0,allow_null=False, required=True)
    width = serializers.FloatField(min_value=0, allow_null=False, required=True)
    height_unit = serializers.ChoiceField(choices=CHOICES, allow_null=False,
                                        allow_blank=False)
    width_unit = serializers.ChoiceField(choices=CHOICES, allow_null=False,
                                       allow_blank=False)
    class Meta:
        model = RecipientSize
        fields = ['name', 'height', 'height_unit', 'width', 'width_unit']


class RecipientSizeDeleteSerializer(serializers.Serializer):
    pk = serializers.PrimaryKeyRelatedField(queryset=RecipientSize.objects.using(settings.READONLY_DATABASE))


class DangerCategoryActionsSerializer(serializers.ModelSerializer):
    h_code = serializers.PrimaryKeyRelatedField(
        many=True,
        required=True,
        queryset=DangerIndication.objects.using(settings.READONLY_DATABASE),
        allow_null=False,
        allow_empty=False,
    )
    danger_category = serializers.CharField(max_length=50, required=True)


    class Meta:
        model = HCodeCategory
        fields = '__all__'

class DangerCategorySerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    h_code = GTS2SerializerBase(many=True)
    danger_category = serializers.SerializerMethodField()

    def get_danger_category(self, obj):
        return obj.get_danger_category_display()

    def get_actions(self, obj):
        user = self.context["request"].user
        add_perm = True if user.has_perm('risk_management.add_hcodecategory') else False
        delele_perm = True if user.has_perm('risk_management.delete_hcodecategory') else False
        view_perm = True if user.has_perm('risk_management.view_hcodecategory') else False
        update_perm = True if user.has_perm('risk_management.change_hcodecategory') else False

        return {
            "list": view_perm,
            "create": add_perm,
            "update": update_perm,
            "destroy": delele_perm
        }


    class Meta:
        model = HCodeCategory
        fields = "__all__"


class DangerCategoryDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=DangerCategorySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

