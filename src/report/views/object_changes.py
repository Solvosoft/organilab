from django.conf import settings
from django.db.models import Sum
from django.utils.timezone import now
from django.utils.translation import gettext as _
from laboratory.models import (
    Object,
    ObjectLogChange,
    Laboratory,
    Catalog,
    Shelf,
    ShelfObject,
)
from laboratory.utils import get_user_laboratories
from report.models import ObjectChangeLogReport, ObjectChangeLogReportBuilder
from report.utils import filter_period


def resume_queryset(report, queryset, objs=None, log_filters=None):

    laboratories = set(queryset.values_list("laboratory__pk", flat=True))
    builder = []
    total = 0
    doc_list = []

    for laboratory in laboratories:
        lab = Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list("object", "measurement_unit"))

        for obj in objects:
            object_log = None
            obj_using = Object.objects.filter(pk=obj[0]).first()
            catalog = Catalog.objects.get(pk=obj[1])
            query_values = query.filter(object=obj_using, measurement_unit__pk=obj[1])
            object_diff = queryset.filter(
                laboratory=lab, object=obj_using, measurement_unit__pk=obj[1]
            ).aggregate(total=Sum("diff_value"))["total"]
            if query_values:

                object_log = ObjectChangeLogReport.objects.create(
                    task_report=report,
                    laboratory=lab,
                    object=obj_using,
                    unit=catalog,
                    diff_value=object_diff,
                )

            for values in query_values:

                object_builder = ObjectChangeLogReportBuilder(
                    report=object_log,
                    user=values.user,
                    old_value=values.old_value,
                    new_value=values.new_value,
                    diff_value=values.diff_value,
                    update_time=values.update_time,
                )

                builder.append(object_builder)

                total += 1
            if object_log:
                ObjectChangeLogReportBuilder.objects.bulk_create(builder)
            builder.clear()
        shelf_obj = set(
            objs.filter(in_where_laboratory=lab).values_list(
                "object", "measurement_unit"
            )
        )

        for obj in shelf_obj:
            log_now = queryset.filter(
                laboratory=lab, object__pk=obj[0], measurement_unit__pk=obj[1]
            )
            if not log_now.exists():
                old_log = ObjectLogChange.objects.filter(
                    laboratory=lab, object__pk=obj[0], measurement_unit__pk=obj[1]
                ).distinct()
                if old_log.exists():

                    ObjectChangeLogReport.objects.create(
                        task_report=report,
                        laboratory=lab,
                        object=Object.objects.filter(pk=obj[0]).first(),
                        unit=Catalog.objects.filter(pk=obj[1]).first(),
                        diff_value=0,
                    )

                    total += 1

    return total


def resume_queryset_doc(report, queryset, objs, log_filters):

    laboratories = set(queryset.values_list("laboratory__pk", flat=True))
    builder = []
    total = 0
    doc_list = []

    for laboratory in laboratories:
        object_log = None
        lab = Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list("object", "measurement_unit"))

        for obj in objects:

            object_log = None
            obj_using = Object.objects.filter(pk=obj[0]).first()
            catalog = Catalog.objects.get(pk=obj[1])
            query_values = query.filter(object=obj_using, measurement_unit__pk=obj[1])
            object_diff = queryset.filter(
                laboratory=lab, object=obj_using, measurement_unit__pk=obj[1]
            ).aggregate(total=Sum("diff_value"))["total"]
            if query_values:
                object_log = True
            for values in query_values:

                try:
                    user = values.user.get_full_name()
                    if not user:
                        user = values.user.username
                except Exception as e:
                    user = ""
                builder.append(
                    [
                        user,
                        values.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                        values.old_value,
                        values.new_value,
                        values.diff_value,
                    ]
                )
                total += 1

            if object_log:
                cas = ""
                if hasattr(obj_using, "sustancecharacteristics"):
                    cas = obj_using.cas_code if (obj_using.cas_code) else ""
                doc_list.append([f"{lab.name} | {obj_using.name} {cas}"])
                doc_list.append([f": {object_diff} {catalog.description}"])
                doc_list.append(
                    [
                        _("User"),
                        _("Day"),
                        _("Initial amount"),
                        _("Final amount"),
                        _("Difference"),
                    ]
                )
                doc_list.extend(builder)
                doc_list.append([])
                doc_list.append([])
            builder = []
        shelf_obj = set(
            objs.filter(in_where_laboratory=lab).values_list(
                "object", "measurement_unit"
            )
        )

        for obj in shelf_obj:
            log_now = queryset.filter(
                laboratory=lab, object__pk=obj[0], measurement_unit__pk=obj[1]
            )
            if not log_now.exists():
                old_log = ObjectLogChange.objects.filter(
                    laboratory=lab, object__pk=obj[0], measurement_unit__pk=obj[1]
                ).distinct()

                if old_log.exists():
                    old_log = old_log.last()
                    cas = old_log.object.cas_code if old_log.object.cas_code else ""
                    doc_list.append([f"{lab.name} | {old_log.object.name} {cas}"])
                    doc_list.append([f": {0} {old_log.measurement_unit.description}"])
                    doc_list.append([])
                    doc_list.append([])
                total += 1

    return {"record": total, "content": doc_list}


def get_queryset(report):
    query = (
        ObjectLogChange.objects.all()
        .using(settings.READONLY_DATABASE)
        .order_by("update_time")
    )
    labs = Laboratory.objects.all().using(settings.READONLY_DATABASE)
    filters = {}
    object_log_filters = {}
    if "period" in report.data:
        if report.data["period"]:
            query = filter_period(report.data["period"], query)
    if "precursor" in report.data:
        if report.data["precursor"]:
            query = query.filter(precursor=True)
            object_log_filters["precursor"] = True
    if "all_labs_org" in report.data:
        if report.data["all_labs_org"]:
            labs = get_user_laboratories(report.created_by)
            query = query.filter(laboratory__in=labs)
            filters["in_where_laboratory__in"] = labs
        else:
            query = query.filter(laboratory__pk=report.data["lab_pk"])
            filters["in_where_laboratory__pk"] = report.data["lab_pk"]
    else:
        query = query.filter(laboratory__pk=report.data["lab_pk"])
        filters["in_where_laboratory__pk__in"] = report.data["lab_pk"]
    obj = ShelfObject.objects.filter(**filters).using(settings.READONLY_DATABASE)

    return query, obj, object_log_filters


def get_dataset_objectlogchanges(report, is_doc=False, column_list=None):
    queryset, objs, log_filters = get_queryset(report)
    object_list = None
    if is_doc:
        object_list = resume_queryset_doc(report, queryset, objs, log_filters)
    else:
        object_list = resume_queryset(report, queryset, objs, log_filters)
    return object_list
