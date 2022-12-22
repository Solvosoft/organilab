from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm

from presentation.models import Donation
from presentation.forms import DonateForm
from django.conf import settings


def index_tutorial(request, org_pk):
    return render(request, 'tutorial.html', context={'org_pk': org_pk})


@login_required
def donate(request):
    pay = False

    if request.method == "POST":
        form = DonateForm(request.POST)
        if form.is_valid():
            donation = Donation(
                name=form.cleaned_data['name'], email=form.cleaned_data['email'],
                amount=form.cleaned_data['amount'], is_donator=form.cleaned_data['is_donator'],
                is_paid=False)
            donation.save()
            paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': form.cleaned_data['amount'],
                'item_name': _('Donate Organilab'),
                'invoice': str(donation.pk),
                'currency_code': 'USD',
                'notify_url': settings.MY_PAYPAL_HOST + reverse('paypal-ipn'),
                'return_url': settings.MY_PAYPAL_HOST + reverse('donate_success'),
                'cancel_return': settings.MY_PAYPAL_HOST + reverse('index'),
            }
            pay = True
            paypal_form = PayPalPaymentsForm(initial=paypal_dict)
            paypal_form.button_type = "donate"
        return render(
            request, 'donate_organilab.html', {'paypal_form': paypal_form, 'pay': pay, 'form':form})
    else:
        form = DonateForm()
        return render(
            request, 'donate_organilab.html', {'form': form, 'pay': pay})


def donate_success(request):
    messages.success(request, _("Your donation was completed successfully, thank you for support this project!"))
    return HttpResponseRedirect(reverse('donate'))



@login_required
def index_organilab(request):
    return render(request, 'index_organilab.html')
