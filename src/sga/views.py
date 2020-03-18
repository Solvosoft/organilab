# Import functions of another modules
import os

from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _

from organilab import settings
from sga import utils_pictograms
from sga.forms import SGAEditorForm, RecipientInformationForm, EditorForm
from sga.models import TemplateSGA, RecipientSize, Substance
from .models import Substance, Component, RecipientSize, DangerIndication, PrudenceAdvice, Pictogram, WarningWord
from django.http import HttpResponse, HttpResponseNotFound, FileResponse, HttpResponseNotAllowed
from django.db.models.query_utils import Q
from django.template import Library
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import json
from django.contrib import messages
from weasyprint import HTML
from django.core.files import temp as tempfile
from django.views.decorators.http import require_http_methods
from .json2html import json2html
from django.core.files.storage import FileSystemStorage, Storage

register = Library()


@require_http_methods(["POST"])
def render_pdf_view(request):
    label_pk = request.POST.get("template_sga_pk", None)
    json_data = request.POST.get("json_data", None)
    global_info_recipient = request.session['global_info_recipient']
    html_data = json2html(json_data, global_info_recipient)
    response = html2pdf(html_data)
    return response


# Return html rendered in pdf o return a html
def html2pdf(json_data):
    file_name = "report.pdf"
    pdf_absolute_path = tempfile.gettempdir() + "/" + file_name
    HTML(string=json_data).write_pdf(pdf_absolute_path)
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


# SGA information
def information_creator(request):
    recipients = RecipientSize.objects.all()
    context = {
        'laboratory': None,
        'recipients': recipients,
    }
    if request.method == 'POST':
        form = RecipientInformationForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse('index_sga.html'))
        else:
            form = RecipientInformationForm()

    return render(request, 'information.html', context)


# SGA template visualize
def template(request):
    sgatemplates = TemplateSGA.objects.all()
    barcode_file_url = logo_file_url = False
    request.session['commercial_information'] = request.POST.get('commercial_information', '')
    if request.method == 'POST' and request.FILES.get('logo', False):
        logo = request.FILES['logo']
        fs_logo = FileSystemStorage()
        logo_filename = fs_logo.save(logo.name, logo)
        logo_file_url = fs_logo.url(logo_filename)
    if request.FILES.get('barcode', False):
        barcode = request.FILES['barcode']
        fs_barcode = FileSystemStorage()
        barcode_filename = fs_barcode.save(barcode.name, barcode)
        barcode_file_url = fs_barcode.url(barcode_filename)
    request.session['logo_file_url'] = logo_file_url
    request.session['barcode_file_url'] = barcode_file_url
    if request.method == 'POST':
        form = RecipientInformationForm(request.POST)
    else:
        form = None
    context = {
        'laboratory': None,
        'form': form,
        'sgatemplates': sgatemplates,
        'files': [logo_file_url, barcode_file_url]

    }
    return render(request, 'template.html', context)

# SGA editor
def editor(request):
    finstance = None
    if 'instance' in request.POST:
        finstance = get_object_or_404(TemplateSGA, pk=request.POST['instance'])
    if 'instance' in request.GET:
        finstance = get_object_or_404(TemplateSGA, pk=request.GET['instance'])
    sgaform = EditorForm(instance=finstance)
    if request.method == "POST":
        sgaform = EditorForm(request.POST, instance=finstance)
        if sgaform.is_valid():
            finstance = sgaform.save()
            messages.add_message(request, messages.INFO, _("Tag Template saved successfully"))

    context = {
        'laboratory': None,
        "form": SGAEditorForm(),
        "generalform": sgaform,
        "pictograms": Pictogram.objects.all(),
        "warningwords": WarningWord.objects.all(),
        'templateinstance': finstance,
        'templates': TemplateSGA.objects.all()
    }
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

def label_creator(request, step=0):
    step = get_step(step)
    context = {
        'laboratory': None,
    }
    form = None
    if step == 0 or step == 1:
        context['recipients'] = RecipientSize.objects.all()
        if request.method == 'POST':
            form = RecipientInformationForm(request.POST)
            if form.is_valid():
                step += 1
    if step == 1:
        if form is None:
            form = RecipientInformationForm()
        context.update({
            'sgatemplates': TemplateSGA.objects.all(),
            'form': form,
        })

    if step == 2:
        finstance = None
        if 'instance' in request.POST:
            finstance = get_object_or_404(TemplateSGA, pk=request.POST['instance'])
        if 'instance' in request.GET:
            finstance = get_object_or_404(TemplateSGA, pk=request.GET['instance'])
        sgaform = EditorForm(instance=finstance)
        if request.method == "POST":
            sgaform = EditorForm(request.POST, instance=finstance)
            if sgaform.is_valid():
                finstance = sgaform.save()
                messages.add_message(request, messages.INFO, _("Tag Template saved successfully"))

        context.update({
            "form": SGAEditorForm(),
            "generalform": sgaform,
            "pictograms": Pictogram.objects.all(),
            "warningwords": WarningWord.objects.all(),
            'templateinstance': finstance,
            'templates': TemplateSGA.objects.all()
        })

    context.update({'step': step,
                    'next_step': step + 1,
                    'prev_step': step - 1 if step > 0 else step})

    return render(request, 'label_creator.html', context)


# SGA Label Information Page
def clean_json_text(text):
    return json.dumps(text)[1:-1]


def show_editor_preview(request, pk):
    recipients = get_object_or_404(RecipientSize, pk=request.POST.get('recipients', ''))
    request.session['global_info_recipient'] = {'height_value': recipients.height, 'height_unit': recipients.height_unit,
                                                'width_value': recipients.width, 'width_unit': recipients.width_unit}
    substance = get_object_or_404(Substance, pk=request.POST.get('substance', ''))
    weight = -1
    warningword = "{{warningword}}"
    dangerindications = ''
    casnumber = ''
    pictograms = {}
    prudenceAdvice = ''
    for di in substance.danger_indications.all():
        if di.warning_words.weigth > weight:
            if di.warning_words.name == "Sin palabra de advertencia":
                warningword = ""
            else:
                warningword = di.warning_words.name
            weight = di.warning_words.weigth
        # get danger indications from substance here
        if di.description == "Sin indicación de peligro":
            dangerindications += ""
        else:
            if dangerindications == '':
                dangerindications += di.description
            else:
                dangerindications += ". " + di.description

        pictograms.update(dict([x.name, x] for x in di.pictograms.all()))

        for advice in di.prudence_advice.all():
            if prudenceAdvice != '':
                prudenceAdvice += ' '
            prudenceAdvice += advice.name
    for component in substance.components.all():
        if casnumber != '':
            casnumber += ' '
        casnumber += component.cas_number

    template_context = {
        '{{warningword}}': clean_json_text(warningword),
        '{{dangerindication}}': clean_json_text(dangerindications),
        '{{selername}}': clean_json_text(request.POST.get('name', '{{selername}}')),
        "{{selerphone}}": clean_json_text(request.POST.get('phone', "{{selerphone}}")),
        "{{seleraddress}}": clean_json_text(request.POST.get('address', '{{seleraddress}}')),
        "{{commercialinformation}}": clean_json_text(request.session['commercial_information']),
        "{{substancename}}": clean_json_text(substance.comercial_name),
        '{{casnumber}}': clean_json_text(casnumber),
        '{{prudenceadvice}}': clean_json_text(prudenceAdvice)
    }

    obj = get_object_or_404(TemplateSGA, pk=pk)
    representation = obj.json_representation
    for key, value in template_context.items():
        if value == 'Sin palabra de advertencia':
            value = " "
        representation = representation.replace(key, value)

    files = {'logo_url': request.session['logo_file_url'],
             'barcode_url': request.session['barcode_file_url']}

    representation = utils_pictograms.pic_selected(representation,
                                                   pictograms, files)

    context = {
        'object': representation,
        'preview': obj.preview
    }

    return JsonResponse(context)


def label_information(request):
    # Includes recipient search
    context = RecipientSize.objects.all()
    return render(request, 'label_information.html', {'recipients': context})


# SGA Label Template Page

def label_template(request):
    recipients = RecipientSize.objects.all()

    return render(request, 'label_template.html', {'recipients': recipients,
                                                   'laboratory': None
                                                   })


def get_sga_editor_options(request):
    content = {
        'warningword': list(WarningWord.objects.values('pk', 'name', 'weigth')),
        'dangerindication': list(DangerIndication.objects.values('pk', 'code', 'description')),
        'prudenceadvice': list(PrudenceAdvice.objects.values('pk', 'code', 'name'))}
    return JsonResponse(content, content_type='application/json')


# SGA Label Editor Page
def label_editor(request):
    return render(request, 'label_editor.html', {})


# SGA Search sustance with autocomplete
def search_autocomplete_sustance(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        # Contains the typed characters, is valid since the first character
        # Search Parameter: Comercial Name or CAS Number
        if any(c.isalpha() for c in q):
            search_qs = Substance.objects.filter(
                Q(comercial_name__icontains=q) | Q(synonymous__icontains=q))
        else:
            search_qs = Substance.objects.filter(
                components__cas_number__icontains=q)
        results = []
        for r in search_qs:
            results.append({'label': r.comercial_name +
                                     ' : ' + r.synonymous, 'value': r.id})
        if not results:
            results.append('No results')
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
