from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView

from derb.models import CustomForm

@method_decorator(permission_required('derb.view_customform'), name='dispatch')
class FormList(ListView):
    model = CustomForm
    context_object_name = "forms"
    template_name = 'formBuilder/form_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forms'] = CustomForm.objects.all()
        return context

@method_decorator(permission_required('derb.delete_customform'), name='dispatch')
class DeleteForm(DeleteView):
    model = CustomForm
    success_url = reverse_lazy('derb:form_list')
    # decir este formulario tiene x respuestas en el warning
@method_decorator(permission_required('derb.add_customform'), name='dispatch')
def CreateForm(request):

    if request.method == 'POST':

        empty_schema = {
            "name": request.POST.get('name'),
            "status": "admin",
            "components": [
                {
                "collapsible": False,
                "key": "section",
                "type": "custom_section",
                "label": "Section",
                "title": "New Untitled Section",
                "input": False,
                "tableView": False,
                "components": [
                    {
                    "collapsible": False,
                    "key": "section1",
                    "type": "custom_section",
                    "label": "Section",
                    "title": "New Untitled Subsection",
                    "input": False,
                    "tableView": False,
                    "components": []
                    }
                ]
                }
            ]
        }

        custom_form = CustomForm.objects.create(
            name=empty_schema['name'],
            status=empty_schema['status'],
            schema=empty_schema
        )
        url = reverse('derb:edit_view', args=[custom_form.id])
        return JsonResponse({"url": url})
