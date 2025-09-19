from laboratory.models import ShelfObject, Object
from laboratory.utils import get_user_laboratories
from django.db.models import F
from django.utils.translation import gettext as _


def convert_hcodereport_list(data):
    context = [
        [
            _("Laboratory"),
            _("Rooms"),
            _("Shelf"),
            _("Reactive"),
            _("Quantity"),
            _("Unit"),
            _("H code"),
        ]
    ]
    for result in data:
        reactive_id = result["reactive_id"]
        result["units"] = ShelfObject.get_units(result["units"])
        result["h_codes"] = ",".join(
            Object.objects.filter(pk=reactive_id).values_list(
                "sustancecharacteristics__h_code__code", flat=True
            )
        )
        context.append(
            [
                result["name"],
                result["room"],
                result["furniture"],
                result["reactive"],
                result["quantity"],
                result["units"],
                result["h_codes"],
            ]
        )
    return context


def convert_hcodereport_table(data):
    reactive_list = []
    context = {}
    for result in data:
        name = result.pop("name")
        reactive_id = result["reactive_id"]
        result["units"] = ShelfObject.get_units(result["units"])
        result["h_codes"] = Object.objects.filter(pk=reactive_id).values_list(
            "sustancecharacteristics__h_code__code",
            "sustancecharacteristics__h_code__description",
        )
        if name not in context:
            context[name] = len(reactive_list)
            reactive_list.append({"lab": name, "reactives": []})
        reactive_list[context[name]]["reactives"].append(result)
    return reactive_list


def get_function(name):
    dev = convert_hcodereport_table
    if name == "convert_hcodereport_list":
        dev = convert_hcodereport_list
    return dev


def filter_by_user_and_hcode(user, q, function="convert_hcodereport_table"):
    functiont = get_function(function)
    user_labs = get_user_laboratories(user)
    labs = user_labs.filter(
        laboratoryroom__furniture__shelf__shelfobject__object__sustancecharacteristics__h_code__in=q
    )
    # 'rooms__furniture__shelf__shelfobject__object__h_code__code'
    result = labs.annotate(
        room=F("laboratoryroom__name"),
        furniture=F("laboratoryroom__furniture__name"),
        reactive=F("laboratoryroom__furniture__shelf__shelfobject__object__name"),
        quantity=F("laboratoryroom__furniture__shelf__shelfobject__quantity"),
        units=F("laboratoryroom__furniture__shelf__shelfobject__measurement_unit"),
        reactive_id=F("laboratoryroom__furniture__shelf__shelfobject__object__pk"),
    ).values(
        "name",
        "laboratoryroom",
        "furniture",
        "reactive",
        "quantity",
        "units",
        "reactive_id",
    )
    return functiont(result)
