from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from tree_queries.models import TreeNode

from laboratory import catalog
from laboratory.models_utils import upload_files
from presentation.models import AbstractOrganizationRef


class WarningClass(TreeNode):
    TYPE = (
        ("typeofdanger", _("Type of danger")),
        ("class", _("Danger class")),
        ("category", _("Danger Category"))
    )
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    danger_type = models.CharField(
        max_length=25, default="category", choices=TYPE,
        verbose_name=_("Danger type"))

    position = models.IntegerField(default=0)

    def __str__(self):
        name = self.name

        if len(name) < 3 and self.parent:
            name = self.parent.name + " > " + name
        elif WarningClass.objects.filter(name=self.name).count() > 1:
            name = self.parent.name + " > " + name

        """
        if self.danger_type == 'class':
            name = "+ "+name
        elif self.danger_type == 'category':
            name = "# "+name
        """
        return name

    class Meta:
        verbose_name = _('Warning Class')
        verbose_name_plural = _('Warning Classes')
        ordering = ["position"]


# Pictograma de precaución


class WarningWord(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    weigth = models.SmallIntegerField(default=0, verbose_name=_("Weigth"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Warning Word')
        verbose_name_plural = _('Warning Words')


# palabras de advertencia


class PrudenceAdvice(models.Model):
    code = models.CharField(max_length=150,
                            verbose_name=_("Code"))
    name = models.CharField(max_length=500, verbose_name=_("Name"))
    prudence_advice_help = models.TextField(
        null=True, blank=True,
        verbose_name=_("Help for prudence advice"))

    def __str__(self):
        return self.code + ": " + self.name

    class Meta:
        verbose_name = _('Prudence Advice')
        verbose_name_plural = _('Prudence Advices')


class DangerIndication(models.Model):
    code = models.CharField(max_length=150, primary_key=True,
                            verbose_name=_("Code"))
    description = models.TextField(verbose_name=_("Description"))
    warning_words = models.ForeignKey(WarningWord, on_delete=models.DO_NOTHING,
                                      verbose_name=_("Warning words"))
    warning_class = models.ManyToManyField(WarningClass,
                                           verbose_name=_("Warning class"))

    warning_category = models.ManyToManyField(
        WarningClass,
        related_name='warningcategory',
        verbose_name=_("Warning category"))
    prudence_advice = models.ManyToManyField(
        PrudenceAdvice, verbose_name=_("Prudence advice"))

    def __str__(self):
        return "(%s) %s" % (self.code, self.description)

    class Meta:
        verbose_name = _('Danger Indication')
        verbose_name_plural = _('Indication of Danger')


class DangerPrudence(models.Model):
    danger_indication = models.ManyToManyField(
        DangerIndication, verbose_name=_("Danger indication"))
    prudence_advice = models.ManyToManyField(
        PrudenceAdvice, verbose_name=_("Prudence advice"))


class Component(models.Model):
    name = models.CharField(max_length=250, verbose_name=_("Name"))
    cas_number = models.CharField(max_length=150, verbose_name=_("CAS number"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Component')
        verbose_name_plural = _('Components')


class Substance(AbstractOrganizationRef):
    DRAFT = 0
    UNDER_REVIEW = 1
    APPROVED = 2
    STATUS_CHOICE = (
        (DRAFT, _("Draft")),
        (UNDER_REVIEW, _("Under Review")),
        (APPROVED, _("Approved")),
    )

    status = models.IntegerField(choices=STATUS_CHOICE, default=DRAFT)
    comercial_name = models.CharField(max_length=250,
                                      verbose_name=_("Comercial name"))
    uipa_name = models.CharField(max_length=250, default="",
                                 verbose_name=_("UIPA name"))
    brand = models.CharField(max_length=50, default="", verbose_name=_("Brand"))
    components_sga = models.ManyToManyField(
        "self", verbose_name=_("Components"))
    danger_indications = models.ManyToManyField(
        DangerIndication,
        verbose_name=_("Danger indications"))
    synonymous = models.TextField(verbose_name=_("Synonymous"), null=True, blank=True)
    agrochemical = models.BooleanField(default=False, verbose_name=_("Agrochemical"))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))

    @property
    def warning_word(self):
        last_word = ""
        last_num = -1
        for dindic in self.danger_indications.all():
            if dindic.warning_words.weigth > last_num:
                last_num = dindic.warning_words.weigth
                last_word = dindic.warning_words.name
        return last_word

    def __str__(self):
        return self.comercial_name

    class Meta:
        verbose_name = _('Substance')
        verbose_name_plural = _('Substances')


class SubstanceCharacteristics(models.Model):
    substance = models.OneToOneField(Substance, on_delete=models.CASCADE, null=True)
    iarc = catalog.GTForeignKey("laboratory.Catalog", related_name="gt_iarcrel_sga",
                                on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IARC")
    imdg = catalog.GTForeignKey("laboratory.Catalog", related_name="gt_imdg_sga",
                                on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IDMG")
    white_organ = catalog.GTManyToManyField("laboratory.Catalog",
                                            related_name="gt_white_organ_sga",
                                            key_name="key",
                                            key_value="white_organ", blank=True,
                                            verbose_name=_('White organ'))
    bioaccumulable = models.BooleanField(null=True, verbose_name=_('Bioaccumulable'))
    molecular_formula = models.CharField(_('Molecular formula'), max_length=255,
                                         null=True, blank=True)
    cas_id_number = models.CharField(
        _('Cas ID Number'), max_length=255, null=True, blank=True)
    security_sheet = models.FileField(
        _('Security sheet'), upload_to=upload_files, null=True, blank=True)
    is_precursor = models.BooleanField(_('Is precursor'), default=False)
    precursor_type = catalog.GTForeignKey("laboratory.Catalog",
                                          related_name="gt_precursor_sga",
                                          on_delete=models.SET_NULL,
                                          null=True, blank=True, key_name="key",
                                          key_value="Precursor")

    h_code = models.ManyToManyField(DangerIndication, related_name="sga_h_code",
                                    verbose_name=_("Danger Indication"), blank=True)
    valid_molecular_formula = models.BooleanField(default=False)
    ue_code = catalog.GTManyToManyField("laboratory.Catalog", related_name="gt_ue_sga",
                                        key_name="key",
                                        key_value="ue_code", blank=True,
                                        verbose_name=_('UE codes'))
    nfpa = catalog.GTManyToManyField("laboratory.Catalog", related_name="gt_nfpa_sga",
                                     key_name="key",
                                     key_value="nfpa", blank=True,
                                     verbose_name=_('NFPA codes'))
    storage_class = catalog.GTManyToManyField("laboratory.Catalog",
                                              related_name="gt_storage_class_sga",
                                              key_name="key",
                                              key_value="storage_class", blank=True,
                                              verbose_name=_('Storage class'))
    seveso_list = models.BooleanField(verbose_name=_('Is Seveso list III?'),
                                      default=False)
    number_index = models.CharField(max_length=40, verbose_name=_("Number Index"),
                                    blank=True, null=True)
    number_ce = models.CharField(max_length=40, verbose_name=_("Number CE"), blank=True,
                                 null=True)
    molecular_weight = models.CharField(max_length=30,
                                        verbose_name=_("Molecular Weight"), null=True,
                                        blank=True)
    concentration = models.CharField(max_length=30, verbose_name=_("Concentration"),
                                     null=True, blank=True)

    class Meta:
        verbose_name = _('Substance characteristic SGA')
        verbose_name_plural = _('Substance characteristics SGA')


# build information


class BuilderInformation(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    phone = models.TextField(max_length=15, verbose_name=_("Phone"))
    address = models.TextField(max_length=100, verbose_name=_("Address"))
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.DO_NOTHING,
                             null=True, related_name='user_bi')
    commercial_information = models.TextField(
        null=True, blank=True,
        verbose_name=_("Commercial Information"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Builder Information')
        verbose_name_plural = _('Information of Builders')


# labels


class RecipientSize(models.Model):
    CHOICES = (
        ('mm', _('Milimeters')),
        ('cm', _('Centimeters')),
        ('inch', _('inch')),
    )
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    height = models.FloatField(default=10, verbose_name=_("Height"))
    height_unit = models.CharField(max_length=5, default="cm",
                                   verbose_name=_("Height Unit"),
                                   choices=CHOICES)
    width = models.FloatField(default=10, verbose_name=_("Width"))
    width_unit = models.CharField(max_length=5, default="cm",
                                  verbose_name=_("Width Unit"),
                                  choices=CHOICES)

    def __str__(self):
        return '{0} | height={1} {2}, width={3} {4}'.format(self.name, self.height,
                                                            self.height_unit,
                                                            self.width,
                                                            self.width_unit)

    class Meta:
        verbose_name = _('Recipient Size')
        verbose_name_plural = _('Size of recipients')


class Label(models.Model):
    substance = models.ForeignKey(Substance, verbose_name=_("Substance"),
                                  on_delete=models.CASCADE, null=True)
    builderInformation = models.ForeignKey(
        BuilderInformation, verbose_name=_("Builder Information"),
        on_delete=models.CASCADE, null=True)

    community_share = models.BooleanField(default=False, blank=True,
                                          verbose_name=_("Share with community"))

    def __str__(self):
        return str(self.substance)

    class Meta:
        verbose_name = _('Label')
        verbose_name_plural = _('Labels')


class TemplateSGA(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    recipient_size = models.ForeignKey(RecipientSize, verbose_name=_("Recipient Size"),
                                       on_delete=models.CASCADE)
    json_representation = models.TextField()
    community_share = models.BooleanField(default=True,
                                          verbose_name=_("Share with community"))
    preview = models.TextField(help_text="B64 preview image", null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} {self.recipient_size.name} - {self.recipient_size.height}{self.recipient_size.height_unit} x {self.recipient_size.width}{self.recipient_size.width_unit}'

    class Meta:
        verbose_name = _('Template SGA')
        verbose_name_plural = _('Templates SGA')


class DisplayLabel(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    json_representation = models.TextField()
    template = models.ForeignKey(TemplateSGA, verbose_name=_("Template SGA"),
                                 on_delete=models.DO_NOTHING)
    recipient_size = models.ForeignKey(RecipientSize, null=True,
                                       verbose_name=_("Recipient size"),
                                       on_delete=models.SET_NULL)
    preview = models.TextField(help_text="B64 preview image", null=True)
    label_in_png = models.TextField(help_text="B64 image using the recipient size", null=True)
    label = models.ForeignKey(Label, verbose_name=_("Label"), on_delete=models.CASCADE)
    barcode = models.CharField(max_length=150, verbose_name=_("Barcode"), null=True,
                               blank=True)
    logo = models.FileField(_('Logo'), upload_to=upload_files, null=True, blank=True)

    def __str__(self):
        recipient = RecipientSize.objects.get(pk=self.template.recipient_size.pk)
        return self.name + " Height {0}{1} x Width {2}{3}".format(recipient.height,
                                                                  recipient.height_unit,
                                                                  recipient.width,
                                                                  recipient.width_unit)

    class Meta:
        verbose_name = _('Personal Template SGA')
        verbose_name_plural = _('Personal Templates SGA')


class SGAComplement(models.Model):
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, null=True)
    danger_indication = models.ManyToManyField(
        DangerIndication, verbose_name=_("Danger indication"))
    prudence_advice = models.ManyToManyField(
        PrudenceAdvice, verbose_name=_("Prudence advice"))
    other_dangers = models.TextField(null=True, blank=True,
                                     verbose_name=_("Other Dangers"))
    warningword = models.ForeignKey(WarningWord, null=True, blank=True,
                                    on_delete=models.DO_NOTHING,
                                    verbose_name=_("WarningWord"))


class Provider(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True,
                            verbose_name=_("Name"))
    country = models.CharField(max_length=30, null=True, blank=True,
                               verbose_name=_("Country"))
    direction = models.TextField(blank=True, null=True, verbose_name=_("Direction"))
    telephone_number = models.CharField(max_length=30, null=True, blank=True,
                                        verbose_name=_("Telephone number"))
    fax = models.CharField(max_length=30, null=True, blank=True)
    email = models.CharField(max_length=100, verbose_name=_("Email"), null=True,
                             blank=True)
    provider = models.ForeignKey("self", on_delete=models.DO_NOTHING, null=True,
                                 blank=True, verbose_name=_("Provider"),
                                 related_name="providersga")
    emergency_phone = models.CharField(max_length=30, null=True, blank=True,
                                       verbose_name=_("Emergency number"))

    def __str__(self):
        return self.name


class SecurityLeaf(models.Model):
    """Identificacion de sustancias"""
    register_number = models.CharField(max_length=100, null=True, blank=True,
                                       verbose_name=_("No. Registro"))
    reach_number = models.CharField(max_length=100, null=True, blank=True,
                                    verbose_name=_("REACH No."))
    identified_uses = models.TextField(null=True, blank=True,
                                       verbose_name=_("Identified uses"))
    reference = models.CharField(max_length=100, null=True, blank=True,
                                 verbose_name=_("Reference"))
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(Provider, on_delete=models.DO_NOTHING, null=True,
                                 verbose_name=_('Provider'))
    regulation_classification = models.TextField(null=True, blank=True, verbose_name=_(
        "Classification according to Regulation (CE) 1272/2008"))
    directives_classification = models.TextField(null=True, blank=True, verbose_name=_(
        "Classification according to EU Directives 67/548/CEE or 1999/45/CE"))
    """Primeros Auxilios"""
    general = models.TextField(null=True, blank=True,
                               verbose_name=_("General recommendations"))
    inhalation = models.TextField(null=True, blank=True, verbose_name=_("If inhaled"))
    skin_contact = models.TextField(null=True, blank=True,
                                    verbose_name=_("In case of skin contact"))
    eye_contact = models.TextField(null=True, blank=True,
                                   verbose_name=_("In case of contact with eyes"))
    ingestion = models.TextField(null=True, blank=True,
                                 verbose_name=_("if it is swallowed"))
    symptoms = models.TextField(null=True, blank=True, verbose_name=_(
        "Most important symptoms and effects, both acute and delayed"))
    other_causes = models.TextField(null=True, blank=True,
                                    verbose_name=_("Other Causes"))
    medical_indication = models.TextField(null=True, blank=True, verbose_name=_(
        "Indication of any medical attention and special treatment that should be provided immediately"))

    """Medidas de lucha contra incendios"""
    appropriate = models.TextField(null=True, blank=True,
                                   verbose_name=_("Suitable extinguishing media"))
    no_appropriate = models.TextField(null=True, blank=True,
                                      verbose_name=_("Unsuitable extinguishing media"))
    specific_dangers = models.TextField(null=True, blank=True, verbose_name=_(
        "Specific hazards arising from the substance or mixture"))
    combustion_products = models.TextField(null=True, blank=True, verbose_name=_(
        "Hazardous Combustion Products"))
    recomendations = models.TextField(null=True, blank=True, verbose_name=_(
        "Recommendations for firefighters"))
    other_info = models.TextField(null=True, blank=True,
                                  verbose_name="Other Information")

    """Medidas en caso de vertido accidental"""
    personal_caution = models.TextField(null=True, blank=True, verbose_name=_(
        "Personnel who are not part of the emergency services"))
    environmental_caution = models.TextField(null=True, blank=True, verbose_name=_(
        "Environmental relative precautions"))
    methods_material_contention = models.TextField(
        null=True, blank=True,
        verbose_name=_("Methods and material for containment and cleaning up"))
    references_sections = models.TextField(null=True, blank=True, verbose_name=_(
        "Reference to other sections"))
    """"Manipulación_Almacenamiento"""
    safe_handling = models.TextField(null=True, blank=True,
                                     verbose_name=_("Precautions for safe handling"))
    storage_conditions = models.TextField(null=True, blank=True, verbose_name=_(
        "Conditions for safe storage, including possible incompatibilities"))
    specific_end_uses = models.TextField(null=True, blank=True,
                                         verbose_name=_("Specific end uses"))
    """Controles de exposición/protección individual"""
    vla_ed_pp = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-ED[ppm]")
    vla_ed_mg = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-ED[mgm3]")
    vla_ec_pp = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-EC[ppm]")
    vla_ec_mg = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-EC[mgm3]")
    vla_vm_pp = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-VM[ppm]")
    vla_vm_mg = models.CharField(max_length=20, null=True, blank=True,
                                 verbose_name="VLA-VM[mgm]")
    approppiate_control = models.TextField(null=True, blank=True, verbose_name=_(
        "Appropriate technical controls"))
    eye_face_protection = models.TextField(null=True, blank=True,
                                           verbose_name=_("Eye/face protection"))
    skin_protection = models.TextField(null=True, blank=True,
                                       verbose_name=_("Skin protection"))
    corporal_protection = models.TextField(null=True, blank=True,
                                           verbose_name=_("Corporal protection"))
    breath_protection = models.TextField(null=True, blank=True,
                                         verbose_name=_("Breath protection"))
    environmental_exposition = models.TextField(null=True, blank=True, verbose_name=_(
        "Environmental exposure control"))
    annotation = models.TextField(null=True, blank=True, verbose_name=_("Annotation"))
    font = models.TextField(null=True, blank=True, verbose_name=_("Font"))
    """Propiedades físicas y químicas"""
    aspect = models.TextField(null=True, blank=True, verbose_name=_("Aspect"))
    smell = models.TextField(null=True, blank=True, verbose_name=_("Smell"))
    olfactory_threshold = models.TextField(null=True, blank=True,
                                           verbose_name=_("Olfactory threshold"))
    pH = models.TextField(null=True, blank=True, verbose_name=_("pH"))
    melting_point = models.TextField(null=True, blank=True,
                                     verbose_name=_("Melting point/ point of freezing"))
    starting_point_boiling = models.TextField(null=True, blank=True, verbose_name=_(
        "Starting point of boiling and range boiling"))
    flashpoint = models.TextField(null=True, blank=True, verbose_name=_("Flashpoint"))
    evaporation_rate = models.TextField(null=True, blank=True,
                                        verbose_name=_("Evaporation rate"))
    inflammability_solid_gas = models.TextField(null=True, blank=True, verbose_name=_(
        "Flammability (solid,gas)"))
    Inflammability_top_bottom = models.TextField(null=True, blank=True, verbose_name=_(
        "Inflammability top/bottom or explosive limits"))
    vapor_pressure = models.TextField(null=True, blank=True,
                                      verbose_name=_("Vapor pressure"))
    vapor_density = models.TextField(null=True, blank=True,
                                     verbose_name=_("Vapor density"))
    relative_density = models.TextField(null=True, blank=True,
                                        verbose_name=_("Relative density"))
    water_solubility = models.TextField(null=True, blank=True,
                                        verbose_name=_("Water solubility"))
    partition_coefficient = models.TextField(null=True, blank=True, verbose_name=_(
        "Partition coefficient n-octanol/water"))
    auto_temperature_inflammation = models.TextField(null=True, blank=True,
                                                     verbose_name=_(
                                                         "Auto-temperature inflammation"))
    temperature_decomposition = models.TextField(null=True, blank=True, verbose_name=_(
        "Temperature of decomposition"))
    viscosity = models.TextField(null=True, blank=True, verbose_name=_("Viscosity"))
    explosive_properties = models.TextField(null=True, blank=True,
                                            verbose_name=_("Explosive properties"))
    properties_oxidising = models.TextField(null=True, blank=True,
                                            verbose_name=_("Properties oxidising"))
    other_security_information = models.TextField(null=True, blank=True, verbose_name=_(
        "Other security information"))
    """EstabilidadReactividad"""
    reactivity = models.TextField(null=True, blank=True, verbose_name=_("Reactivity"))
    chemical_stability = models.TextField(null=True, blank=True,
                                          verbose_name=_("Chemical stability"))
    dangerous_reactions = models.TextField(null=True, blank=True, verbose_name=_(
        "Possibility of hazardous reactions"))
    conditions_avoid = models.TextField(null=True, blank=True,
                                        verbose_name=_("Conditions to avoid"))
    incompatible_materials = models.TextField(null=True, blank=True,
                                              verbose_name=_("Incompatible materials"))
    dangerous_decomposition_products = models.TextField(
        null=True, blank=True,
        verbose_name=_("Hazardous decomposition products"))

    """InformaciónToxicologica"""
    acute_toxicity = models.TextField(null=True, blank=True,
                                      verbose_name=_("Acute toxicity"))
    skin_irritation = models.TextField(null=True, blank=True,
                                       verbose_name=_("Skin corrosion or irritation"))
    eye_irritation = models.TextField(null=True, blank=True, verbose_name=_(
        "Serious eye damage or irritation"))
    respiratory_sensitization = models.TextField(null=True, blank=True, verbose_name=_(
        "Respiratory or skin sensitization"))
    germ_mutagenicity = models.TextField(null=True, blank=True,
                                         verbose_name=_("Germ cell mutagenicity"))
    carcinogenicity = models.TextField(null=True, blank=True,
                                       verbose_name=_("Carcinogenicity"))
    reproductive_toxicity = models.TextField(null=True, blank=True,
                                             verbose_name=_("Reproductive toxicity"))
    unique_exhibition = models.TextField(null=True, blank=True, verbose_name=_(
        "Specific target organ toxicity - single exposure"))
    repeated_exposures = models.TextField(null=True, blank=True, verbose_name=_(
        "Specific target organ toxicity - repeated exposure"))
    aspiration_hazard = models.TextField(null=True, blank=True,
                                         verbose_name=_("Aspiration hazard"))
    additional_information = models.TextField(null=True, blank=True,
                                              verbose_name=_("Additional Information"))
    """InformaciónEcológica"""
    toxicity = models.TextField(null=True, blank=True, verbose_name=_("Toxicity"))
    Persistence_degradability = models.TextField(null=True, blank=True, verbose_name=_(
        "Persistence and degradability"))
    bioaccumulative_potential = models.TextField(null=True, blank=True, verbose_name=_(
        "Bioaccumulative potential"))
    soil_mobility = models.TextField(null=True, blank=True,
                                     verbose_name=_("Soil mobility"))
    assessment_result = models.TextField(null=True, blank=True, verbose_name=_(
        "Results of PBT and vPvB assessment"))
    other_adverse_effects = models.TextField(null=True, blank=True,
                                             verbose_name=_("Other adverse effects"))

    """ConsideracionesRelativasEliminación"""
    product = models.TextField(null=True, blank=True, verbose_name=_("Product"))
    contaminated_packaging = models.TextField(null=True, blank=True,
                                              verbose_name=_("Contaminated packaging"))
    """InformaciónTransporte"""
    onu_number = models.TextField(null=True, blank=True, verbose_name=_("ONU Number"))
    proper_shipping_name = models.TextField(null=True, blank=True, verbose_name=_(
        "United Nations proper shipping name"))
    transport_hazard_class = models.TextField(null=True, blank=True,
                                              verbose_name=_("Transport hazard class"))
    packaging_group = models.TextField(null=True, blank=True,
                                       verbose_name=_("Packaging group"))
    environmental_hazards = models.TextField(null=True, blank=True,
                                             verbose_name=_("Environmental hazards"))
    special_precautions = models.TextField(null=True, blank=True, verbose_name=_(
        "Special precautions for users"))
    """InformaciónReglamentaria"""
    regulatory_information = models.TextField(null=True, blank=True,
                                              verbose_name=_("Regulatory information"))
    regulations_legislation = models.TextField(null=True, blank=True, verbose_name=_(
        "Regulations and legislation on safety, health and the " +
        "environment specific to the substance or mixture"))
    chemical_safety_assessment = models.TextField(null=True, blank=True, verbose_name=_(
        "Chemical Safety Assessment"))
    """OtraInformacion"""
    full_text_statements = models.TextField(null=True, blank=True, verbose_name=_(
        "Full text of the H-Statements referred to in sections 2 and 3."))
    full_text_phrases = models.TextField(null=True, blank=True, verbose_name=_(
        "The full text of the R-phrases referred to in points 2 and 3"))
    other_data_text = models.TextField(null=True, blank=True,
                                       verbose_name=_("Otro datos"))
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewSubstance(AbstractOrganizationRef):
    substance = models.ForeignKey(Substance, null=True, blank=True,
                                  on_delete=models.CASCADE, verbose_name=_('Substance'))
    note = models.IntegerField(null=True, blank=True, verbose_name=_('Note'))
    is_approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Review Substance")
        verbose_name_plural = _("Review Substance")

    def __str__(self):
        return f'{self.substance.created_by}- ${self.note}'


class SubstanceObservation(models.Model):
    substance = models.ForeignKey("sga.Substance", on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_('Description'))
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True,
                                verbose_name=_('Creator'))
    create_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date'))

    class Meta:
        verbose_name = _('Observation')
        verbose_name_plural = _('Observations')

    def __str__(self):
        return f'{self.substance} {self.created_by}'


class HCodeCategory(models.Model):
    HCATEGORY = (
        ('physical', _('Physical')),
        ('health', _('Health')),
        ('environment', _('Environment')),
    )
    name = models.CharField(max_length=50,  null=True, blank=True,
                            verbose_name=_('Name'))
    danger_category = models.CharField(max_length=30, choices=HCATEGORY, null=False,
                                       blank=False, verbose_name=_('Danger Category'))
    h_code = models.ManyToManyField(DangerIndication, related_name='category_h_code',
                                    verbose_name=_('H Codes'))
    threshold = models.FloatField(null=True, blank=True, default=0.0,
                                  verbose_name=_('Threshold'))

    def __str__(self):
        return self.danger_category

class Pictogram(models.Model):
    name = models.CharField(max_length=255)
    pictogram = models.FileField(upload_to=upload_files, null=True, blank=True)

    def __str__(self):
        return self.name
