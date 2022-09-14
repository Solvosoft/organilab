import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import TemplateView

from derb.models import CustomForm


def get_form_schema(**kwargs):
    """
    Returns the schema of the form.
    """
    form_id = kwargs.get('form_id')
    if form_id:
        form = CustomForm.objects.get(id=form_id)
        return form.schema

def getId(request):
    url = request.META['HTTP_REFERER']
    url = url.split("/")
    form_id = url[len(url)-1]
    return form_id

class EditView(TemplateView):
    template_name = 'formBuilder/edit_view.html'

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context['saved_schema'] = json.dumps(get_form_schema(**kwargs))
        return context

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        request_context = request
        if is_ajax:
            if request.method == 'POST':
                form_id = getId(request)
                schema = json.loads(request.body)
                custom_form = CustomForm.objects.get(id=form_id)
                custom_form.schema = schema
                custom_form.save()
                return JsonResponse(json.dumps({"result": True}), safe=False)
            else:
                return JsonResponse(json.dumps({"result": False}), safe=False)
        else:
            return HttpResponseBadRequest('Invalid request')

def UpdateForm(request):
    form_id = getId(request)
    if request.method == 'POST':
        form = CustomForm.objects.get(id=form_id)
        form.name = request.POST.get('name')
        form.schema['name'] = form.name
        form.save()
    return JsonResponse({"name": form.schema['name']})
