from django.contrib import admin

from sga.models import (
    TemplateSGA,
    DisplayLabel,
    SecurityLeaf,
    SGAComplement,
    ReviewSubstance,
    Pictogram,
    DangerSubstanceCategory,
    DangerSubstance,
    SDSTraceability,
)
from django.utils.translation import gettext_lazy as _
from .models import (
    DangerIndication,
    BuilderInformation,
    Substance,
    Label,
    WarningClass,
    Component,
    WarningWord,
    PrudenceAdvice,
    RecipientSize,
    SubstanceCharacteristics,
)


class AdminDangerIndication(admin.ModelAdmin):
    # form = DangerIndicationForm
    filter_horizontal = ["warning_class", "warning_category", "prudence_advice"]

    def get_form(self, *args, **kwargs):
        form = super(AdminDangerIndication, self).get_form(*args, **kwargs)

        class MyForm(form):
            def __init__(self, *args_myform, **kwargs_myform):
                super(MyForm, self).__init__(*args_myform, **kwargs_myform)
                self.fields["warning_class"].queryset = WarningClass.objects.filter(
                    danger_type="class"
                )
                self.fields["warning_category"].queryset = WarningClass.objects.filter(
                    danger_type="category"
                )

        return MyForm


class AdminSustance(admin.ModelAdmin):
    filter_horizontal = ["components_sga", "danger_indications"]


class SustanceCharacteristicsAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "object_related__name",
        "cas_id_number",
    ]
    list_filter = ["object_related__name", "cas_id_number", "h_code"]
    search_fields = [
        "object_related__name",
        "object_related__code",
        "cas_id_number",
    ]


admin.site.register(WarningClass)
admin.site.register(
    [BuilderInformation, RecipientSize, PrudenceAdvice, Component, WarningWord]
)
admin.site.register(DangerIndication, AdminDangerIndication)
admin.site.register(Substance, AdminSustance)
admin.site.register(Label)
admin.site.register(TemplateSGA)
admin.site.register(DisplayLabel)
admin.site.register(SecurityLeaf)
admin.site.register(SGAComplement)
admin.site.register(ReviewSubstance)
admin.site.register(Pictogram)
admin.site.register(DangerSubstanceCategory)
admin.site.register(DangerSubstance)
admin.site.register(SubstanceCharacteristics, SustanceCharacteristicsAdmin)


class SDSTraceabilityAdmin(admin.ModelAdmin):
    list_display = [
        "get_object_name",
        "source",
        "revision_date",
        "creation_date",
    ]
    list_filter = ["source"]
    search_fields = ["sga_substance_characteristics__cas_id_number"]

    def get_object_name(self, obj):
        characteristics = obj.sga_substance_characteristics
        if characteristics and characteristics.object_related:
            return characteristics.object_related.name
        return "-"

    get_object_name.short_description = _("Object name")


admin.site.register(SDSTraceability, SDSTraceabilityAdmin)
