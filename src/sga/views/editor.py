# Import functions of another modules
import json

import cairosvg
from barcode import Code128
from barcode.writer import SVGWriter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Max
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Library
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgentelella.models import ChunkedUpload
from django.contrib.admin.models import CHANGE, ADDITION

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from sga.forms import SGAEditorForm, EditorForm, PersonalForm, SubstanceForm, RecipientSizeForm, PersonalSGAForm, \
    BuilderInformationForm, \
    LabelForm, PersonalTemplateForm, SGALabelForm, SGALabelComplementsForm, \
    SGALabelBuilderInformationForm, PersonalSGAAddForm, CompanyForm
from sga.models import SGAComplement, Substance
from sga.models import TemplateSGA, PersonalTemplateSGA, Label, BuilderInformation
from sga.api.serializers import SGAComplementSerializer, BuilderInformationSerializer, RecipientSizeSerializer
from sga.models import RecipientSize, DangerIndication, PrudenceAdvice, WarningWord
from django import forms
register = Library()

# SGA Home Page

@login_required
def render_editor_sga(request, org_pk):
    context={ "org_pk": org_pk }
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    return render(request, 'editor/pictogram_editor.html', context)




# SGA editor
@login_required
def template_editor(request, org_pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    clean_canvas_editor = True

    if request.method == "POST":
        finstance = request.POST['instance'] if 'instance' in request.POST else None
        if finstance:
            finstance = get_object_or_404(TemplateSGA, pk=finstance)
        sgaform = EditorForm(request.POST, instance=finstance)
        if sgaform.is_valid():
            instance = sgaform.save(commit=False)
            instance.creator = request.user
            instance.save()
            organilab_logentry(request.user, instance, ADDITION, 'SGA Template from editor', relobj=[organization])
            messages.add_message(request, messages.INFO, _("Tag Template saved successfully"))
            return redirect(reverse('sga:editor', kwargs={'org_pk': org_pk}))
        else:
            clean_canvas_editor = False
    else:
        finstance = request.POST['instance'] if 'instance' in request.POST else None
        if finstance:
            finstance = get_object_or_404(TemplateSGA, pk=finstance)
        sgaform = EditorForm(instance=finstance)

    context = {
        'laboratory': None,
        "form": SGAEditorForm(),
        "generalform": sgaform,
        "warningwords": WarningWord.objects.all(),
        'instance': finstance,
        'templates': TemplateSGA.objects.filter(creator=request.user),
        'clean_canvas_editor': clean_canvas_editor,
        'form_url': reverse('sga:editor', kwargs={'org_pk': org_pk}),
        'org_pk': org_pk
    }
    return render(request, 'template_editor.html', context)


# SGA Label Creator
# Page
@login_required
def get_step(step):
    if step is None:
        step = 0
    try:
        step = int(step)
        if step not in [0, 1, 2]:
            step = 0
    except ValueError:
        step = 0
    return step


# SGA Label Information Page
def clean_json_text(text):
    return json.dumps(text)[1:-1]


@login_required
@permission_required('sga.add_personaltemplatesga')
def create_personal_template(request, org_pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    user = request.user
    personal_templates = PersonalTemplateSGA.objects.filter(user=user)
    filter = Q(community_share=True) | Q(creator=user)
    sga_templates = TemplateSGA.objects.filter(filter)
    context = {"personal_templates": personal_templates, 'sga_templates': sga_templates,
               "form": PersonalTemplateForm(user=request.user), 'org_pk': org_pk}

    if request.method == 'POST':
        form = PersonalSGAForm(request.POST)
        label_form = LabelForm(request.POST)
        builder_information_form = BuilderInformationForm(request.POST)

        if form.is_valid() and builder_information_form.is_valid() and label_form.is_valid():
            instance = form.save(commit=False)
            instance.user = user
            logo_upload_id = form.cleaned_data['logo_upload_id']

            if logo_upload_id:
                tmpupload = get_object_or_404(ChunkedUpload, upload_id=logo_upload_id)
                instance.logo = tmpupload.get_uploaded_file()

            builder_info = builder_information_form.save(commit=False)
            builder_info.user = user
            builder_info.save()
            label = label_form.save(commit=False)
            label.builderInformation = builder_info
            label.save()
            instance.label = label
            instance.save()
            return redirect(reverse('sga:add_personal', kwargs={'org_pk': org_pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'laboratory': None,
                'form': SGAEditorForm(),
                'warningwords': WarningWord.objects.all(),
                'generalform': PersonalForm(request.POST, user=user),
                'form_url': reverse('sga:add_personal', kwargs={'org_pk': org_pk}),
                'org_pk': org_pk
            }
            return render(request, 'template.html', context)

    return render(request, 'personal_template.html', context)

@login_required
@permission_required('sga.change_personaltemplatesga')
def edit_personal_template(request, org_pk, pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    personaltemplateSGA = get_object_or_404(PersonalTemplateSGA, pk=pk)
    user = request.user

    if request.method == 'POST':

        form = PersonalSGAForm(request.POST, instance=personaltemplateSGA)
        label_form = LabelForm(request.POST, instance=personaltemplateSGA.label)
        builder_information_form = BuilderInformationForm(request.POST, instance=personaltemplateSGA.label.builderInformation)

        if form.is_valid() and builder_information_form.is_valid() and label_form.is_valid():
            instance = form.save(commit=False)
            upload_id = form.cleaned_data['logo_upload_id']

            if upload_id:
                tmpupload = get_object_or_404(ChunkedUpload, upload_id=upload_id)
                instance.logo = tmpupload.get_uploaded_file()

            instance.save()
            builder_information_form.save()
            label_form.save()

            return redirect(reverse('sga:add_personal', kwargs={'org_pk': org_pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'laboratory': None,
                'form': SGAEditorForm(),
                'warningwords': WarningWord.objects.all(),
                'generalform': PersonalForm(request.POST, user=user),
                'form_url': reverse('sga:add_personal', kwargs={'org_pk': org_pk}),
                'org_pk': org_pk
            }
            return render(request, 'template_edit.html', context)

    initial = {'name': personaltemplateSGA.name, 'template': personaltemplateSGA.template,
               'barcode': personaltemplateSGA.barcotesthtml.htmlde, 'json_representation': personaltemplateSGA.json_representation}

    if personaltemplateSGA.label:
        bi_info = personaltemplateSGA.label.builderInformation
        initial.update({'substance': personaltemplateSGA.label.substance })

        if bi_info:
            initial.update({'company_name': bi_info.name,
                            'phone': bi_info.phone,
                            'address': bi_info.address,
                            'commercial_information': bi_info.commercial_information})

    context={
        'warningwords': WarningWord.objects.all(),
        'form': SGAEditorForm,
        "instance": personaltemplateSGA,
        "generalform": PersonalForm(user=user, initial=initial),
        'org_pk': org_pk
    }
    return render(request, 'template_edit.html', context)


@login_required
@permission_required('sga.delete_personaltemplatesga')
def delete_sgalabel(request, org_pk, pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    template = get_object_or_404(PersonalTemplateSGA, pk=pk)
    if template.user == request.user:
        template.delete()
        messages.success(request, _("SGA label was deleted successfully"))
    else:
        messages.error(request, _("Error, user is not creator label"))
    return redirect(reverse('sga:add_personal', kwargs={'org_pk': org_pk}))

# FIXME: Delete
@login_required
def get_preview(request, org_pk, pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    template = get_object_or_404(PersonalTemplateSGA, pk=pk)
    return JsonResponse({'svgString': template.json_representation})


@login_required
def create_recipient(request, org_pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    form = RecipientSizeForm()
    if request.method == 'POST':
        form = RecipientSizeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('The Recipient size saved successfully'))
            return redirect('sga:add_recipient_size')
        else:
            return redirect('sga:add_recipient_size')
    return render(request, 'add_recipient_size.html', context={'form': form, 'org_pk': org_pk})

@login_required
@permission_required('sga.change_personaltemplate')
def create_sgalabel(request, org_pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    if request.method == "POST":
        form = SGALabelForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.json_representation = form.cleaned_data['template'].json_representation
            label = Label.objects.create()
            instance.label = label
            instance.save()
            return redirect(reverse("sga:sgalabel_step_one", kwargs={'pk': instance.pk, 'org_pk': org_pk}))
        else:
            messages.error(request, _("Form is invalid"))

@login_required
@permission_required('sga.change_personaltemplate')
def sgalabel_step_one(request, org_pk, pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    sgalabel = get_object_or_404(PersonalTemplateSGA, pk=pk)
    builderinformation = sgalabel.label.builderInformation
    sustance = sgalabel.label.substance
    complement = None
    if sustance:
        complement = SGAComplement.objects.filter(substance=sgalabel.label.substance).first()

    complementsga_form = SGALabelComplementsForm(instance=complement, org_pk=org_pk)
    sgabuilderinfo_form = SGALabelBuilderInformationForm(user=request.user, instance=builderinformation,
                                                         initial={'company': builderinformation.pk if builderinformation else None})
    personal_form = PersonalSGAAddForm(instance=sgalabel)


    if request.method == "POST":
        complementsga_form = SGALabelComplementsForm(request.POST, instance=complement, org_pk=org_pk)
        sgabuilderinfo_form = SGALabelBuilderInformationForm(request.POST, user=request.user, instance=builderinformation)
        personal_form = PersonalSGAAddForm(request.POST, request.FILES, instance=sgalabel)

        complementsga_form_ok = complementsga_form.is_valid()
        sgabuilderinfo_form_ok = sgabuilderinfo_form.is_valid()
        personal_form_ok = personal_form.is_valid()

        if complementsga_form_ok:
            complementsga_form.save()
            sgalabel.label.substance = complementsga_form.cleaned_data['substance']
            sgalabel.label.save()
        if sgabuilderinfo_form_ok:
            instance = sgabuilderinfo_form.save()
            instance.user = request.user
            instance.save()
            if sgalabel.label.builderInformation is None:
                sgalabel.label.builderInformation = instance
                sgalabel.label.save()
        if personal_form_ok:
            personal_form.save()

        if complementsga_form_ok and sgabuilderinfo_form_ok and personal_form_ok:
            return redirect(reverse("sga:sgalabel_step_two", kwargs={'pk': sgalabel.pk, 'org_pk': org_pk}))

    context = {
        'sgalabel': sgalabel,
        'complementsga_form': complementsga_form,
        'builderinformationform': sgabuilderinfo_form,
        'pesonalform': personal_form,
        'org_pk': org_pk
    }

    return render(request, 'sgalabel/step_one.html', context=context)

@login_required
@permission_required('sga.change_personaltemplate')
def sgalabel_step_two(request, org_pk, pk):
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    sgalabel = get_object_or_404(PersonalTemplateSGA, pk=pk)
    substance = sgalabel.label.substance
    complement = SGAComplement.objects.filter(substance=substance).first()

    if request.method == 'POST':
        form = PersonalSGAForm(request.POST, instance=sgalabel)
        if form.is_valid():
            form.save()
            return redirect(reverse('sga:add_personal', args=(org_pk, )))

    context = {
        'sgalabel': sgalabel,
        'complement': complement,
        'editorform': PersonalSGAForm(instance=sgalabel),
        'org_pk': org_pk
    }

    return render(request, 'sgalabel/step_two.html', context=context)


def get_sgacomplement_by_substance(request, org_pk, pk):

    substance = get_object_or_404(Substance, pk=pk)
    complement = SGAComplement.objects.filter(substance =substance)
    if complement.exists():
        data = SGAComplementSerializer(complement.first()).data
    else:
        data = {}
    return JsonResponse(data)

def get_company(request, org_pk, pk):
    builder_info = get_object_or_404(BuilderInformation, pk=pk)
    data = BuilderInformationSerializer(builder_info).data
    return JsonResponse(data)

@login_required
@permission_required('sga.view_builderinformation')
def get_recipient_size(request, org_pk, pk):
    recipient_size = get_object_or_404(RecipientSize, pk=pk)
    data = RecipientSizeSerializer(recipient_size).data
    return JsonResponse(data)


@login_required
def get_barcode_from_number(request, org_pk, code):
    context={ "org_pk": org_pk }
    organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    response = HttpResponse(content_type='image/svg+xml')
    Code128(code,  writer=SVGWriter()).write(response)
    return response

@login_required
@permission_required('sga.view_builderinformation')
def get_companies(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    company = BuilderInformation.objects.filter(user=request.user, organization=organization)
    return render(request,'list_company.html', context={'companies':company, 'org_pk': org_pk})

@login_required
@permission_required('sga.add_builderinformation')
def create_company(request, org_pk):
    form = CompanyForm(user=request.user)
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    if request.method=='POST':
        form= CompanyForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organization = organization
            obj.save()
            return redirect(reverse('sga:get_companies', kwargs={'org_pk': org_pk}))

    context={
        'form':form,
        'title':_('Create Company'),
        'url': reverse('sga:add_company', kwargs={'org_pk': org_pk}),
        'org_pk': org_pk
    }

    return render(request,'add_company.html', context=context)

@login_required
@permission_required('sga.change_builderinformation')
def edit_company(request, org_pk, pk):
    company = BuilderInformation.objects.filter(pk=pk).first()
    form = CompanyForm(instance=company)
    if request.method=='POST':
        form= CompanyForm(request.POST,instance=company)
        if form.is_valid():
            form.save()
            return redirect(reverse('sga:get_companies', kwargs={'org_pk': org_pk}))
    context={
        'form':form,
        'title': _('Edit Company'),
        'url': reverse('sga:edit_company', kwargs={'org_pk': org_pk, 'pk':pk}),
        'org_pk': org_pk
    }

    return render(request,'add_company.html', context=context)


@login_required
@permission_required('sga.delete_builderinformation')
def remove_company(request, org_pk, pk):
    if pk:
        company = BuilderInformation.objects.get(pk=pk)
        company.delete()
        return JsonResponse({'msg':_('The company is removed successfully'),'status':True})

    return JsonResponse({'msg': _('Error'), 'status':False})
