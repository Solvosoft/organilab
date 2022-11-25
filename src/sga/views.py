# Import functions of another modules
import json

import cairosvg
from barcode import Code128
from barcode.writer import SVGWriter
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files import temp as tempfile
from django.db.models import Max
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Library
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from djgentelella.models import ChunkedUpload
from paypal.standard.forms import PayPalPaymentsForm
from weasyprint import HTML
from xhtml2pdf import pisa

from organilab import settings
from sga.forms import SGAEditorForm, EditorForm, SearchDangerIndicationForm, DonateForm, \
    PersonalForm, SubstanceForm, RecipientSizeForm, PersonalSGAForm, BuilderInformationForm, \
    LabelForm, PersonalTemplateForm, PictogramForm, SGALabelForm, SGALabelComplementsForm, \
    SGALabelBuilderInformationForm, PersonalSGAAddForm, CompanyForm
from sga.models import SGAComplement, Substance
from sga.models import TemplateSGA, Donation, PersonalTemplateSGA, Label, Pictogram, BuilderInformation
from .api.serializers import SGAComplementSerializer, BuilderInformationSerializer
from .decorators import organilab_context_decorator
from .json2html import json2html
from .models import RecipientSize, DangerIndication, PrudenceAdvice, WarningWord

register = Library()


@require_http_methods(["POST"])
def render_pdf_view(request):
    json_data = request.POST.get("json_data", None)

    global_info_recipient = request.session['global_info_recipient']
    html_data = json2html(json_data, global_info_recipient)
    response = generate_pdf(html_data) #html2pdf(html_data)
    return response


def generate_pdf(json):
    """Generate pdf."""
    # Model data

    # Rendered
    pdf_absolute_path = tempfile.gettempdir() + "/x.pdf"
    result_file = open(pdf_absolute_path, "w+b")

    html = HTML(string=json)
    result = html.write_pdf(pdf_absolute_path)
    result_file.close()
    # Creating http response
    ''' response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=list_people.pdf'
    doc='''
    try:
        pdf = open(pdf_absolute_path, "rb")
        response = FileResponse(pdf, content_type='application/pdf')
    except IOError:
        return HttpResponseNotFound()
    response['Content-Disposition'] = 'attachment; filename=x.pdf'

    return response


# Return html rendered in pdf o return a html
def html2pdf(json_data):
    file_name = "report.pdf"
    pdf_absolute_path = tempfile.gettempdir() + "/" + file_name
    result_file = open(pdf_absolute_path, "w+b")
    pisa_status = pisa.CreatePDF(
        json_data,  # the HTML to convert
        dest=result_file)  # file handle to recieve result
    result_file.close()
    try:
        pdf = open(pdf_absolute_path, "rb")
        response = FileResponse(pdf, content_type='application/pdf')
    except IOError:
        return HttpResponseNotFound()
    response['Content-Disposition'] = 'attachment; filename=' + file_name

    return response


# SGA Home Page
@login_required
def index_sga(request):
    return render(request, 'index_sga.html', {})


# SGA template visualize
@login_required
@organilab_context_decorator
def template(request, organilabcontext):
    context = {
        'laboratory': None,
        'form': SGAEditorForm(),
        'warningwords': WarningWord.objects.all(),
        'generalform': PersonalForm(user=request.user),
        'organilabcontext': organilabcontext,
        'form_url': reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext})
    }
    return render(request, 'template.html', context)


# SGA editor
@login_required
@organilab_context_decorator
def editor(request, organilabcontext):
    finstance = None
    clean_canvas_editor = True
    if 'instance' in request.POST:
        finstance = get_object_or_404(TemplateSGA, pk=request.POST['instance'])
    if 'instance' in request.GET:
        finstance = get_object_or_404(TemplateSGA, pk=request.GET['instance'])

    if request.method == "POST":
        sgaform = EditorForm(request.POST, instance=finstance)
        if sgaform.is_valid():
            finstance = sgaform.save(commit=False)
            finstance.creator = request.user
            finstance.save()
            messages.add_message(request, messages.INFO, _("Tag Template saved successfully"))
            return redirect(reverse('sga:editor', kwargs={'organilabcontext': organilabcontext}))
        else:
            clean_canvas_editor = False
    else:
        sgaform = EditorForm(instance=finstance)

    context = {
        'laboratory': None,
        "form": SGAEditorForm(),
        "generalform": sgaform,
        "warningwords": WarningWord.objects.all(),
        'instance': finstance,
        'templates': TemplateSGA.objects.filter(creator=request.user),
        'clean_canvas_editor': clean_canvas_editor,
        'organilabcontext': organilabcontext,
        'form_url': reverse('sga:editor', kwargs={'organilabcontext': organilabcontext})
    }
    return render(request, 'editor.html', context)


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
def index_organilab(request):
    if request.method == "POST":
        form = SearchDangerIndicationForm(request.POST)

        if form.is_valid():
            hcodes_list = form.cleaned_data['codes']
            prudence_advices = set([y for x in hcodes_list for y in x.prudence_advice.all()])
            pictograms = set([y for x in hcodes_list for y in x.pictograms.all() if y.name != "Sin Pictograma"])
            warning_word = max(hcodes_list, key=lambda x: x.warning_words.weigth).warning_words
            return render(request, 'danger_indication_info.html', {'hcodes_list': hcodes_list,
                                                                   'prudence_advices': prudence_advices,
                                                                   'warning_word': warning_word,
                                                                   'pictograms': pictograms})

    else:
        form = SearchDangerIndicationForm()

    return render(request, 'index_organilab.html', {'form': form})

@login_required
@permission_required('sga.add_personaltemplatesga')
@organilab_context_decorator
def create_personal_template(request, organilabcontext):
    user = request.user
    personal_templates = PersonalTemplateSGA.objects.filter(user=user)
    filter = Q(community_share=True) | Q(creator=user)
    sga_templates = TemplateSGA.objects.filter(filter)
    context = {"personal_templates": personal_templates, 'sga_templates': sga_templates,
               "organilabcontext": organilabcontext, "form": PersonalTemplateForm(user=request.user)}

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
            return redirect(reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext,}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'laboratory': None,
                'form': SGAEditorForm(),
                'warningwords': WarningWord.objects.all(),
                'generalform': PersonalForm(request.POST, user=user),
                'form_url': reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext}),
                'organilabcontext': organilabcontext
            }
            return render(request, 'template.html', context)

    return render(request, 'personal_template.html', context)

@login_required
@permission_required('sga.change_personaltemplatesga')
@organilab_context_decorator
def edit_personal_template(request, organilabcontext, pk):
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

            return redirect(reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext,}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'laboratory': None,
                'form': SGAEditorForm(),
                'warningwords': WarningWord.objects.all(),
                'generalform': PersonalForm(request.POST, user=user),
                'form_url': reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext}),
                'organilabcontext': organilabcontext
            }
            return render(request, 'template_edit.html', context)

    initial = {'name': personaltemplateSGA.name, 'template': personaltemplateSGA.template,
               'barcode': personaltemplateSGA.barcode, 'json_representation': personaltemplateSGA.json_representation}

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
        'organilabcontext': organilabcontext,
        "generalform": PersonalForm(user=user, initial=initial)
    }
    return render(request, 'template_edit.html', context)

@login_required
def donate(request):
    pay = False

    if request.method == "POST":
        form = DonateForm(request.POST)
        if form.is_valid():
            donation = Donation(
                name=form.cleaned_data['name'], email=form.cleaned_data['email'],
                amount=form.cleaned_data['amount'], is_donator=form.cleaned_data['is_donator'],
                is_paid=False)
            donation.save()
            paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': form.cleaned_data['amount'],
                'item_name': _('Donate Organilab'),
                'invoice': str(donation.pk),
                'currency_code': 'USD',
                'notify_url': settings.MY_PAYPAL_HOST + reverse('paypal-ipn'),
                'return_url': settings.MY_PAYPAL_HOST + reverse('donate_success'),
                'cancel_return': settings.MY_PAYPAL_HOST + reverse('index'),
            }
            pay = True
            paypal_form = PayPalPaymentsForm(initial=paypal_dict)
            paypal_form.button_type = "donate"
        return render(
            request, 'donate_organilab.html', {'paypal_form': paypal_form, 'pay': pay, 'form':form})
    else:
        form = DonateForm()
        return render(
            request, 'donate_organilab.html', {'form': form, 'pay': pay})


def donate_success(request):
    messages.success(request, _("Your donation was completed successfully, thank you for support this project!"))
    return HttpResponseRedirect(reverse('donate'))

@login_required
@organilab_context_decorator
def get_prudence_advice(request,organilabcontext):
    pk = request.POST.get('pk', '')
    data = PrudenceAdvice.objects.get(pk=pk)
    return HttpResponse(data.name)

@login_required
@organilab_context_decorator
def get_danger_indication(request,organilabcontext):
    pk = request.POST.get('pk', '')
    data = DangerIndication.objects.get(pk=pk)
    return HttpResponse(data.description)


@login_required
@permission_required('sga.delete_personaltemplatesga')
@organilab_context_decorator
def delete_sgalabel(request, organilabcontext, pk):
    template = get_object_or_404(PersonalTemplateSGA, pk=pk)
    if template.user == request.user:
        template.delete()
        messages.success(request, _("SGA label was deleted successfully"))
    else:
        messages.error(request, _("Error, user is not creator label"))
    return redirect(reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext}))

@login_required
@organilab_context_decorator
def get_recipient_size(request, organilabcontext, is_template, pk):
    response = {}

    if int(is_template):
        template = TemplateSGA.objects.filter(pk=pk)
        if template.exists():
            template = template.first()
            response.update({
                'size': {
                    'width': template.recipient_size.width,
                    'height': template.recipient_size.height},
                'svg_content': template.json_representation
            })
    else:
        recipient = get_object_or_404(RecipientSize, pk=pk)
        response.update({
            'size': {
                'width': recipient.width,
                'height': recipient.height}
        })
    return JsonResponse(response)


@login_required
@organilab_context_decorator
def get_preview(request, organilabcontext, pk):
    template = get_object_or_404(PersonalTemplateSGA, pk=pk)
    return JsonResponse({'svgString': template.json_representation})

@login_required
@permission_required('laboratory.change_object')
@organilab_context_decorator
def create_substance(request,organilabcontext):
    form=SubstanceForm()
    if request.method == 'POST':
        form =SubstanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,_('The substance saved successfully'))
            return redirect(reverse('sga:add_substance', kwargs={'organilabcontext': organilabcontext}))
        else:
            return redirect(reverse('sga:add_substance', kwargs={'organilabcontext': organilabcontext}))
    return render(request, 'add_substance.html', context={'form':form})

@login_required
def create_recipient(request):
    form=RecipientSizeForm()
    if request.method == 'POST':
        form =RecipientSizeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,_('The Recipient size saved successfully'))
            return redirect('sga:add_recipient_size')
        else:
            return redirect('sga:add_recipient_size')
    return render(request, 'add_recipient_size.html', context={'form':form})


@login_required
def get_svgexport(request, is_pdf, pk):
    personalsga = get_object_or_404(PersonalTemplateSGA, pk=pk)
    svg = personalsga.json_representation
    type = "png"

    try:
        if int(is_pdf):
            file = cairosvg.svg2pdf(svg)
            type = "pdf"
        else:
           file = cairosvg.svg2png(svg)
           response = HttpResponse(file, content_type='application/'+type)
    except IOError:
        return HttpResponseNotFound()
    response['Content-Disposition'] = 'attachment; filename=labelsga.'+type

    return response

@login_required
@permission_required('sga.view_pictogram')
def get_pictograms(request):
    pictograms = Pictogram.objects.all()
    return render(request, 'list_pictograms.html', context={'pictograms':pictograms})

@login_required
@permission_required('sga.add_pictogram')
def add_pictogram(request):

    if request.method=='POST':
        form = PictogramForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            upload_id = form.cleaned_data['image_upload']
            last_id=Pictogram.objects.all().aggregate(largest=Max('id_pictogram'))['largest']
            if last_id==None:
                last_id=0
            if upload_id:
                tmpupload = get_object_or_404(ChunkedUpload, upload_id=upload_id)
                instance.image = tmpupload.get_uploaded_file()
            instance.id_pictogram=last_id+1
            instance.save()

            return redirect(reverse('sga:pictograms_list'))
    context= {
        'url': reverse('sga:add_pictograms'),
        'form': PictogramForm(),
        'title': _('Create pictogram'),
        'button_text': _('Add')
    }
    return render(request, 'add_pictograms.html', context=context)
@login_required
@permission_required('sga.change_pictogram')
def update_pictogram(request,id_pictogram):
    instance = get_object_or_404(Pictogram,id_pictogram=id_pictogram)
    form = None
    if instance:
        form = PictogramForm(instance=instance)

        if request.method=='POST':
            form = PictogramForm(request.POST, instance=instance)

            if form.is_valid():
                instance = form.save(commit=False)
                upload_id = form.cleaned_data['image_upload']

                if upload_id:
                    tmpupload = get_object_or_404(ChunkedUpload, upload_id=upload_id)
                    instance.image = tmpupload.get_uploaded_file()

                instance.save()
                return redirect(reverse('sga:pictograms_list'))
    context= {
        'url': reverse('sga:update_pictogram',kwargs={'id_pictogram':id_pictogram}),
        'form': form,
        'title': _('Update pictogram'),
        'button_text': _('Edit')
    }
    return render(request, 'add_pictograms.html', context=context)


def create_sgalabel(request, organilabcontext):

    if request.method == "POST":
        form = SGALabelForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.json_representation = form.cleaned_data['template'].json_representation
            label = Label.objects.create()
            instance.label = label
            instance.save()
            return redirect(reverse("sga:sgalabel_step_one", kwargs={'organilabcontext':organilabcontext,
                                                                     'pk': instance.pk}))
        else:
            messages.error(request, _("Form is invalid"))


def sgalabel_step_one(request, organilabcontext, pk):
    sgalabel = get_object_or_404(PersonalTemplateSGA, pk=pk)
    builderinformation = sgalabel.label.builderInformation
    sustance = sgalabel.label.substance
    complement = None
    if sustance:
        complement = SGAComplement.objects.filter(substance=sgalabel.label.substance).first()

    complementsga_form = SGALabelComplementsForm(instance=complement)
    sgabuilderinfo_form = SGALabelBuilderInformationForm(user=request.user, instance=builderinformation,
                                                         initial={'company': builderinformation.pk})
    personal_form = PersonalSGAAddForm(instance=sgalabel)


    if request.method == "POST":
        complementsga_form = SGALabelComplementsForm(request.POST, instance=complement)
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
            return redirect(reverse("sga:sgalabel_step_two", kwargs={'organilabcontext':organilabcontext,
                                                                     'pk': sgalabel.pk}))

    context = {
        'sgalabel': sgalabel,
        'organilabcontext': organilabcontext,
        'complementsga_form': complementsga_form,
        'builderinformationform': sgabuilderinfo_form,
        'pesonalform': personal_form
    }

    return render(request, 'sgalabel/step_one.html', context=context)

def sgalabel_step_two(request, organilabcontext, pk):
    sgalabel = get_object_or_404(PersonalTemplateSGA, pk=pk)
    substance = sgalabel.label.substance
    complement = SGAComplement.objects.filter(substance=substance).first()

    if request.method == 'POST':
        form = EditorForm(request.POST, instance=sgalabel.template)
        if form.is_valid():
            instance = form.save()
            instance.creator = request.user
            instance.save()
            return redirect(
                reverse('sga:add_personal', args=('laboratory',) )
            )

    context = {
        'sgalabel': sgalabel,
        'organilabcontext': organilabcontext,
        'complement': complement,
        'form': SGAEditorForm(),
        'editorform': EditorForm()
    }

    return render(request, 'sgalabel/step_two.html', context=context)


def get_sgacomplement_by_substance(request, pk):
    substance = get_object_or_404(Substance, pk=pk)
    complement = SGAComplement.objects.filter(substance =substance)
    if complement.exists():
        data = SGAComplementSerializer(complement.first()).data
    else:
        data = {}
    return JsonResponse(data)

def get_company(request, pk):
    builder_info = get_object_or_404(BuilderInformation, pk=pk)
    data = BuilderInformationSerializer(builder_info).data
    return JsonResponse(data)

@login_required
def get_barcode_from_number(request, code):
    response = HttpResponse(content_type='image/svg+xml')
    Code128(code,  writer=SVGWriter()).write(response)
    return response

@login_required
@permission_required('sga.view_builderinformation')
def get_companies(request):
    company = BuilderInformation.objects.filter(user=request.user)
    return render(request,'list_company.html', context={'companies':company})

@login_required
@permission_required('sga.add_builderinformation')
def create_company(request):
    form = CompanyForm(user=request.user)
    if request.method=='POST':
        form= CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('sga:get_companies'))

    context={
        'form':form,
        'title':_('Create Company'),
        'url': reverse('sga:add_company')
    }

    return render(request,'add_company.html', context=context)

@login_required
@permission_required('sga.change_builderinformation')
def edit_company(request,pk):
    company = BuilderInformation.objects.filter(pk=pk).first()
    form = CompanyForm(instance=company)
    if request.method=='POST':
        form= CompanyForm(request.POST,instance=company)
        if form.is_valid():
            form.save()
            return redirect(reverse('sga:get_companies'))
    context={
        'form':form,
        'title': _('Edit Company'),
        'url': reverse('sga:edit_company', kwargs={'pk':pk})
    }

    return render(request,'add_company.html', context=context)
@login_required
@permission_required('sga.delete_builderinformation')
def remove_company(request,pk):
    if pk:
        company = BuilderInformation.objects.get(pk=pk)
        company.delete()
        return JsonResponse({'msg':_('The company is removed successfully'),'status':True})

    return JsonResponse({'msg': _('Error'), 'status':False})
