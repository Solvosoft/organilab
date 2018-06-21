from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

# Create your models here.


@python_2_unicode_compatible
class FeedbackEntry(models.Model):
    title = models.CharField(_('Title'), max_length=255)
    explanation = models.TextField(_('Explanation'), blank=True)
    related_file = models.FileField(
        _('Related file'), upload_to='media/feedback_entries/', blank=True)

    class Meta:
        verbose_name = _('Feedback entry')
        verbose_name_plural = _('Feedback entries')
        permissions = (
            ("view_feedbackentry", _("Can see available feed back entry")),
        )

    def __str__(self):
        return '%s' % (self.title,)
