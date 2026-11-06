"""
Created on 4 may. 2017

@author: luis
"""

from django import template
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from academic.models import ProcedureStep, ProcedureRequiredObject
from laboratory.utils import get_user_laboratories
from laboratory import models as laboratorymodels
from laboratory.qr_nodes import node_laboratory_pk, node_qr_url

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perms(context, codename, lab_pk=None):
    if "request" in context:
        user = context["request"].user

        if user.has_perm(codename) or user.is_superuser:
            return True
        # Antes se probaba además check_lab_group_has_perm, pero esa función
        # exige el mismo user.has_perm(codename) que acaba de fallar: nunca
        # concedía nada.

    return False


@register.simple_tag(takes_context=True)
def index_permissions(context):
    dev = {
        "view_laboratory": has_perms(context, "laboratory.view_laboratory"),
        "view_procedure": has_perms(context, "academic.view_procedure"),
        "delete_laboratory": has_perms(context, "laboratory.delete_laboratory"),
        "add_laboratory": has_perms(context, "laboratory.add_laboratory"),
        "manage_laboratory": has_perms(context, "laboratory.change_laboratory"),
        "add_furniture": has_perms(context, "laboratory.add_furniture"),
        "add_object": has_perms(context, "laboratory.add_object"),
        "add_features": has_perms(context, "laboratory.add_objectfeatures"),
        "view_reports": has_perms(context, "laboratory.view_report"),
        "do_reports": has_perms(context, "laboratory.do_report"),
        "add_reservation": has_perms(context, "djreservation.add_reservation"),
        "view_organizationstructure": has_perms(
            context, "laboratory.view_organizationstructure"
        ),
        "add_reservations": has_perms(
            context, "reservations_management.add_reservation"
        ),
        "add_reserved_product": has_perms(
            context, "reservations_management.add_reserved_product"
        ),
        "delete_reserved_product": has_perms(
            context, "reservations_management.delete_reserved_product"
        ),
    }

    dev["show_labview"] = dev["view_laboratory"] or dev["view_procedure"]
    dev["admin_lab"] = (
        dev["add_laboratory"]
        or dev["manage_laboratory"]
        or dev["add_furniture"]
        or dev["add_object"]
        or dev["add_features"]
    )

    dev["show_reports"] = dev["view_reports"] or dev["do_reports"]

    return dev


@register.simple_tag
def check_perms(*args, **kwargs):
    user = kwargs["user"]
    perm = kwargs["perm"]
    return user.has_perm(perm)


@register.simple_tag(takes_context=True)
def get_user_labs(context):
    if "request" not in context:
        return []

    return get_user_laboratories(context["request"].user)


@register.simple_tag(takes_context=True)
def show_laboratory_name(context):
    if "laboratory" in context and context["laboratory"]:
        lab = laboratorymodels.Laboratory.objects.filter(
            pk=context["laboratory"]
        ).first()
        if lab:
            return str(lab)
    return ""


@register.filter()
def to_int(value):
    return int(value)


@register.filter()
def get_lab_pk(value):
    if isinstance(value, str):
        if len(value) == 0:
            return 0
        else:
            return value
    elif isinstance(value, int):
        return value


@register.simple_tag()
def show_reserve_button(procedure):
    show_reserve_btn = False
    steps = list(ProcedureStep.objects.filter(procedure=procedure))
    items = ProcedureRequiredObject.objects.filter(step__in=steps)
    if items.exists():
        show_reserve_btn = True
    return show_reserve_btn


@register.simple_tag(takes_context=True)
def get_qr_svg_img(context, object, **kwargs):
    """Enlace (e imagen) al QR de una sala, mueble o estante.

    Ya no incrusta el SVG en base64 ni lo genera al pintar la página: apunta a
    ``laboratory:node_qr_svg``, que lo crea la primera vez que se pide. En una
    lista de salas con decenas de estantes eso eran segundos de CPU y páginas
    de casi 2 MB.
    """
    # En las vistas de creación la instancia todavía no existe y la plantilla
    # llama al tag igual (furniture_form.html).
    if not getattr(object, "pk", None):
        return ""
    use_icon = kwargs.pop("icon", False)
    kwargs.pop("url", None)
    organization = kwargs.pop("organization")
    laboratory = context.get("laboratory")
    lab_pk = getattr(laboratory, "pk", laboratory) or node_laboratory_pk(object)
    qr_url = node_qr_url(organization, lab_pk, object)
    if qr_url is None:
        return ""

    if use_icon:
        icon = mark_safe('<i class="fa fa-qrcode" aria-hidden="true"></i>')
    else:
        icon = format_html(
            '<img alt="" src="{}" loading="lazy" {} />',
            qr_url,
            format_html_join(" ", '{}="{}"', kwargs.items()),
        )
    return format_html(
        '<a class="imgqr" href="{}?download=1" target="_blank" download="{}.svg">{}</a>',
        qr_url,
        str(object),
        icon,
    )


@register.simple_tag(takes_context=True)
def get_laboratory_view_url(context, *objs_list, **kwargs):
    laboratory = context["laboratory"]
    org_pk = context["org_pk"]
    request = context["request"]
    schema = request.scheme + "://"
    domain = schema + request.get_host()
    baseurl = domain + reverse(
        "laboratory:rooms_list", kwargs={"lab_pk": laboratory, "org_pk": org_pk}
    )
    url = "?"
    url_parts = []
    for obj in objs_list:
        if isinstance(obj, laboratorymodels.LaboratoryRoom):
            url_parts.append("labroom=%d" % obj.pk)
        elif isinstance(obj, laboratorymodels.Furniture):
            url_parts.append("furniture=%d" % obj.pk)
        elif isinstance(obj, laboratorymodels.Shelf):
            url_parts.append("shelf=%d" % obj.pk)
        elif isinstance(obj, laboratorymodels.ShelfObject):
            url_parts.append("shelfobject=%d" % obj.pk)

    url += "&".join(url_parts)
    return baseurl + url
