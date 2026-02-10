from __future__ import absolute_import, unicode_literals

import importlib
import re
from collections import defaultdict
from datetime import date, timedelta

from async_notifications.utils import send_email_from_template
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from auth_and_perms.models import ProfilePermission
from laboratory.models import (
    ShelfObject,
    Laboratory,
    PrecursorReport,
    InformScheduler,
    Furniture, Object, ObjectMaximumLimit, BlockedListNotification,
)
from .limit_shelfobject import send_email_limit_objs
from .task_utils import (
    create_informsperiods,
    save_object_report_precursor,
    build_precursor_report_from_reports,
)
from .utils_base_unit import get_conversion_units

app = importlib.import_module(settings.CELERY_MODULE).app


def get_limited_shelf_objects(lab):
    return ShelfObject.objects.filter(in_where_laboratory=lab)


@app.task
def notify_about_product_limit_reach():
    labs = Laboratory.objects.all()
    object_list = []
    for lab in labs:
        for shelfobjects in get_limited_shelf_objects(lab):
            object_list.append(shelfobjects)
        send_email_limit_objs(lab, object_list, enqueued=False)
        object_list.clear()


@app.on_after_configure.connect
def setup_daily_tasks(sender, **kwargs):
    sender.add_periodic_task(2, notify_about_product_limit_reach.s(), name="notify")


@app.task()
def create_precursor_reports():
    day = date.today()

    for lab in Laboratory.objects.all():
        previos_report = PrecursorReport.objects.filter(laboratory=lab)

        if previos_report.exists():
            previos_report = previos_report.last()
        else:
            previos_report = None
        month_belong = day.month - 1
        if day.month == 1:
            month_belong = 12
        report = PrecursorReport.objects.create(
            month=day.month,
            year=day.year,
            laboratory=lab,
            consecutive=add_consecutive(lab),
            month_belong=month_belong,
        )
        save_object_report_precursor(report)
        build_precursor_report_from_reports(report, previos_report)


def add_consecutive(lab):
    report = PrecursorReport.objects.filter(laboratory=lab).last()
    consecutive = 1
    if report is not None:
        consecutive = int(report.consecutive) + 1

    return consecutive


@app.task
def create_informs_based_on_period():
    informschedulerquery = InformScheduler.objects.filter(active=True)
    for informscheduler in informschedulerquery:
        create_informsperiods(informscheduler)


@app.task()
def remove_shelf_not_furniture():
    furnitures = Furniture.objects.all()
    for furniture in furnitures:
        obj_pks = re.findall(r"\d+", furniture.dataconfig)
        furniture.shelf_set.all().exclude(pk__in=obj_pks).delete()

@app.task()
def add_maximum_object_stock_per_day():
    laboratories = Laboratory.objects.all()
    for laboratory in laboratories:
        objects = ShelfObject.objects.filter(in_where_laboratory=laboratory, object__type= Object.REACTIVE).values_list("object", flat=True)
        objects = set(objects)
        for obj in Object.objects.filter(pk__in=objects):
            total = sum([get_conversion_units(shelfobject.measurement_unit, shelfobject.quantity)
            for shelfobject in ShelfObject.objects.filter(in_where_laboratory=laboratory, object=obj)])
            shelfobject = ShelfObject.objects.filter(in_where_laboratory=laboratory, object=obj).first()
            data = {
                "quantity": total,
                "laboratory": laboratory,
                "object": obj,
            }
            if shelfobject:
                data["measurement_unit"] = shelfobject.measurement_unit
            ObjectMaximumLimit.objects.create(**data)

@app.task()
def send_expiration_email():
    tomorrow = date.today() + timedelta(days=1)
    expiring_reactives = ShelfObject.objects.filter(
        object__type=Object.REACTIVE,
        reactive_expiration_date=tomorrow
    ).select_related('object', 'shelf__furniture__labroom')
    reactives_by_lab = defaultdict(list)
    for reactive in expiring_reactives:
        lab = reactive.in_where_laboratory
        if lab:
            reactives_by_lab[lab].append(reactive)

    for lab, reactives in reactives_by_lab.items():
        blocked = BlockedListNotification.objects.filter(
            laboratory=lab,
            object__in=[r.object for r in reactives]
        )
        blocked_emails = list(blocked.values_list("user__email", flat=True))
        cc = ContentType.objects.get_for_model(Laboratory)
        user_ids = ProfilePermission.objects.filter(
            content_type=cc,
            object_id=lab.pk
        ).values_list("profile__user", flat=True)
        users = User.objects.filter(id__in=user_ids)
        emails = [user.email for user in users if
                  user.email and user.email not in blocked_emails]
        if emails:
            schema = "https" if not settings.DEBUG else "http"
            domain = Site.objects.get_current().domain
            url = f"/lab/{lab.pk}/blocknotifications/"
            context = {
                'laboratory': lab,
                'shelf_object': reactives,
                'blockurl': f"{schema}://{domain}{url}",
                'domain': domain,
            }
            send_email_from_template(
                "Expiring reactives",
                emails,
                context=context,
                enqueued=False,
                user=None,
                upfile=None,
            )
