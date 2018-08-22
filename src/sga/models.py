from django.db import models
from django.utils.translation import ugettext_lazy as _
# Create your models here.
from tagging.registry import register
from tagging.fields import TagField


class WarningCategory(models.Model):
    name = models.CharField(max_length=256, verbose_name=_("Name"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Warning Category')
        verbose_name_plural = _('Warning Categories')
        permissions = (
            ("view_warningclass", _("Can see available Warning Categories")),
        )


class WarningClass(models.Model):
    TYPES = (
        (0, _("Physic danger")),
        (1, _("Healty danger")),
        (2, _("Environment danger"))
    )
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    _type = models.SmallIntegerField(choices=TYPES, verbose_name=_("Type"))
    categories = models.ManyToManyField(WarningCategory,
                                        verbose_name=_("Categories"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Warning Class')
        verbose_name_plural = _('Warning Classes')
        permissions = (
            ("view_warningclass", _("Can see available Warning Classes")),
        )

# Pictograma de precaución


class Pictogram(models.Model):
    name = models.CharField(max_length=150, primary_key=True,
                            verbose_name=_("Name"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Pictogram')
        verbose_name_plural = _('Pictograms')
        permissions = (
            ("view_pictogram", _("Can see available pictograms")),
        )
# palabras de advertencia


class WarningWord(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    weigth = models.SmallIntegerField(default=0, verbose_name=_("Weigth"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Warning Word')
        verbose_name_plural = _('Warning Words')
        permissions = (
            ("view_warningword", _("Can see available Warning Words")),
        )
# Indicación de peligro


class DangerIndication(models.Model):
    code = models.CharField(max_length=150, primary_key=True,
                            verbose_name=_("Code"))
    description = models.TextField(verbose_name=_("Description"))
    warning_words = models.ForeignKey(WarningWord, on_delete=models.CASCADE,
                                      verbose_name=_("Warning words"))
    pictograms = models.ManyToManyField(
        Pictogram, verbose_name=_("Pictograms"))
    warning_class = models.ManyToManyField(WarningClass,
                                           verbose_name=_("Warning class"))
    prudence_advice = models.TextField(default=_("None"),
                                       verbose_name=_("Prudence advice"))

    prudence_advice_help = models.TextField(
        null=True, blank=True,
        verbose_name=_("Help for prudence advice"))

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _('Danger Indication')
        verbose_name_plural = _('Indication of Danger')
        permissions = (
            ("view_dangerindication", _("Can see available indication of danger")),
        )


class Component(models.Model):
    name = models.CharField(max_length=250, verbose_name=_("Name"))
    cas_number = models.CharField(max_length=150, verbose_name=_("CAS number"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Component')
        verbose_name_plural = _('Components')
        permissions = (
            ("view_component", _("Can see available Component")),
        )


class Sustance(models.Model):
    comercial_name = models.CharField(max_length=250,
                                      verbose_name=_("Comercial name"))
    components = models.ManyToManyField(
        Component, verbose_name=_("Components"))
    danger_indications = models.ManyToManyField(
        DangerIndication,
        verbose_name=_("Danger indications"))
    synonymous = TagField(verbose_name=_("Synonymous"))

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
        verbose_name = _('Sustance')
        verbose_name_plural = _('Sustances')
        permissions = (
            ("view_sustance", _("Can see available Sustance")),
        )


register(Sustance)
# build information


class BuilderInformation(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    phone = models.TextField(max_length=15, verbose_name=_("Phone"))
    address = models.TextField(max_length=100, verbose_name=_("Address"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Builder Information')
        verbose_name_plural = _('Information of Builders')
        permissions = (
            ("view_builderinformation", _("Can see available Builder Information")),
        )

# labels


class Label(models.Model):
    SIZES = (
        (0, "default"),
    )
    sustance = models.ForeignKey(Sustance,
                                 verbose_name=_("Sustance"),
                                 on_delete=models.CASCADE)
    builderInformation = models.ForeignKey(
        BuilderInformation, verbose_name=_("Builder Information"),
        on_delete=models.CASCADE)
    size = models.SmallIntegerField(choices=SIZES, verbose_name=_("Size"))

    def __str__(self):
        return str(self.sustance)

    class Meta:
        verbose_name = _('Label')
        verbose_name_plural = _('Labels')
        permissions = (
            ("view_label", _("Can see available labels")),
        )
