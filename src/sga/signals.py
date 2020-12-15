# -*- coding: UTF-8 -*-
from .models import Donation
from paypal.standard.ipn.signals import valid_ipn_received
from paypal.standard.models import ST_PP_COMPLETED


def paypal_bill_paid(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        donation = Donation()
        donation.is_paid = True
        donation.name = ipn_obj.name
        donation.email = ipn_obj.email
        donation.details = ipn_obj
        donation.is_donator = ipn_obj.is_donator
        donation.save()


valid_ipn_received.connect(paypal_bill_paid)
