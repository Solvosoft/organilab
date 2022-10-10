import json

from django.shortcuts import render

from derb.models import CustomForm


def previewForm(request, form_id):
    template_name = 'formBuilder/preview_form.html'

    form = CustomForm.objects.get(id=form_id)
    schema = form.schema
    context = {"schema": json.dumps(schema)} 

    return render(request, template_name, context)
    
    

