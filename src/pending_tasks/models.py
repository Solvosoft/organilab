from django.db import models
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import Profile, Rol
from presentation.models import AbstractOrganizationRef


class PendingTask(AbstractOrganizationRef):
    PENDING = 0
    IN_PROCESS = 1
    FINISHED = 2

    STATUS = (
        (PENDING, _("Pending")),
        (IN_PROCESS, _("In process")),
        (FINISHED, _("Finished"))
    )
    description = models.TextField(_('Description'), null=True, blank=True)
    status = models.IntegerField(_('Status'), choices=STATUS, default=PENDING)
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name=_('Profile'))
    rols = models.ManyToManyField(Rol, verbose_name=_('Roles'), blank=True)
    link = models.URLField(_('Link'), null=True, blank=True)

    class Meta:
        verbose_name = _('Pending task')
        verbose_name_plural = _('Pending tasks')
        ordering = ['-creation_date']

    def __str__(self):
        return f'{self.description} - {self.profile}'
