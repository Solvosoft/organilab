REPORT_FORMS ={
    'reactive_precursor': {
        'task':'report.tasks.report_reactive_precursor',
        'form':'report.forms.ValidateReportForm',
        'title':'List of reactive precursors',
    },
    'report_laboratory_room': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'title':'Objects list by laboratory',
        'html':'report.views.lab_room.lab_room_html',
        'pdf':'report.views.lab_room.lab_room_pdf',
        'xls':'report.views.lab_room.lab_room_doc',
        'xlsx':'report.views.lab_room.lab_room_doc',
        'ods':'report.views.lab_room.lab_room_doc',
    },
    'report_objects': {
        'task':'laboratory.tasks.report_objects',
        'form':'report.forms.ReportObjectForm',
        'title':'List of objects',
    },
    'report_limit_objects': {
        'task': 'report.tasks.report_limit_objects',
        'form': 'report.forms.ValidateReportForm',
        'title': 'Limited shelf objects',
    },
    'report_objectschanges': {
        'task': 'report.tasks.object_log_change_report',
        'form': 'report.forms.ValidateObjectLogChangeReportForm',
        'title': 'Changes on Objects',
    },
    'report_furniture': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'title':'Furniture report',
        'html':'report.views.furniture.furniture_html',
        'pdf':'report.views.furniture.furniture_pdf',
        'xls':'report.views.furniture.furniture_doc',
        'xlsx':'report.views.furniture.furniture_doc',
        'ods':'report.views.furniture.furniture_doc',
    },
    'report_organization_reactive_list': {
        'task': 'report.tasks.report_organization_reactive_list',
        'form': 'report.forms.OrganizationReactiveForm',
        'title': 'User exposition',
    },
}