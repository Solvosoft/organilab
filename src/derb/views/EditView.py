import json

from django.contrib.admin.models import CHANGE
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import TemplateView

from derb.models import CustomForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

from laboratory.utils import organilab_logentry


def get_form_schema(**kwargs):
    """
    Returns the schema of the form.
    """
    form_id = kwargs.get("form_id")
    if form_id:
        form = CustomForm.objects.get(id=form_id)
        return form.schema


def getId(request, index=1):
    url = request.META["HTTP_REFERER"]
    url = url.split("/")
    form_id = url[len(url) - index]
    return form_id


@method_decorator(permission_required("derb.change_customform"), name="dispatch")
class EditView(TemplateView):
    template_name = "formBuilder/edit_view.html"

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context["saved_schema"] = json.dumps(get_form_schema(**kwargs))
        return context

    def post(self, request, org_pk=None):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        request_context = request
        if is_ajax:
            if request.method == "POST":
                form_id = getId(request, 2)
                schema = json.loads(request.body)
                custom_form = CustomForm.objects.get(id=form_id)
                custom_form.schema = schema
                custom_form.save()
                organilab_logentry(
                    self.request.user,
                    custom_form,
                    CHANGE,
                    "custom form",
                    changed_data=["schema"],
                )
                return JsonResponse(json.dumps({"result": True}), safe=False)
            else:
                return JsonResponse(json.dumps({"result": False}), safe=False)
        else:
            return HttpResponseBadRequest("Invalid request")


@permission_required("derb.change_customform")
def UpdateForm(request, org_pk):
    form_id = getId(request, 2)
    if request.method == "POST":
        form = CustomForm.objects.get(id=form_id)
        form.name = request.POST.get("name")
        form.schema["name"] = form.name
        form.save()
        organilab_logentry(
            request.user, form, CHANGE, "custom form", changed_data=["name", "schema"]
        )
    return JsonResponse({"name": form.schema["name"]})
