from django.db import models
from django.utils.translation import ugettext_lazy as _
# Create your models here.
from tagging.registry import register
from tagging.fields import TagField
from mptt.models import MPTTModel, TreeForeignKey


class WarningClass(MPTTModel):
    TYPE = (
        ("typeofdanger", _("Type of danger")),
        ("class", _("Danger class")),
        ("category", _("Danger Category"))
    )
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    danger_type = models.CharField(
        max_length=25, default="category", choices=TYPE,
        verbose_name=_("Danger type"))

    parent = TreeForeignKey('self',
                            on_delete=models.CASCADE, null=True, blank=True,
                            related_name='children')

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


# Pictograma de precaución


class WarningWord(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    weigth = models.SmallIntegerField(default=0, verbose_name=_("Weigth"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Warning Word')
        verbose_name_plural = _('Warning Words')


# Indicación de peligro


class Pictogram(models.Model):
    name = models.CharField(max_length=150, primary_key=True,
                            verbose_name=_("Name"))
    warning_word = models.ForeignKey(WarningWord, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Pictogram')
        verbose_name_plural = _('Pictograms')


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
    pictograms = models.ManyToManyField(
        Pictogram, verbose_name=_("Pictograms"))
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


class Substance(models.Model):
    comercial_name = models.CharField(max_length=250,
                                      verbose_name=_("Comercial name"))
    uipa_name= models.CharField(max_length=250, default="",
                                verbose_name=_("UIPA name"))
    components = models.ManyToManyField(
        Component, verbose_name=_("Components"))
    danger_indications = models.ManyToManyField(
        DangerIndication,
        verbose_name=_("Danger indications"))
    synonymous = TagField(verbose_name=_("Synonymous"))
    agrochemical = models.BooleanField(default=False,
                                       verbose_name=_("Agrochemical"))

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


register(Substance)


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
        return 'name={0} | height={1}, height_unit={2}, width={3}, width_unit={4}'.format(self.name, self.height,
                                                                                          self.height_unit, self.width,
                                                                                          self.width_unit)

    class Meta:
        verbose_name = _('Recipient Size')
        verbose_name_plural = _('Size of recipients')


class Label(models.Model):
    sustance = models.ForeignKey(Substance,
                                 verbose_name=_("Sustance"),
                                 on_delete=models.CASCADE)
    builderInformation = models.ForeignKey(
        BuilderInformation, verbose_name=_("Builder Information"),
        on_delete=models.CASCADE)
    commercial_information = models.TextField(
        null=True, blank=True,
        verbose_name=_("Commercial Information"))
    size = models.ForeignKey(RecipientSize, verbose_name=_("Recipient Size"), on_delete=models.CASCADE)

    def __str__(self):
        return str(self.sustance)

    class Meta:
        verbose_name = _('Label')
        verbose_name_plural = _('Labels')


class TemplateSGA(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    recipient_size = models.ForeignKey(RecipientSize, verbose_name=_("Recipient Size"), on_delete=models.CASCADE)
    json_representation = models.TextField()
    community_share = models.BooleanField(default=True, verbose_name=_("Share with community"))
    preview = models.TextField(help_text="B64 preview image")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Template SGA')
        verbose_name_plural = _('Templates SGA')
