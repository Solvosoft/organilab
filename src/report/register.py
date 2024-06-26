REPORT_FORMS ={
    'reactive_precursor': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateReportForm',
        'html': 'report.views.objects.report_reactive_precursor_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.objects.report_reactive_precursor_doc',
        'xlsx': 'report.views.objects.report_reactive_precursor_doc',
        'ods': 'report.views.objects.report_reactive_precursor_doc',
    },
    'report_laboratory_room': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'html':'report.views.lab_room.lab_room_html',
        'pdf':'report.views.base.base_pdf',
        'xls':'report.views.lab_room.lab_room_doc',
        'xlsx':'report.views.lab_room.lab_room_doc',
        'ods':'report.views.lab_room.lab_room_doc',
    },
    'report_objects': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ReportObjectForm',
        'html': 'report.views.objects.report_objects_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.objects.report_objects_doc',
        'xlsx': 'report.views.objects.report_objects_doc',
        'ods': 'report.views.objects.report_objects_doc'
    },
    'report_limit_objects': {
        'task':'report.tasks.task_report',
        'form': 'report.forms.ValidateReportForm',
        'html': 'report.views.objects.report_limit_object_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.objects.report_limit_object_doc',
        'xlsx': 'report.views.objects.report_limit_object_doc',
        'ods': 'report.views.objects.report_limit_object_doc',
    },
    'report_objectschanges': {
        'task':'report.tasks.task_report',
        'form': 'report.forms.ValidateObjectLogChangeReportForm',
        'html': 'report.views.objects.report_objectlogchange_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.objects.report_objectlogchange_doc',
        'xlsx': 'report.views.objects.report_objectlogchange_doc',
        'ods': 'report.views.objects.report_objectlogchange_doc',
    },
    'report_furniture': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'html':'report.views.furniture.furniture_html',
        'pdf':'report.views.base.base_pdf',
        'xls':'report.views.furniture.furniture_doc',
        'xlsx':'report.views.furniture.furniture_doc',
        'ods':'report.views.furniture.furniture_doc',
    },
    'report_organization_reactive_list': {
        'task':'report.tasks.task_report',
        'form': 'report.forms.OrganizationReactiveForm',
        'html': 'report.views.objects.report_reactive_exposition_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.objects.report_organization_reactive_list_doc',
        'xlsx': 'report.views.objects.report_organization_reactive_list_doc',
        'ods': 'report.views.objects.report_organization_reactive_list_doc'

    },
    'report_waste_objects': {
        'task':'report.tasks.task_report',
        'form': 'report.forms.DiscardShelfForm',
        'html': 'report.views.discard_objects.report_discard_object_html',
        'pdf': 'report.views.base.base_pdf',
        'xls': 'report.views.discard_objects.report_discard_object_doc',
        'xlsx': 'report.views.discard_objects.report_discard_object_doc',
        'ods': 'report.views.discard_objects.report_discard_object_doc'

    },
}
