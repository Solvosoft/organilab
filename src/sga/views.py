"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
"""

# Import functions of another modules
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from sga.forms import SGAEditorForm, RecipientInformationForm, EditorForm
from sga.models import TemplateSGA, RecipientSize
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

register = Library()


@require_http_methods(["POST"])
def render_pdf_view(request):
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
    if request.method == 'POST':
        form = RecipientInformationForm(request.POST)
    else:
        form = None
    context = {
        'laboratory': None,
        'form': form,
        'sgatemplates': sgatemplates,

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

    weigth = 10000
    warningword = "{{warningword}}"
    dangerindications = ''
    casnumber = ''
    pictograms = []
    prudenceAdvice = ''
    for di in substance.danger_indications.all():
        if di.warning_words.weigth < weigth:
            warningword = di.warning_words.name
        if dangerindications != '':
            dangerindications += '\n'
        dangerindications += di.description
        pictograms += list(di.pictograms.all())

        for advice in di.prudence_advice.all():
            if prudenceAdvice != '':
                prudenceAdvice += '\n'
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
        "{{commercialinformation}}": clean_json_text(request.POST.get('name', '{{commercialinformation}}')),
        '{{casnumber}}': clean_json_text(casnumber),
        '{{prudenceadvice}}': clean_json_text(prudenceAdvice)

    }

    obj = get_object_or_404(TemplateSGA, pk=pk)

    representation = obj.json_representation
    for key, value in template_context.items():
        representation = representation.replace(key, value)

    for image in pictograms:
        representation = representation.replace(
            "/static/sga/img/pictograms/example.gif",
            "/static/sga/img/pictograms/" + image.name,
            1)
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
        'prudenceadvice': list(PrudenceAdvice.objects.values('pk', 'code', 'name'))
    }

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


# SGA Obtain substance information


# TODO not to pep8 standard
def getSubstanceInformation(request):
    substanceInformation = {}
    signalWordSubstance = ''
    dangerIndicationsDescriptionSubstance = []
    dangerIndicationsCodeSubstance = []
    prudenceAdvicesNameSubstance = []
    prudenceAdvicesCodeSubstance = []
    pictogramasNameSubstance = []
    components = []
    componentsCasNumbers = []
    if request.is_ajax():
        dangerIndications = DangerIndication.objects.filter(sustance__in=request.GET['substance_id'])
        # ---------------------------------------------------------------------
        # ----------------------------Signal Word------------------------------
        for dangerIndication in dangerIndications:
            # Set priority to Danger
            if str(signalWordSubstance) == 'Peligro':
                break
            else:
                # Set priority to Warning
                if (str(dangerIndication.warning_words) == 'Sin palabra de advertencia' and str(
                        signalWordSubstance) == 'atención'):
                    pass
                else:
                    signalWordSubstance = dangerIndication.warning_words
        substanceInformation['signalWord'] = str(signalWordSubstance)
        # ---------------------------------------------------------------------
        # --------------------------Danger Indications-------------------------
        for dangerIndication in dangerIndications:
            if str(dangerIndication.code) in dangerIndicationsCodeSubstance:
                pass
            # Special cases
            # H410 > H400
            elif 'H410' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H400':
                pass
            elif 'H400' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H410':
                index = dangerIndicationsCodeSubstance.index('H400')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H411 > H401
            elif 'H411' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H401':
                pass
            elif 'H401' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H411':
                index = dangerIndicationsCodeSubstance.index('H401')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H412 > H402
            elif 'H412' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H402':
                pass
            elif 'H402' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H412':
                index = dangerIndicationsCodeSubstance.index('H402')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H314 > H318
            elif 'H314' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H318':
                pass
            elif 'H318' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H314':
                index = dangerIndicationsCodeSubstance.index('H318')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            else:
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
        substanceInformation['DangerIndications'] = dangerIndicationsDescriptionSubstance
        # ---------------------------------------------------------------------
        # ------------------Prudence Advices and Pictograms--------------------
        for dangerIndicationCode in dangerIndicationsCodeSubstance:
            prudenceAdvices = PrudenceAdvice.objects.filter(dangerindication=dangerIndicationCode)
            pictograms = Pictogram.objects.filter(dangerindication=dangerIndicationCode)
            if prudenceAdvices:
                for prudenceAdvice in prudenceAdvices:
                    if str(prudenceAdvice.code) in prudenceAdvicesCodeSubstance:
                        pass
                    else:
                        prudenceAdvicesNameSubstance.append(str(prudenceAdvice.name))
                        dangerIndicationsCodeSubstance.append(str(prudenceAdvice.code))
            if pictograms:
                for pictogram in pictograms:
                    if str(pictogram.name) in pictogramasNameSubstance:
                        pass
                    else:
                        if str(pictogram.name) != 'Sin Pictograma':
                            pictogramasNameSubstance.append(str(pictogram.name))
        substanceInformation['PrudenceAdvices'] = prudenceAdvicesNameSubstance
        substanceInformation['Pictograms'] = pictogramasNameSubstance
        # ---------------------------------------------------------------------
        # --------------------------Cas Numbers--------------------------------
        components = Component.objects.filter(sustance=request.GET['substance_id'])
        if components:
            for component in components:
                if str(component.cas_number) in componentsCasNumbers:
                    pass
                else:
                    componentsCasNumbers.append(str(component.cas_number))
        substanceInformation['CasNumbers'] = componentsCasNumbers
        # ---------------------------------------------------------------------
        # print(substanceInformation)
        data = json.dumps(substanceInformation)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
