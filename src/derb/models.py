from django.db import models


class CustomForm(models.Model):
    STATUS_CHOICES = (
        ('admin', 'Creating form'),
        ('fill', 'Filling form'),
        ('result', 'Form results')
    )
    name = models.CharField(max_length=40)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES)
    schema = models.JSONField(default=dict)


class Section(models.Model):
    form = models.ForeignKey(CustomForm, related_name='sections', on_delete=models.CASCADE)
    name = models.CharField(max_length=40)


class Subsection(models.Model):
    section = models.ForeignKey(Section, related_name='subsections', on_delete=models.CASCADE)
    name = models.CharField(max_length=40)


class FieldType(models.Model):
    import_name = models.CharField(max_length=80)
    display_name = models.CharField(max_length=40)

    def __str__(self):
        return self.display_name


class WidgetType(models.Model):
    import_name = models.CharField(max_length=80)
    display_name = models.CharField(max_length=40)
    extra_args = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.display_name


class CustomFormField(models.Model):

    subsection = models.ForeignKey(Subsection, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    label = models.CharField(max_length=40)
    label_suffix = models.CharField(max_length=10, blank=True, null=True)
    field_type = models.ForeignKey(FieldType, on_delete=models.CASCADE)
    widget_type = models.ForeignKey(WidgetType, on_delete=models.CASCADE)
    help_text = models.CharField(max_length=100, blank=True, null=True)
    initial = models.CharField(max_length=40, blank=True, null=True)
    required = models.BooleanField(default=False)
    disabled = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    localize = models.BooleanField(default=False)
    props_css = models.CharField(max_length=300, blank=True, null=True)
    extra_args = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.label


class Validator(models.Model):

    field = models.ForeignKey(to=CustomFormField, on_delete=models.CASCADE, related_name="validators")
    name = models.CharField(max_length=40)
    parameters = models.JSONField()


class Action(models.Model):
    condition = models.JSONField(blank=True, null=True)
    conditional_field = models.ForeignKey(CustomFormField, on_delete=models.CASCADE, related_name="variable_fields")