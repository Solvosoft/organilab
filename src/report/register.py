REPORT_FORMS ={
    'reactive_precursor': {
        'task':'laboratory.tasks.report_reactive_precursor',
        'form':'report.forms.ValidateReportForm',
        'title':'List of reactive precursors',
    },
    'report_laboratory_room': {
        'task':'report.tasks.task_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'title':'Objects list by laboratory',
        'html':'report.views.lab_room.lab_room_html',
        'pdf':'report.views.lab_room.lab_room_pdf'
    },
    'report_objects': {
        'task':'laboratory.tasks.report_objects',
        'form':'report.forms.ReportObjectForm',
        'title':'List of objects',
    },
    'report_limit_objects': {
        'task': 'laboratory.tasks.report_limit_objects',
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
    },
}