from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

DELIVER = _('Delivered')
WAIT = _('On hold')
GENERATED = _('Generated')
STATUS_TEMPLATE=[(_('On hold'),WAIT),
                  (_('Delivered'),DELIVER),
                  (_('Generated'),GENERATED),
                 ]
class TaskReport(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    type_report = models.CharField(max_length=100, blank=False, null=False)
    form_name = models.TextField(null=True, blank=True)
    table_content = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=30, default=WAIT,choices=STATUS_TEMPLATE)
    file_type = models.CharField(max_length=30, blank=True, null=True)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    data = models.JSONField(null=True, blank=True)
    language = models.CharField(max_length=10, default=settings.LANGUAGE_CODE)

    def __str__(self):
        return f'{self.pk} - {self.type_report} - {self.file_type}'


class DocumentReportStatus(models.Model):
    report=models.ForeignKey(TaskReport, on_delete=models.CASCADE)
    report_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=512)

    def __str__(self):
        return f"{self.report_time} {self.description}"
