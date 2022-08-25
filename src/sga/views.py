# Import functions of another modules
from django.shortcuts import render, get_object_or_404,redirect
from django.utils.translation import ugettext_lazy as _
from django.core import serializers
from django.contrib.auth.decorators import login_required,permission_required
from organilab import settings
from sga import utils_pictograms
from sga.forms import SGAEditorForm, RecipientInformationForm, EditorForm, SearchDangerIndicationForm, DonateForm,PersonalForm,PersonalTemplatesForm
from sga.models import TemplateSGA, RecipientSize, Substance, Donation,PersonalTemplateSGA
from .models import Substance, RecipientSize, DangerIndication, PrudenceAdvice, Pictogram, WarningWord
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.db.models.query_utils import Q
from django.template import Library
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import json
from django.contrib import messages
from django.core.files import temp as tempfile
from django.views.decorators.http import require_http_methods
from .json2html import json2html
from django.core.files.storage import FileSystemStorage
from xhtml2pdf import pisa
from paypal.standard.forms import PayPalPaymentsForm
from weasyprint import HTML
from django.utils.decorators import method_decorator

register = Library()


@require_http_methods(["POST"])
def render_pdf_view(request):
    json_data = request.POST.get("json_data", None)

    global_info_recipient = request.session['global_info_recipient']
    html_data = json2html(json_data, global_info_recipient)
    response = generate_pdf(html_data) #html2pdf(html_data)
    return response

def render_user_pdf(request,pk):

    instance = get_object_or_404(PersonalTemplateSGA, pk=pk)
    json_data = instance.json_representation
    recipient=RecipientSize.objects.get(pk=instance.recipient_size.pk)
    global_info_recipient = {'height_value': recipient.height, 'height_unit': recipient.height_unit, 'width_value': recipient.width, 'width_unit': recipient.width_unit}
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


# SGA information
def information_creator(request):
    recipients = RecipientSize.objects.all()
    template= RecipientSize.objects.all()
    context = {
        'laboratory': None,
        'recipients': recipients,
        'templates': template,
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
    sgatemplates = TemplateSGA.objects.get(pk=request.POST.get('templates'))
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
    template_sizes=RecipientSize.objects.filter(templatesga__pk=sgatemplates.id)
    context = {
        'laboratory': None,
        'form': form,
        'sgatemplates': sgatemplates,
        'sizes': template_sizes,
        'barcode_file_url':  barcode_file_url,
        'logo_file_url': logo_file_url,
        'formselects': SGAEditorForm,
        'pictograms': Pictogram.objects.all(),
        'warningwords': WarningWord.objects.all()

    }
    return render(request, 'template.html', context)

def personal_templates(request):
    context={
        'pictograms': Pictogram.objects.all(),
        'warningwords': WarningWord.objects.all(),
        'formselects': SGAEditorForm

    }
    return render(request,'personal_template.html', context)

# SGA editor
def editor(request):
    finstance = None
    clean_canvas_editor = True
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
            return redirect('sga:editor')
        else:
            clean_canvas_editor = False

    context = {
        'laboratory': None,
        "form": SGAEditorForm(),
        "generalform": sgaform,
        "pictograms": Pictogram.objects.all(),
        "warningwords": WarningWord.objects.all(),
        'templateinstance': finstance,
        'templates': TemplateSGA.objects.all(),
        'clean_canvas_editor': clean_canvas_editor
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
    request.session['global_info_recipient'] = {'height_value': recipients.height,
                                                'height_unit': recipients.height_unit,
                                                'width_value': recipients.width, 'width_unit': recipients.width_unit}
    substance = get_object_or_404(Substance, pk=request.POST.get('substance', ''))
    weight = -1
    warningword = "{{warningword}}"
    dangerindications = 'Indicaciones de Peligro\n'
    casnumber = ''
    pictograms = {}
    prudenceAdvice = 'Consejos de Prudencia\n'

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
                dangerindications += di.description

        pictograms.update(dict([x.name, x] for x in di.pictograms.all()))

        for advice in di.prudence_advice.all():
            if prudenceAdvice != '':
                prudenceAdvice += ' '
            prudenceAdvice += advice.name
    for component in substance.components.all():
        if casnumber != '':
            casnumber += ' '
        casnumber += "CAS: "+component.cas_number
    template_context = {
        '{{warningword}}': clean_json_text(warningword),
        '{{dangerindication}}': clean_json_text(dangerindications),
        '{{selername}}': clean_json_text(request.POST.get('name', '{{selername}}')),
        "{{selerphone}}": clean_json_text(request.POST.get('phone', "{{selerphone}}")),
        "{{seleraddress}}": clean_json_text(request.POST.get('address', '{{seleraddress}}')),
        "{{commercialinformation}}": clean_json_text(request.session['commercial_information']),
        "{{substancename}}": clean_json_text(substance.comercial_name),
        "{{uipa}}": clean_json_text(substance.uipa_name),
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
    representation['objects'] = orderby_elements(representation['objects'])
    context = {
        'object': representation,
        'preview': obj.preview
    }

    return JsonResponse(context)


def orderby_elements(datalist):

    for i in range(len(datalist) - 1, 0, -1):
        for j in range(i):
            if datalist[j]['top'] > datalist[j + 1]['top']:
                aux = datalist[j]
                datalist[j] = datalist[j + 1]
                datalist[j + 1] = aux
    return datalist

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
def create_personal_template(request):
    user = request.user
    templates = PersonalTemplateSGA.objects.filter(user=user)
    context = {"templates": templates }
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            recipient=RecipientSize.objects.get(pk=form.cleaned_data['sizes'])
            personal = PersonalTemplateSGA(
                user=user,  name=form.cleaned_data['name'],
                json_representation=request.POST.get('json_representation',''),
                recipient_size=recipient
            )
            personal.save()
            return redirect('sga:add_personal')

    else:

        return render(request, 'personal_template.html', context)

def show_preview(request,pk):
    templates = PersonalTemplateSGA.objects.get(pk=pk)
    context = {"object": templates.json_representation}
    return JsonResponse(context)


@permission_required('sga.change_personaltemplatesga')
def edit_personal_template(request,pk):
    if request.method=='POST':
        form=PersonalTemplatesForm(request.POST)

        if form.is_valid():

            template = PersonalTemplateSGA.objects.get(pk=pk)
            template.name = form.cleaned_data['name']
            template.json_representation = form.cleaned_data['json_data']
            template.save()
            return redirect(reverse('sga:add_personal'))

    templates = PersonalTemplateSGA.objects.filter(pk=pk).first()
    context={
        'pictograms': Pictogram.objects.all(),
        'warningwords': WarningWord.objects.all(),
        'formselects': SGAEditorForm,
        "sgatemplates": templates,
    }
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

def get_prudence_advice(request):
    pk = request.POST.get('pk', '')
    data = PrudenceAdvice.objects.get(pk=pk)
    return HttpResponse(data.name)


def get_danger_indication(request):
    pk = request.POST.get('pk', '')
    data = DangerIndication.objects.get(pk=pk)
    return HttpResponse(data.description)

def getTemplates(request):
    pk = request.POST.get('pk', '')

    templates = TemplateSGA.objects.filter(recipient_size=pk)
    aux=[]
    for template in templates:
        aux.append({'id':template.pk, 'name':template.name})
    data=json.dumps(aux)
    return JsonResponse(data,safe=False)

@login_required
@permission_required('sga.delete_personaltemplatesga')
def delete_personal(request):
    templates = PersonalTemplateSGA.objects.filter(user=request.user)
    if request.is_ajax():
        pk = request.GET.get('pk', '')
        obj = PersonalTemplateSGA.objects.get(pk=pk)
        obj.delete()

    templates = serializers.serialize("json", templates)
    return JsonResponse(templates, safe=False)

def saveImages(img):
    fs_image = FileSystemStorage()
    image_filename = fs_image.save(img.name, img)
    path = fs_image.url(image_filename)
    return path

def get_files(request):
    data = []
    if request.is_ajax():
        if 'logo' in request.FILES:
            data.append(saveImages(request.FILES['logo']))
        if 'barcode' in request.FILES:
            data.append(saveImages(request.FILES['barcode']))

        return JsonResponse({'data': data})