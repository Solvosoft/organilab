from async_notifications.utils import send_email_from_template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import CreateView
from paypal.standard.forms import PayPalPaymentsForm

from presentation.models import Donation, FeedbackEntry
from presentation.forms import DonateForm, FeedbackEntryForm
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
            request, 'presentation/donate_organilab.html', {'paypal_form': paypal_form, 'pay': pay, 'form':form})
    else:
        form = DonateForm()
        return render(
            request, 'presentation/donate_organilab.html', {'form': form, 'pay': pay})


def donate_success(request):
    messages.success(request, _("Your donation was completed successfully, thank you for support this project!"))
    return HttpResponseRedirect(reverse('donate'))


@method_decorator(login_required(), name='dispatch')
class FeedbackView(CreateView):
    template_name = 'feedback/feedbackentry_form.html'
    model = FeedbackEntry
    form_class = FeedbackEntryForm

    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in request.GET:
            self.org= int(request.GET['org_pk'])
        if 'lab_pk' in request.GET:
            self.lab= int(request.GET['lab_pk'])
        return CreateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FeedbackView, self).get_context_data()
        context['lab_pk'] = self.lab
        context['org_pk'] = self.org
        return context

    def get_success_url(self):
        text_message = _(
            'Thank you for your help. We will check your problem as soon as we can')
        messages.add_message(self.request, messages.SUCCESS, text_message)
        try:
            lab_pk = int(self.request.POST.get('lab_pk', 0))
            org_pk = int(self.request.POST.get('org_pk', 0))
        except:
            lab_pk = None
            org_pk = None
        dev = reverse('index')
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        if lab_pk and org_pk:
            self.object.laboratory_id = lab_pk
            dev = reverse('laboratory:labindex', kwargs={'lab_pk': lab_pk, 'org_pk': org_pk})
        if self.request.user.is_authenticated or lab_pk:
            self.object.save()

        send_email_from_template("New feedback",
                                 settings.DEFAULT_FROM_EMAIL,
                                 context={
                                     'feedback': self.object
                                 },
                                 enqueued=True,
                                 user=None,
                                 upfile=self.object.related_file)

        return dev


def index_organilab(request):
    if request.user.is_authenticated:
        return redirect(reverse('auth_and_perms:select_organization_by_user'))
    return render(request, 'index.html')
