from django.db import models
from django.utils.translation import ugettext_lazy as _
# Create your models here.


class WarningClass(models.Model):
    CATEGORIES = (
        (0, _("Physic warning")),
        (1, _("Healty warning")),
        (2, _("Environment warning"))
    )
    name = models.CharField(max_length=150)
    category = models.SmallIntegerField(choices=CATEGORIES)

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
    name = models.CharField(max_length=150, primary_key=True)

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
    name = models.CharField(max_length=50)
    weigth = models.SmallIntegerField(default=0)

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
    code = models.CharField(max_length=150, primary_key=True)
    description = models.TextField()
    warning_words = models.ForeignKey(WarningWord, on_delete=models.CASCADE)
    pictograms = models.ManyToManyField(Pictogram)
    warning_class = models.ManyToManyField(WarningClass)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _('Danger Indication')
        verbose_name_plural = _('Indication of Danger')
        permissions = (
            ("view_dangerindication", _("Can see available indication of danger")),
        )


class Component(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Component')
        verbose_name_plural = _('Components')
        permissions = (
            ("view_component", _("Can see available Component")),
        )


class Sustance(models.Model):
    comercial_name = models.CharField(max_length=250)
    cas_number = models.CharField(max_length=150)
    components = models.ManyToManyField(Component)
    danger_indications = models.ManyToManyField(DangerIndication)

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

# build information


class BuilderInformation(models.Model):
    name = models.CharField(max_length=150)
    phone = models.TextField(max_length=15)
    address = models.TextField(max_length=100)

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
    sustance = models.ForeignKey(Sustance, on_delete=models.CASCADE)
    builderInformation = models.ForeignKey(
        BuilderInformation, on_delete=models.CASCADE)
    size = models.SmallIntegerField(choices=SIZES)

    def __str__(self):
        return str(self.sustance)

    class Meta:
        verbose_name = _('Label')
        verbose_name_plural = _('Labels')
        permissions = (
            ("view_label", _("Can see available labels")),
        )
