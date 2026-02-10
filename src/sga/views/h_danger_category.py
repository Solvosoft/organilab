from django.views.generic import TemplateView

from sga.forms import HCategoryForm


class HCategoryView(TemplateView):
    template_name = 'h_category/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_create'] = HCategoryForm(prefix="create")
        context['form_update'] = HCategoryForm(prefix="update")
        context['org_pk'] = self.kwargs.get("org_pk", None)
        return context
