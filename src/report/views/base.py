from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import gettext as _, get_language

from report.forms import TasksForm
from report.models import TaskReport
from report import register
from django.utils import translation, timezone
from weasyprint import HTML
from io import BytesIO

from report.models import DocumentReportStatus
from report.utils import get_pdf_table_content, create_notification, save_request_data, get_report_name, \
    document_status, calc_duration
from django_celery_results.models import TaskResult


def build_report(pk, absolute_uri):
    report = TaskReport.objects.get(pk=pk)
    translation.activate(report.language)
    start_time = now()
    record_total=0
    if report.type_report in register.REPORT_FORMS:
        report_obj = register.REPORT_FORMS[report.type_report]
        if report.file_type in register.REPORT_FORMS[report.type_report]:

            description =_("Starting report creation")
            document_status(report, description)
            t, tx = calc_duration(start_time, now())
            description = _("Loading data to analyze in")+f" {t} {tx}"
            document_status(report, description)

            if report.file_type == 'pdf':
                if 'html' in report_obj:
                    f_pdf = report_obj[report.file_type]
                    import_string(report_obj['html'])(report) #GET DATASET AND COLUMNS
                    record_total=import_string(f_pdf)(report, absolute_uri) #(ABSOLUTE URL MEDIA REQUIRED)
                    report.status = _('Generated')
            else:
                record_total=import_string(report_obj[report.file_type])(report)
                report.status = _('Generated')
            t, tx = calc_duration(start_time, now())
            description = report.data['name']+"."+report.file_type+f" {_('created in')} {t} {tx} {_('with')} {record_total} {_('records')}"

            document_status(report, description)
            report.save()


def base_pdf(report, uri):
    title = ''
    if 'title' in report.data and report.data['title']:
        title = report.data['title']
    report_name = get_report_name(report)
    context = {
        'datalist': get_pdf_table_content(report.table_content),
        'user': report.creator,
        'title': title if title else report_name,
        'datetime': timezone.now(),
        'size_sheet': 'landscape'
    }

    html = render_to_string('report/base_report_pdf.html', context=context)
    file = BytesIO()
    HTML(string=html, base_url=uri, encoding='utf-8').write_pdf(file)
    file_name = f'{report_name}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return len(report.table_content['dataset'])



@login_required
@permission_required('laboratory.do_report')
def create_request_by_report(request, org_pk, lab_pk):
    response = {'result': False}
    report_name_list = register.REPORT_FORMS.keys()
    error_message = _("Report can't be processed, try again or contact administrator")

    if 'report_name' in request.GET and request.GET['report_name'] in report_name_list:
        type_report = register.REPORT_FORMS[request.GET['report_name']]

        if 'form' in type_report:
            import_form = import_string(type_report['form'])
            form = import_form(request.GET)

            if form.is_valid():
                format=form.cleaned_data['format']
                data = request.GET.copy()
                data['lab_pk'] = lab_pk
                save_request_data(form, data)

                task = TaskReport.objects.create(
                    creator=request.user,
                    type_report=form.cleaned_data['report_name'],
                    status=_("On hold"),
                    file_type=format,
                    data=data,
                    language=get_language()
                )

                method = import_string(type_report['task'])
                task_celery=method.delay(task.pk, request.build_absolute_uri())
                task_celery=task_celery.task_id

                response['result'] = True
                response.update({
                    'report': task.pk,
                    'celery_id': task_celery
                })
            else:
                response.update({'form_errors': form.errors})
        else:
            response['error_message'] = error_message
    else:
        response['error_message'] = error_message
    return JsonResponse(response)

@login_required
@permission_required('laboratory.do_report')
def download_report(request, lab_pk, org_pk):
    response = {'result': False}
    error_message = _("Report can't be processed, try again or contact administrator")

    if request.method == "GET":
        form = TasksForm(request.GET)

        if form.is_valid():
            task = TaskReport.objects.filter(pk=form.cleaned_data['taskreport']).first()
            result = TaskResult.objects.filter(task_id=form.cleaned_data['task']).first()
            if result:
                if task.status==_('Generated') and result.status=='SUCCESS':
                    task.status=_('Delivered')
                    task.save()
                    response['result'] = True
                    if task.file_type=='html':
                        response.update({
                            'url_file':reverse('report:report_table', kwargs={
                                'org_pk': org_pk,
                                'lab_pk':lab_pk,
                                'pk':task.pk
                            }),
                            'type_report':task.file_type
                        })
                        create_notification(request.user, f"{task.data['name']} {_('On screen')}".capitalize() , reverse('report:report_table',kwargs={"lab_pk":lab_pk,"org_pk":org_pk,"pk":task.pk}))
                    else:
                        file_name = f"{task.data['name']}.{task.file_type}"
                        create_notification(request.user, file_name , task.file.url)
                        response.update({'url_file': task.file.url})
        else:
            response['error_message'] = error_message
    return JsonResponse(response)

@login_required
@permission_required('laboratory.do_report')
def report_table(request, org_pk, lab_pk, pk):
    task = TaskReport.objects.filter(pk=pk).first()
    return render(request, template_name='report/general_reports.html', context={
        'table': task.table_content,
        'lab_pk': lab_pk,
        'org_pk': org_pk,
        'obj_task': task
    })


@login_required
@permission_required('laboratory.do_report')
def report_status(request, org_pk, lab_pk):
    end = False
    description=""

    if request.method == "GET":
        form = TasksForm(request.GET)

        if form.is_valid():
            result = TaskResult.objects.filter(task_id=form.cleaned_data['task'])

            if result.exists():
                end = result.first().status=='SUCCESS'

            status = DocumentReportStatus.objects.filter(report=form.cleaned_data['taskreport']).order_by('report_time')

            if status.exists():
                for text in status:
                    description += "<li>%s %s </li>"%(text.report_time.strftime("%m/%d/%Y, %H:%M:%S"), text.description)
    return JsonResponse({'end': end, 'text': description})