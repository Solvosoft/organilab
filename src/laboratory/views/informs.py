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
from derb.models import CustomForm


@permission_required('laboratory.view_inform')
def get_informs(request, *args, **kwargs):
    informs= Inform.objects.all().order_by('-pk')
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
        inform.object_id=1
        inform.schema=inform.custom_form.schema


        inform.save()
        return redirect(reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory}))

    return render(request, 'laboratory/inform.html', context={'laboratory':laboratory})

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

        i = 0

        for f in schema['components']:
            if f['key'] in result:
                if schema['components'][i]['type'] not in ["selectboxes"]:
                    schema['components'][i]['defaultValue'] = result[f['key']][0]
                else:
                    z={}
                    for s in result[f['key']]:
                        z[s]=True
                    schema['components'][i]['defaultValue'] = z

            i += 1

        inform.schema = schema
        inform.save()

        return JsonResponse({'url':reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory})})
    return render(request, 'laboratory/complete_inform.html', context)