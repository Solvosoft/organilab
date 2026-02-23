from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PendingTasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pending_tasks'
    verbose_name = _('Pending Tasks')
