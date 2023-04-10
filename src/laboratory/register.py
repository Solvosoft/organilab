REPORT_FORMS ={
    'reactive_precursor': {
        'task':'laboratory.tasks.report_reactive_precursor',
        'form':'report.forms.ValidateReportForm',
        'title':'List of reactive precursors',
    },
    'laboratory_room': {
        'task':'report.tasks.laboratory_room_report',
        'form':'report.forms.ValidateLaboratoryRoomReportForm',
        'title':'Objects list by laboratory',
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
}