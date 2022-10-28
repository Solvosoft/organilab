# encoding: utf-8
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, reverse
from django.shortcuts import render

from laboratory.forms import InformForm
from laboratory.models import Inform
from laboratory.decorators import has_lab_assigned
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
import json

def get_informs(request):
    informs= Inform.objects.all()
    context = {
        'informs':informs,
        'form': InformForm
    }
    return render(request, 'laboratory/inform.html', context=context)

def create_informs(request, lab, content_type, model):
    form = InformForm(request.POST)
    if form.is_valid():
        inform= form.save(commit=False)
        content = ContentType.objects.get(app_label=content_type, model=model)
        inform.content_type=content
        inform.object_id=lab
        inform.save()
        return redirect(reverse('laboratory:get_informs'))
    return render(request, 'laboratory/inform.html')

def complete_inform(request, pk):
    template_name = 'laboratory/complete_inform.html'
    inform = Inform.objects.get(pk=2)
    schema = inform.custom_form.schema

    context = {"schema": json.dumps(schema,indent=2)}
    if request.method=='POST':
        print(request.POST.keys())
        return render(request, template_name, context)
    return render(request, template_name, context)