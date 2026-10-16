from django.conf import settings
from collections import defaultdict

from django.db.models import Max
from django.utils.translation import gettext as _
from laboratory.models import (
    Object,
    ObjectLogChange,
    Laboratory,
    Catalog,
    ShelfObject,
    OrganizationStructure,
)
from laboratory.utils import get_user_laboratories
from report.models import ObjectChangeLogReport, ObjectChangeLogReportBuilder
from report.utils import filter_period
from django.contrib.auth import get_user_model

User = get_user_model()


def _group_logs(queryset):
    """Bitácoras agrupadas por ``(laboratorio, objeto, unidad)``.

    Una consulta en vez de una por laboratorio y otras cuatro por par
    objeto-unidad. Dentro de cada grupo se respeta el orden del queryset.
    """
    groups = defaultdict(list)
    for log in queryset:
        groups[(log.laboratory_id, log.object_id, log.measurement_unit_id)].append(log)
    return groups


def _lookups(groups, extra_pairs=()):
    """Laboratorios, objetos y unidades que aparecen en el reporte, por pk."""
    lab_ids, object_ids, unit_ids = set(), set(), set()
    for lab_id, object_id, unit_id in list(groups) + list(extra_pairs):
        lab_ids.add(lab_id)
        object_ids.add(object_id)
        unit_ids.add(unit_id)
    labs = Laboratory.objects.in_bulk(lab_ids)
    objects = {
        obj.pk: obj
        for obj in Object.objects.filter(pk__in=object_ids).prefetch_related(
            "substancharacteristics_object"
        )
    }
    units = Catalog.objects.in_bulk(unit_ids)
    return labs, objects, units


def _unlogged_with_history(groups, objs):
    """Inventario sin movimientos en el periodo pero con historia anterior.

    Devuelve ``{(lab, objeto, unidad): pk de la última bitácora}`` para los
    pares que el reporte lista en cero. Solo cuenta para los laboratorios que
    tienen movimientos en el periodo, como siempre lo hizo el reporte.
    """
    lab_ids = {key[0] for key in groups}
    if not lab_ids:
        return {}, set()
    inventory = set(
        objs.filter(in_where_laboratory__in=lab_ids).values_list(
            "in_where_laboratory", "object", "measurement_unit"
        )
    )
    candidates = inventory - set(groups)
    if not candidates:
        return {}, candidates
    history = (
        ObjectLogChange.objects.filter(
            laboratory_id__in=lab_ids,
            object_id__in={key[1] for key in candidates},
        )
        .order_by()
        .values_list("laboratory_id", "object_id", "measurement_unit_id")
        .annotate(last_pk=Max("pk"))
    )
    with_history = {
        (lab, obj, unit): last_pk
        for lab, obj, unit, last_pk in history
        if (lab, obj, unit) in candidates
    }
    return with_history, candidates


def resume_queryset(report, queryset, objs=None, log_filters=None):
    groups = _group_logs(queryset)
    with_history, _candidates = _unlogged_with_history(groups, objs)
    labs, objects, units = _lookups(groups, with_history)
    user_ids = {log.user_id for logs in groups.values() for log in logs}
    user_map = User.objects.using(settings.READONLY_DATABASE).in_bulk(user_ids)

    total = 0
    keys = sorted(groups)
    reports = ObjectChangeLogReport.objects.bulk_create(
        [
            ObjectChangeLogReport(
                task_report=report,
                laboratory=labs[lab_id],
                object=objects.get(object_id),
                unit=units[unit_id],
                diff_value=round(sum(log.diff_value for log in groups[key]), 3),
            )
            for key in keys
            for lab_id, object_id, unit_id in [key]
        ]
    )
    builder = []
    for key, object_log in zip(keys, reports):
        for values in groups[key]:
            builder.append(
                ObjectChangeLogReportBuilder(
                    report=object_log,
                    user=user_map.get(values.user_id),
                    old_value=round(values.old_value, 3),
                    new_value=round(values.new_value, 3),
                    diff_value=round(values.diff_value, 3),
                    update_time=values.update_time,
                )
            )
            total += 1
    ObjectChangeLogReportBuilder.objects.bulk_create(builder, batch_size=1000)

    ObjectChangeLogReport.objects.bulk_create(
        [
            ObjectChangeLogReport(
                task_report=report,
                laboratory=labs[lab_id],
                object=objects.get(object_id),
                unit=units.get(unit_id),
                diff_value=0,
            )
            for lab_id, object_id, unit_id in sorted(with_history)
        ]
    )
    total += len(with_history)

    return total


def _user_display(log, user_map):
    if log.deleted_user_info:
        return log.deleted_user_info
    user = user_map.get(log.user_id)
    if user is None:
        return ""
    return user.get_full_name() or user.username


def resume_queryset_doc(report, queryset, objs, log_filters):
    groups = _group_logs(queryset)
    with_history, candidates = _unlogged_with_history(groups, objs)
    last_logs = ObjectLogChange.objects.in_bulk(with_history.values())
    labs, objects, units = _lookups(groups, with_history)
    user_ids = {log.user_id for logs in groups.values() for log in logs}
    user_map = User.objects.using(settings.READONLY_DATABASE).in_bulk(user_ids)

    total = 0
    doc_list = []
    for key in sorted(groups):
        lab_id, object_id, unit_id = key
        logs = groups[key]
        lab, obj_using, catalog = labs[lab_id], objects.get(object_id), units[unit_id]
        object_diff = sum(log.diff_value for log in logs)
        cas = obj_using.cas_code if obj_using else ""
        name = obj_using.name if obj_using else ""
        doc_list.append([f"{lab.name} | {name} {cas}"])
        doc_list.append([f"{_('Difference')}: {object_diff} {catalog.description}"])
        doc_list.append(
            [
                _("User"),
                _("Day"),
                _("Initial amount"),
                _("Final amount"),
                _("Difference"),
            ]
        )
        for values in logs:
            doc_list.append(
                [
                    _user_display(values, user_map),
                    values.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                    round(values.old_value, 3),
                    round(values.new_value, 3),
                    round(values.diff_value, 3),
                ]
            )
            total += 1
        doc_list.append([])
        doc_list.append([])

    for key in sorted(candidates):
        if key in with_history:
            lab_id, object_id, unit_id = key
            old_log = last_logs.get(with_history[key])
            obj = objects.get(object_id)
            unit = units.get(unit_id)
            cas = obj.cas_code if obj else ""
            name = obj.name if obj else ""
            description = unit.description if unit else ""
            if old_log is not None:
                doc_list.append([f"{labs[lab_id].name} | {name} {cas}"])
                doc_list.append([f"{_('Difference')}: 0 {description}"])
                doc_list.append([])
                doc_list.append([])
        # El conteo siempre incluyó todo el inventario sin movimientos.
        total += 1

    if not doc_list:
        # Sin movimientos la hoja salía vacía y no decía por qué.
        doc_list = [[_("No changes were recorded with the selected filters.")]]
    return {"record": total, "content": doc_list}


def get_queryset(report):
    query = (
        ObjectLogChange.objects.all()
        .using(settings.READONLY_DATABASE)
        .order_by("update_time")
    )

    labs = report.data.get("laboratory", [])
    general = not labs or len(labs) > 1
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()

    filters = {}
    object_log_filters = {}
    if "period" in report.data:
        if report.data["period"]:
            query = filter_period(report.data["period"], query)

    if "precursor" in report.data:
        if report.data["precursor"]:
            query = query.filter(precursor=True)
            object_log_filters["precursor"] = True

    if general:
        labs = labs if len(labs) > 1 else organization.get_my_laboratories
        query = query.filter(laboratory__pk__in=labs)
        filters["in_where_laboratory__pk__in"] = labs
    else:
        # `general` es falso solo cuando hay exactamente un laboratorio.
        lab_pk = labs[0]
        query = query.filter(laboratory__pk=lab_pk)
        filters["in_where_laboratory__pk"] = lab_pk

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
