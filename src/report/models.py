from django.db import models

from laboratory.models import TaskReport


# Create your models here.

class DocumentReportStatus(models.Model):
    report=models.ForeignKey(TaskReport, on_delete=models.CASCADE)
    report_time = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=512)

    def __str__(self):
        return f"{self.report_time} {self.description}"