import sys
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_organilab_version():
    return sys.modules["organilab"].__version__


@register.simple_tag
def is_testing_mode():
    return getattr(settings, 'TESTING_MODE', False)
