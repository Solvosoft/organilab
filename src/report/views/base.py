from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import gettext as _, get_language

from laboratory.forms import TasksForm
from report.models import TaskReport
from report import register
from django.utils import translation, timezone
from weasyprint import HTML
from io import BytesIO

from report.models import DocumentReportStatus
from report.utils import get_pdf_table_content, create_notification, save_request_data, get_report_name


def build_report(pk, absolute_uri):
    report = TaskReport.objects.get(pk=pk)
    translation.activate(report.language)

    if report.type_report in register.REPORT_FORMS:
        report_obj = register.REPORT_FORMS[report.type_report]
        if report.file_type in register.REPORT_FORMS[report.type_report]:
            DocumentReportStatus.objects.create(
                report=report,
                description="Iniciando creacíon del reporte %s" % (now().strftime("%m/%d/%Y, %H:%M:%S"))
            )
            if report.file_type == 'pdf':
                if 'html' in report_obj:
                    f_pdf = report_obj[report.file_type]
                    import_string(report_obj['html'])(report) #GET DATASET AND COLUMNS
                    import_string(f_pdf)(report, absolute_uri) #(ABSOLUTE URL MEDIA REQUIRED)
                    report.status = _('Generated')
            else:
                import_string(report_obj[report.file_type])(report)
                report.status = _('Generated')
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


@login_required
@permission_required('laboratory.do_report')
def create_request_by_report(request, lab_pk):
    response = {'result': False}

    if 'report_name' in request.GET:
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
    return JsonResponse(response)

@login_required
@permission_required('laboratory.do_report')
def download_report(request, lab_pk, org_pk):
    from django_celery_results.models import TaskResult
    form = TasksForm(request.GET)
    response = {'result': False}

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
                            'lab_pk':lab_pk,
                            'pk':task.pk,
                            'org_pk':org_pk
                        }),
                        'type_report':task.file_type
                    })
                    create_notification(request.user, _("A list of")+" "+task.data['name'], reverse('report:report_table',kwargs={"lab_pk":lab_pk,"org_pk":org_pk,"pk":task.pk}))
                else:
                    file_name = f"{task.data['name']}.{task.file_type}"
                    create_notification(request.user, file_name , task.file.url)
                    response.update({'url_file': task.file.url})
    return JsonResponse(response)

@login_required
@permission_required('laboratory.do_report')
def report_table(request, lab_pk, pk, org_pk):
    task = TaskReport.objects.filter(pk=pk).first()
    return render(request, template_name='report/general_reports.html', context={
        'table': task.table_content,
        'lab_pk': lab_pk,
        'org_pk': org_pk,
        'obj_task': task
    })


@login_required
def download_pdf_status(request):
    from django_celery_results.models import TaskResult

    result = TaskResult.objects.filter(task_id=request.GET.get('task')).first()
    if result:
        end = result.status=='SUCCESS'
    else:
        end = False
    status = DocumentReportStatus.objects.filter(report__pk=request.GET.get('pk')).order_by('report_time')
    description = ''
    for text in status:
        description += "%s %s %s <br>"%(
            text.report_time.strftime("%m/%d/%Y, %H:%M:%S"),
            text.description, result.status)
    return JsonResponse({'end': end, 'text': description})