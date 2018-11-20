from django import template
from django.conf import settings
from django.utils.translation import get_language
register = template.Library()


@register.simple_tag(takes_context=True)
def get_dataset_translation(context):
    lang = get_language()
    print("LANG ", lang)
    if lang:
        if lang in settings.DATASETS_SUPPORT_LANGUAGES:
            return settings.DATASETS_SUPPORT_LANGUAGES[lang]
    return "//cdn.datatables.net/plug-ins/1.10.19/i18n/English.json"
