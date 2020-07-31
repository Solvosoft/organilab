from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class FeedbackEntry(models.Model):
    title = models.CharField(_('Title'), max_length=255)
    explanation = models.TextField(_('Explanation'), null=True, blank=True)
    related_file = models.FileField(
        _('Related file'), upload_to='media/feedback_entries/', null=True, blank=True)
    laboratory_id = models.IntegerField(
        default=0, null=True, verbose_name=_("Laboratory id"))
    user = models.ForeignKey(
        User, verbose_name=_("User"), null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Feedback entry')
        verbose_name_plural = _('Feedback entries')


    def __str__(self):
        return '%s' % (self.title,)

class DemoRequest(models.Model):
    name = models.CharField(_('First Name'), max_length=120)
    business_email = models.EmailField(_('Business Email Address'),max_length=70)
    company_name = models.CharField(_('Company Name'), max_length=120)
    country = models.CharField(_('Country Name'), max_length=120)
    phone_number = models.CharField(_('Phone Number'),max_length=12)

    def __str__(self):
        return '%s %s' % (self.first_name, self.company_name)

    class Meta:
        verbose_name = _('Demo Request')
        verbose_name_plural = _('Demo Requests')

