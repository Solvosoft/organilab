# encoding: utf-8
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, reverse
from django.shortcuts import render

from laboratory.forms import InformForm, CommentForm
from laboratory.models import Inform
from laboratory.decorators import has_lab_assigned
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
import json


@permission_required('laboratory.view_inform')
def get_informs(request, *args, **kwargs):
    lab = int(kwargs.get('lab_pk'))
    content = ContentType.objects.get(app_label="laboratory", model="laboratory")
    informs= Inform.objects.filter(object_id=lab, content_type=content).order_by('-pk')
    context = {
        'informs':informs,
        'form': InformForm,
        'laboratory': kwargs.get('lab_pk')

    }
    return render(request, 'laboratory/inform.html', context=context)
@permission_required('laboratory.delete_inform')
def remove_inform(request, *args, **kwargs):
    informs= Inform.objects.filter(pk=int(kwargs.get('pk'))).first()
    if informs:
        informs.delete()
        return redirect(reverse('laboratory:get_informs',kwargs={'lab_pk':kwargs.get('lab_pk')}))
    return redirect(reverse('laboratory:get_informs', kwargs={'lab_pk': kwargs.get('lab_pk')}))


@has_lab_assigned()
@permission_required('laboratory.add_inform')
def create_informs(request, *args, **kwargs):

    form = InformForm(request.POST)
    laboratory = kwargs.get('lab_pk')
    if form.is_valid():

        inform= form.save(commit=False)
        content = ContentType.objects.get(app_label=kwargs.get("content_type"), model=kwargs.get("model"))
        inform.content_type=content
        inform.object_id=int(laboratory)
        inform.schema=inform.custom_form.schema


        inform.save()
        return redirect(reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory}))

    return render(request, 'laboratory/inform.html', context={'laboratory':laboratory})

def update_inform_data(item,data):

    if 'key' in item and 'defaultValue' in item:
        if item['key'] in data:
            if item['type'] not in ["selectboxes"]:
                item['defaultValue']=data[item['key']][0]
            else:
                aux_list = {}
                for key in data[item['key']]:
                    aux_list[key] = True
                    item['defaultValue'] = aux_list

    if 'components' in item:
        for child in item['components']:
            update_inform_data(child,data)

    if 'rows' in item and isinstance(item['rows'], (list,tuple)):
        for row in item['rows']:
            for child in row:
                update_inform_data(child,data)

@has_lab_assigned()
@permission_required('laboratory.change_inform')
def complete_inform(request, *args, **kwargs):
    inform = Inform.objects.get(pk=kwargs.get('pk'))
    schema = inform.schema
    laboratory= kwargs.get('lab_pk')
    form = json.dumps(schema,indent=2)
    context = {"schema": form,
               'inform': inform,
               'laboratory': laboratory,
               'form':CommentForm}

    if request.method=='POST':

        data = dict(request.POST)
        inform.status =request.POST.get('status')
        del data['csrfmiddlewaretoken']
        del data['status']

        result= {}

        for d in data.keys():
            result[d[d.find("[")+1:d.find("]")]]=data[d]

        update_inform_data(schema, result)
        inform.schema = schema
        inform.save()

        return JsonResponse({'url':reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory})})
    return render(request, 'laboratory/complete_inform.html', context)
