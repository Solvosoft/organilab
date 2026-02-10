from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator

from laboratory.forms import InformSchedulerForm, InformSchedulerFormEdit
from laboratory.models import InformScheduler, Laboratory
from laboratory.views.djgeneric import UpdateView, CreateView, DetailView


@method_decorator(
    permission_required("laboratory.add_informscheduler"), name="dispatch"
)
class InformSchedulerAdd(CreateView):
    model = InformScheduler
    template_name = "informs/informscheduler_create.html"
    form_class = InformSchedulerForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["org_pk"] = self.org
        kwargs["initial"] = {"organization": self.org}
        return kwargs

    def get_success_url(self):
        return reverse("laboratory:inform_index", args=[self.org])


@method_decorator(
    permission_required("laboratory.change_informscheduler"), name="dispatch"
)
class InformSchedulerEdit(UpdateView):
    model = InformScheduler
    template_name = "informs/informscheduler_edit.html"
    form_class = InformSchedulerFormEdit

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["org_pk"] = self.org
        kwargs["initial"] = {"organization": self.org}
        return kwargs

    def get_success_url(self):
        return reverse("laboratory:inform_index", args=[self.org])


@method_decorator(
    permission_required("laboratory.view_informscheduler"), name="dispatch"
)
class InformSchedulerDetail(DetailView):
    model = InformScheduler
    template_name = "informs/informscheduler_detail.html"


@permission_required("laboratory.view_inform")
def get_inform_index(request, org_pk):

    labs = Laboratory.objects.filter(organization__pk=org_pk)
    schedulers = InformScheduler.objects.filter(organization__pk=org_pk).order_by(
        "active"
    )

    return render(
        request,
        "informs/index.html",
        context={"org_pk": org_pk, "labs": labs, "schedulers": schedulers},
    )
