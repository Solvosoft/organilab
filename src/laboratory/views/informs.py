# encoding: utf-8
from django.conf import settings
from django.contrib.admin.models import DELETION, ADDITION
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, reverse, get_object_or_404
from django.shortcuts import render

from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.forms import InformForm, CommentForm
from laboratory.models import Inform, OrganizationStructure, Laboratory

from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
import json

from laboratory.utils import organilab_logentry


@permission_required('laboratory.view_inform')
def get_informs(request, *args, **kwargs):
    lab = int(kwargs.get('lab_pk'))
    content = ContentType.objects.get(app_label="laboratory", model="laboratory")
    informs= Inform.objects.filter(object_id=lab, content_type=content).order_by('-pk')
    org_pk = kwargs.get('org_pk', None)
    context = {
        'informs':informs,
        'form': InformForm(org_pk=org_pk),
        'laboratory': kwargs.get('lab_pk'),
        'org_pk': org_pk,

    }
    return render(request, 'laboratory/inform.html', context=context)
@permission_required('laboratory.delete_inform')
def remove_inform(request, *args, **kwargs):
    informs= Inform.objects.filter(pk=int(kwargs.get('pk'))).first()
    if informs:
        organilab_logentry(request.user, informs, DELETION, 'informs', relobj=kwargs.get('lab_pk'))
        informs.delete()
        return redirect(reverse('laboratory:get_informs',kwargs={'lab_pk':kwargs.get('lab_pk'),'org_pk':kwargs.get('org_pk')}))
    return redirect(reverse('laboratory:get_informs', kwargs={'lab_pk': kwargs.get('lab_pk'),'org_pk':kwargs.get('org_pk')}))



@permission_required('laboratory.add_inform')
def create_informs(request, *args, **kwargs):
    org = kwargs.get('org_pk')
    form = InformForm(request.POST, org_pk=org)
    laboratory = kwargs.get('lab_pk')
    lab = get_object_or_404(Laboratory, pk=laboratory)
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org)
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(lab, organization)
    if form.is_valid():
        inform= form.save(commit=False)
        content = ContentType.objects.get(app_label=kwargs.get("content_type"), model=kwargs.get("model"))
        inform.content_type = content
        inform.object_id = int(laboratory)
        inform.schema = get_components_url(request, inform.custom_form.schema, org, laboratory) #Changes the url of the components to the respective api
        inform.organization = organization
        inform.created_by = request.user
        inform.save()
        organilab_logentry(request.user, inform, ADDITION, 'informs', relobj=laboratory)
        return redirect(reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory,'org_pk':org}))

    return render(request, 'laboratory/inform.html', context={'laboratory':laboratory, 'org_pk':org})


def update_inform_data(item,data):

    if 'key' in item and 'defaultValue' in item:
        if item['key'] in data:
            if item['type'] not in ["selectboxes", "select", "custom_select"]:
                item['defaultValue'] = data[item['key']][0]
            elif item['type'] in ["select", "custom_select"]:
                # Save data from a select, allows multiple selection
                item['defaultValue'] = data[item['key']]
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


@permission_required('laboratory.change_inform')
def complete_inform(request, *args, **kwargs):
    inform = Inform.objects.get(pk=kwargs.get('pk'))
    schema = inform.schema
    laboratory= kwargs.get('lab_pk')
    org= kwargs.get('org_pk')
    form = json.dumps(schema,indent=2)
    context = {"schema": form,
               'inform': inform,
               'laboratory': laboratory,
               'org_pk': org,
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

        return JsonResponse({'url':reverse('laboratory:get_informs', kwargs={'lab_pk':laboratory, 'org_pk':org})})
    return render(request, 'laboratory/complete_inform.html', context)

"""
This is a method, not a view, no permission_required decorator needed
"""
def get_components_url(request, schema, org, laboratory):
    host = request.get_host()
    protocol = 'https://' if request.is_secure() else 'http://'
    for component in schema['components']:
        if component['type'] == 'custom_select':
            route = reverse(f'derb:{component["data"]["api"]}', kwargs={'org_pk': org})
            if 'lab=' in component['data']['url']:
                component['data']['url'] = f'{protocol}{host}{route}?lab={laboratory}'
            else:
                component['data']['url'] = f'{protocol}{host}{route}'

    return schema
