from django.contrib.admin.models import DELETION, ADDITION
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from laboratory.models import OrganizationStructure
from laboratory.views.djgeneric import ListView, DeleteView

from derb.models import CustomForm
from laboratory.utils import organilab_logentry


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("derb.view_customform", raise_exception=True),
    name="dispatch",
)
class FormList(ListView):
    model = CustomForm
    context_object_name = "forms"
    template_name = "formBuilder/form_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.org:
            queryset = queryset.filter(organization__pk=self.org)
        else:
            queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms"] = self.get_queryset()
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("derb.delete_customform", raise_exception=True),
    name="dispatch",
)
class DeleteForm(DeleteView):
    model = CustomForm

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(
            self.request.user,
            self.object,
            DELETION,
            "custom form",
            changed_data=["name", "schema", "organization"],
            change_message=_("Deleted custom form '%(name)s'")
            % {"name": self.object.name},
        )
        self.object.delete()
        return HttpResponseRedirect(success_url)

    # decir este formulario tiene x respuestas en el warning
    def get_success_url(self, **kwargs):
        success_url = reverse_lazy("derb:form_list", kwargs={"org_pk": self.org})
        return success_url


@login_required
@permission_required("derb.add_customform", raise_exception=True)
def CreateForm(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)

    if request.method == "POST":

        empty_schema = {
            "name": request.POST.get("name"),
            "status": "admin",
            "components": [],
        }

        custom_form = CustomForm.objects.create(
            name=empty_schema["name"],
            status=empty_schema["status"],
            schema=empty_schema,
            organization=organization,
        )
        url = reverse("derb:edit_view", args=[org_pk, custom_form.id])
        organilab_logentry(
            request.user,
            custom_form,
            ADDITION,
            "custom form",
            changed_data=["name", "status", "schema", "organization"],
            change_message=_("Created custom form '%(name)s'")
            % {"name": custom_form.name},
        )

        return JsonResponse({"url": url})
    return None
