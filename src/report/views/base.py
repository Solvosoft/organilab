from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext as _, get_language

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import check_user_access_kwargs_org_lab
from report.forms import TasksForm
from report.models import TaskReport, ObjectChangeLogReport, \
    ObjectChangeLogReportBuilder
from report import register
from django.utils import translation, timezone
from weasyprint import HTML
from io import BytesIO

from report.models import DocumentReportStatus
from report.utils import get_pdf_table_content, create_notification, get_report_name, \
    document_status, calc_duration, check_import_obj, get_pdf_log_change_table_content
from django_celery_results.models import TaskResult


def build_report(pk, absolute_uri):
    report = TaskReport.objects.get(pk=pk)
    translation.activate(report.language)
    start_time = now()
    record_total=0
    import_report = None

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

                    import_html = check_import_obj(report_obj['html'])
                    import_pdf = check_import_obj(f_pdf)

                    if import_html and import_pdf:
                        import_html(report) #GET DATASET AND COLUMNS
                        record_total = import_pdf(report, absolute_uri) #(ABSOLUTE URL MEDIA REQUIRED)
                        report.status = _('Generated')
            else:
                import_report = check_import_obj(report_obj[report.file_type])

                if import_report:
                    record_total = import_report(report)
                    report.status = _('Generated')

            t, tx = calc_duration(start_time, now())
            description = report.data['name']+"."+report.file_type+f" {_('created in')} {t} {tx} {_('with')} {record_total} {_('records')}"

            if import_report:
                document_status(report, description)
            report.save()


def base_pdf(report, uri):
    title = ''
    datalist = ""
    total = 0
    columns = 0
    if 'title' in report.data and report.data['title']:
        title = report.data['title']
    report_name = get_report_name(report)
    if report.type_report == "report_objectschanges":
        datalist = get_pdf_log_change_table_content(report)
        total = ObjectChangeLogReportBuilder.objects.\
            filter(report__task_report=report).count()

    else:
        datalist = get_pdf_table_content(report.table_content)
        total=len(report.table_content['dataset'])
        if total > 0:
            columns = len(report.table_content['dataset'][0])
    context = {
        'datalist': datalist,
        'user': report.created_by,
        'title': title if title else report_name,
        'datetime': timezone.now(),
        'size_sheet': 'b4 landscape' if columns > 8 else 'landscape'
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
    return total



@login_required
@permission_required('laboratory.do_report')
def create_request_by_report(request, org_pk, lab_pk):
    response = {'result': False}
    data = {'org_pk': org_pk, 'lab_pk': lab_pk}
    report_name_list = register.REPORT_FORMS.keys()
    status_code = 401
    reason = None

    if check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        if 'report_name' in request.GET and request.GET['report_name'] in report_name_list:
            type_report = register.REPORT_FORMS[request.GET['report_name']]

            if 'form' in type_report:
                import_form = check_import_obj(type_report['form'])

                if import_form:
                    form = import_form(request.GET)
                    status_code = 200

                    if form.is_valid():
                        data.update(form.cleaned_data)

                        task = TaskReport.objects.create(
                            created_by=request.user,
                            type_report=form.cleaned_data['report_name'],
                            status=_("On hold"),
                            file_type=form.cleaned_data['format'],
                            data=data,
                            language=get_language()
                        )

                        import_task = check_import_obj(type_report['task'])

                        if import_task:
                            task_celery=import_task.delay(task.pk, request.build_absolute_uri())
                            task_celery=task_celery.task_id

                            response['result'] = True
                            response.update({
                                'report': task.pk,
                                'celery_id': task_celery
                            })
                        else:
                            status_code = 401
                    else:
                        response.update({'form_errors': form.errors})

    if status_code != 200 or status_code != 201:
        reason = _("Report can't be processed, try again or contact administrator")
    response = JsonResponse(response, status=status_code, reason=reason)
    return response

@login_required
@permission_required('laboratory.do_report')
def download_report(request, org_pk, lab_pk):
    response = {'result': False}
    status_code = 200
    reason = None

    if check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):

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
                status_code = 401
    else:
        status_code = 401

    if status_code != 200 or status_code != 201:
        reason = _("Report can't be processed, try again or contact administrator")
    response = JsonResponse(response, status=status_code, reason=reason)
    return response


@login_required
@permission_required('laboratory.do_report')
def report_table(request, org_pk, lab_pk, pk):
    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404()
    task = get_object_or_404(TaskReport.objects.using(settings.READONLY_DATABASE),pk=pk)
    template_name = 'report/general_reports.html'
    content = {
        'table': task.table_content,
        'lab_pk': lab_pk,
        'org_pk': org_pk,
        'obj_task': task,
        'changelogreport': None
    }
    if task.type_report == "report_objectschanges":
        template_name= "report/log_change.html"
        content['changelogreport'] = ObjectChangeLogReport.objects.\
            filter(task_report=task)
    return render(request, template_name=template_name, context=content)


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

@login_required
@permission_required('laboratory.do_report')
def create_organization_request_by_report(request, org_pk):
    response = {'result': False}
    data = {'org_pk': org_pk}
    report_name_list = register.REPORT_FORMS.keys()
    status_code = 401
    reason = None
    organization = OrganizationStructure.objects.filter(pk=org_pk).first()

    if organization:
        if 'report_name' in request.GET and request.GET['report_name'] in report_name_list:
            type_report = register.REPORT_FORMS[request.GET['report_name']]

            if 'form' in type_report:
                import_form = check_import_obj(type_report['form'])

                if import_form:
                    form = import_form(request.GET, org_pk=org_pk)
                    status_code = 200

                    if form.is_valid():
                        data.update(form.cleaned_data)

                        task = TaskReport.objects.create(
                            created_by=request.user,
                            type_report=form.cleaned_data['report_name'],
                            status=_("On hold"),
                            file_type=form.cleaned_data['format'],
                            data=data,
                            language=get_language()
                        )

                        import_task = check_import_obj(type_report['task'])

                        if import_task:
                            task_celery=import_task.delay(task.pk, request.build_absolute_uri())
                            task_celery=task_celery.task_id

                            response['result'] = True
                            response.update({
                                'report': task.pk,
                                'celery_id': task_celery
                            })
                        else:
                            status_code = 401
                    else:
                        response.update({'form_errors': form.errors})

    if status_code != 200 or status_code != 201:
        reason = _("Report can't be processed, try again or contact administrator")
    response = JsonResponse(response, status=status_code, reason=reason)
    return response

@login_required
@permission_required('laboratory.do_report')
def download__organization_report(request, org_pk):
    response = {'result': False}
    status_code = 200
    reason = None
    organization = OrganizationStructure.objects.filter(pk=org_pk).first()

    if organization:

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
                                'url_file':reverse('report:report_organization_table', kwargs={
                                    'org_pk': org_pk,
                                    'pk':task.pk
                                }),
                                'type_report':task.file_type
                            })
                            create_notification(request.user, f"{task.data['name']} {_('On screen')}".capitalize() , reverse('report:report_organization_table',kwargs={"org_pk":org_pk,"pk":task.pk}))
                        else:
                            file_name = f"{task.data['name']}.{task.file_type}"
                            create_notification(request.user, file_name , task.file.url)
                            response.update({'url_file': task.file.url})
            else:
                status_code = 401
    else:
        status_code = 401

    if status_code != 200 or status_code != 201:
        reason = _("Report can't be processed, try again or contact administrator")
    response = JsonResponse(response, status=status_code, reason=reason)
    return response

@login_required
@permission_required('laboratory.do_report')
def report_organization_table(request, org_pk,pk):
    task = get_object_or_404(TaskReport.objects.using(settings.READONLY_DATABASE),pk=pk)
    template_name = 'report/general_reports.html'
    content = {
        'table': task.table_content,
        'org_pk': org_pk,
        'obj_task': task,
        'changelogreport': None
    }
    if task.type_report == "report_objectschanges":
        template_name= "report/log_change.html"
        content['changelogreport'] = ObjectChangeLogReport.objects.\
            filter(task_report=task)
    return render(request, template_name=template_name, context=content)

@login_required
@permission_required('laboratory.do_report')
def report_organization_table(request, org_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    task = get_object_or_404(TaskReport.objects.using(settings.READONLY_DATABASE),pk=pk)
    template_name = 'report/general_reports.html'
    content = {
        'table': task.table_content,
        'org_pk': org_pk,
        'obj_task': task,
        'changelogreport': None
    }
    if task.type_report == "report_objectschanges":
        template_name= "report/log_change.html"
        content['changelogreport'] = ObjectChangeLogReport.objects.\
            filter(task_report=task)
    return render(request, template_name=template_name, context=content)
