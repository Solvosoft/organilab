# -*- coding: UTF-8 -*-
from .models import Donation
from paypal.standard.ipn.signals import valid_ipn_received
from paypal.standard.models import ST_PP_COMPLETED
from datetime import datetime


def paypal_bill_paid(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        donation = Donation.objects.get(pk=ipn_obj.invoice)
        donation.is_paid = True
        donation.donation_date = datetime.now()
        donation.details = ipn_obj.txn_id
        donation.save()


valid_ipn_received.connect(paypal_bill_paid)
