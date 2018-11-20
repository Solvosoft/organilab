'''
Created on 30 jun. 2018

@author: luis
'''

from django import template
from constance import config
from django.utils.safestring import mark_safe
register = template.Library()

ADSENSEHEADER = """
<script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
<script>
  (adsbygoogle = window.adsbygoogle || []).push({
    google_ad_client: "%s",
    enable_page_level_ads: true
  });
</script>
"""


@register.simple_tag(takes_context=True)
def adsense_header(context):
    if not config.ADSENSE_ACTIVE:
        return ''
    return mark_safe(ADSENSEHEADER % (
        config.ADSENSE_PUB_TOKEN))
