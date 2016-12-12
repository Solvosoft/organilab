# encoding: utf-8

'''
Free as freedom will be 2/9/2016

@author: luisza
'''

from __future__ import unicode_literals
from laboratory.models import ShelfObject
from djreservation.views import ProductReservationView


class ShelfObjectReservation(ProductReservationView):
    base_model = ShelfObject
    modelpk = None
    amount_field = 'quantity'
    extra_display_field = ['limit_quantity', 'measurement_unit']
