from async_notifications.utils import send_email_from_template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import CreateView
from presentation.models import Donation, FeedbackEntry
from presentation.forms import DonateForm, FeedbackEntryForm
from django.conf import settings
import logging

logger = logging.getLogger("organilab")


def index_tutorial(request, org_pk):
    return render(request, "tutorial.html", context={"org_pk": org_pk})


@method_decorator(login_required(), name="dispatch")
class FeedbackView(CreateView):
    template_name = "feedback/feedbackentry_form.html"
    model = FeedbackEntry
    form_class = FeedbackEntryForm

    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if "org_pk" in request.GET:
            self.org = int(request.GET["org_pk"])
        if "lab_pk" in request.GET:
            self.lab = int(request.GET["lab_pk"])
        return CreateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FeedbackView, self).get_context_data()
        context["lab_pk"] = self.lab
        context["org_pk"] = self.org
        return context

    def get_success_url(self):
        text_message = _(
            "Thank you for your help. We will check your problem as soon as we can"
        )
        messages.add_message(self.request, messages.SUCCESS, text_message)
        try:
            lab_pk = int(self.request.POST.get("lab_pk", 0))
            org_pk = int(self.request.POST.get("org_pk", 0))
        except Exception as e:
            logger.error("Error parsing organization or lab id", exc_info=e)
            lab_pk = None
            org_pk = None
        dev = reverse("index")
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        if lab_pk and org_pk:
            self.object.laboratory_id = lab_pk
            dev = reverse(
                "laboratory:labindex", kwargs={"lab_pk": lab_pk, "org_pk": org_pk}
            )
        if self.request.user.is_authenticated or lab_pk:
            self.object.save()

        send_email_from_template(
            "New feedback",
            settings.DEFAULT_FROM_EMAIL,
            context={"feedback": self.object},
            enqueued=True,
            user=None,
            upfile=self.object.related_file,
        )

        return dev


def index_organilab(request):
    if request.user.is_authenticated:
        return redirect(reverse("auth_and_perms:select_organization_by_user"))
    return render(request, "index.html")


def general_information(request):
    return render(request, "general_information.html")
