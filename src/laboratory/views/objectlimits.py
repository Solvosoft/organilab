from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from laboratory.forms import ReactiveStockForm
from laboratory.models import Object
from laboratory.utils import check_user_access_kwargs_org_lab

@method_decorator(permission_required("laboratory.view_object"), name="dispatch")
class ReactiveStockDashboard(TemplateView):
    template_name = "laboratory/objectlimit/dashboard.html"
    def get(self, request, *args, **kwargs):
        if not check_user_access_kwargs_org_lab(self.kwargs.get("org_pk", None), self.kwargs.get("lab_pk", None), request.user):
            raise Http404()
        return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super(ReactiveStockDashboard, self).get_context_data()
        context["org_pk"] = self.kwargs["org_pk"]
        context["lab_pk"] = self.kwargs["lab_pk"]
        x = ""
        i = 0
        for key in self.request.GET:
            data = self.request.GET.get(key)
            if i > 0:
                x += f"&{key}={data}"
            else:
                x += f"?{key}={data}"
            i += 1
        if i>0:
            x += "&laboratory=" + str(self.kwargs["lab_pk"])
        else:
            x += "?laboratory=" + str(self.kwargs["lab_pk"])
        urls = {
            "objectlimits_url": reverse(
                "objectlimitschart-detail", kwargs={"pk": self.kwargs["org_pk"]}
            )
            + x,
        }
        context.update(urls)
        context["form"] = ReactiveStockForm(
            self.request.GET, organization=self.kwargs["org_pk"]
        )

        return context
