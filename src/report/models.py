import datetime

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from laboratory.models_utils import upload_files

DELIVER = _("Delivered")
WAIT = _("On hold")
GENERATED = _("Generated")
STATUS_TEMPLATE = [
    (_("On hold"), WAIT),
    (_("Delivered"), DELIVER),
    (_("Generated"), GENERATED),
]


class TaskReport(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    type_report = models.CharField(max_length=100, blank=False, null=False)
    form_name = models.TextField(null=True, blank=True)
    table_content = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=30, default=WAIT, choices=STATUS_TEMPLATE)
    file_type = models.CharField(max_length=30, blank=True, null=True)
    file = models.FileField(upload_to=upload_files, blank=True, null=True)
    data = models.JSONField(null=True, blank=True)
    language = models.CharField(max_length=10, default=settings.LANGUAGE_CODE)

    def __str__(self):
        return f"{self.pk} - {self.type_report} - {self.file_type}"


class DocumentReportStatus(models.Model):
    report = models.ForeignKey(TaskReport, on_delete=models.CASCADE)
    report_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=512)

    def __str__(self):
        return f"{self.report_time} {self.description}"


class ObjectChangeLogReport(models.Model):
    task_report = models.ForeignKey(TaskReport, on_delete=models.CASCADE)
    laboratory = models.ForeignKey("laboratory.Laboratory", on_delete=models.CASCADE)
    unit = models.ForeignKey("laboratory.Catalog", on_delete=models.CASCADE)
    object = models.ForeignKey("laboratory.Object", on_delete=models.CASCADE)
    diff_value = models.FloatField(default=0.0)


class ObjectChangeLogReportBuilder(models.Model):
    report = models.ForeignKey(ObjectChangeLogReport, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    update_time = models.DateTimeField()
    new_value = models.FloatField(default=0.0)
    old_value = models.FloatField(default=0.0)
    diff_value = models.FloatField(default=0.0)


class RegencyReport(models.Model):
    task_report = models.ForeignKey(TaskReport, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        "laboratory.OrganizationStructure", on_delete=models.CASCADE
    )
    year = models.IntegerField()
    physical_total = models.FloatField(null=True, blank=True, default=0.0)
    break_physical_total = models.BooleanField(default=False)
    enviroment_total = models.FloatField(null=True, blank=True, default=0.0)
    break_enviroment_total = models.BooleanField(default=False)
    health_total = models.FloatField(null=True, blank=True, default=0.0)
    break_health_total = models.BooleanField(default=False)


class RegencyReportBuilder(models.Model):
    report = models.ForeignKey(RegencyReport, on_delete=models.CASCADE)
    substance = models.ForeignKey("laboratory.Object", on_delete=models.DO_NOTHING)
    danger_category = models.CharField(max_length=50)
    danger_list = models.PositiveIntegerField(default=3)
    total = models.FloatField(default=0.0)
    break_threshold = models.BooleanField(default=False)
