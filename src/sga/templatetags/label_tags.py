'''
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 27 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
'''

from django import template
from sga.models import RecipientSize

register = template.Library()


@register.assignment_tag
def get_recipient_size():
    return RecipientSize.objects.all()
