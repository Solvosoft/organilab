import sys
from django import template

register = template.Library()

@register.simple_tag
def get_organilab_version():
    return sys.modules['organilab'].__version__
