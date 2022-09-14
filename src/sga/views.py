# Import functions of another modules
import json

import cairosvg
from chunked_upload.models import ChunkedUpload
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core import serializers
from django.core.files import temp as tempfile
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Library
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from paypal.standard.forms import PayPalPaymentsForm
from weasyprint import HTML
from xhtml2pdf import pisa

from organilab import settings
from sga.forms import SGAEditorForm, EditorForm, SearchDangerIndicationForm, DonateForm, \
    PersonalForm, SubstanceForm, RecipientSizeForm, PersonalSGAForm, BuilderInformationForm, \
    LabelForm
from sga.models import TemplateSGA, Donation, PersonalTemplateSGA, Label
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
def index_sga(request):
    return render(request, 'index_sga.html', {})


# SGA template visualize
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
    if finstance:
        context.update({'width': finstance.recipient_size.width, 'height': finstance.recipient_size.height})

    return render(request, 'editor.html', context)


# SGA Label Creator Page
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
    context = {"personal_templates": personal_templates, 'sga_templates': sga_templates, "organilabcontext": organilabcontext}

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
               'barcode': personaltemplateSGA.barcode}

    if personaltemplateSGA.label:
        bi_info = personaltemplateSGA.label.builderInformation
        initial.update({'substance': personaltemplateSGA.label.substance,
            'commercial_information': personaltemplateSGA.label.commercial_information})

        if bi_info:
            initial.update({'company_name': bi_info.name,
                            'phone': bi_info.phone,
                            'address': bi_info.address})

    context={
        'warningwords': WarningWord.objects.all(),
        'form': SGAEditorForm,
        "instance": personaltemplateSGA,
        "width": personaltemplateSGA.template.recipient_size.width,
        "height": personaltemplateSGA.template.recipient_size.height,
        'organilabcontext': organilabcontext,
        "generalform": PersonalForm(user=user, initial=initial)
    }

    if personaltemplateSGA.logo:
        name = personaltemplateSGA.logo.name.split('/')
        if len(name) == 3:
            name = name[2]
            context.update({'logo_name': name})
    return render(request, 'template_edit.html', context)


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

@organilab_context_decorator
def get_prudence_advice(request,organilabcontext):
    pk = request.POST.get('pk', '')
    data = PrudenceAdvice.objects.get(pk=pk)
    return HttpResponse(data.name)

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