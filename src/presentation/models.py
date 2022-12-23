from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractOrganizationRef(models.Model):

    organization = models.ForeignKey('laboratory.OrganizationStructure', null=True, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class FeedbackEntry(models.Model):
    title = models.CharField(_('Title'), max_length=255)
    explanation = models.TextField(_('Explanation'), null=True, blank=True)
    related_file = models.FileField(
        _('Related file'), upload_to='media/feedback_entries/', null=True, blank=True)
    laboratory_id = models.IntegerField(
        default=0, null=True, verbose_name=_("Laboratory id"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Feedback entry')
        verbose_name_plural = _('Feedback entries')

    def __str__(self):
        return '%s' % (self.title,)


class Donation(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    email = models.CharField(max_length=100, verbose_name=_("Email"))
    amount = models.CharField(max_length=10, verbose_name=_("Amount"))
    details = models.TextField(max_length=255, verbose_name=_("Details"))
    is_donator = models.BooleanField(default=True, verbose_name=_("Add me to the donators list"))
    is_paid = models.BooleanField(default=False, verbose_name=_("Is paid?"))
    donation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Donation date'))

    class Meta:
        verbose_name = _("Donation")
        verbose_name_plural = _("Donations")

    def __str__(self):
        return f'{self.name}: ${self.amount}'
