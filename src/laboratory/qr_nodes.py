"""QR de salas, muebles y estantes servidos por URL y creados al pedirlos.

El árbol del labview y la lista de salas generaban el SVG de cada QR faltante
mientras armaban la respuesta (unos 130 ms por nodo) y además incrustaban el
base64 de cada QR: respuestas de varios MB y segundos de CPU. Ahora cada nodo
lleva solo la URL de su QR; el navegador la pide cuando la necesita y esta
vista lo crea la primera vez.

El QR siempre apunta al enlace profundo del labview (``?labroom=&furniture=
&shelf=``), el mismo que comparten los enlaces del mapa de peligros.
"""

from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.text import slugify

from auth_and_perms.organization_utils import (
    organization_can_change_laboratory,
    user_is_allowed_on_organization,
)
from laboratory.models import (
    Furniture,
    Laboratory,
    LaboratoryRoom,
    OrganizationStructure,
    Shelf,
)
from presentation.utils import build_qr_instance, get_qr_by_instance, update_qr_instance

#: tipo en la URL -> (modelo, ruta hasta el laboratorio, select_related)
NODE_KINDS = {
    "labroom": (LaboratoryRoom, "laboratory_id", ()),
    "furniture": (Furniture, "labroom__laboratory_id", ()),
    "shelf": (Shelf, "furniture__labroom__laboratory_id", ("furniture",)),
}

KIND_BY_MODEL = {model: kind for kind, (model, _path, _related) in NODE_KINDS.items()}


def labview_deep_link(org_pk, lab_pk, labroom=None, furniture=None, shelf=None):
    """El contrato de siempre: ``?labroom=&furniture=&shelf=``.

    Es el mismo query string que llevan los QR impresos y los enlaces del mapa
    de peligros, de modo que un enlace copiado desde la pantalla y uno pegado
    en la pared abran lo mismo.
    """
    base = reverse("laboratory:labview", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
    parts = []
    if labroom is not None:
        parts.append("labroom=%d" % labroom)
    if furniture is not None:
        parts.append("furniture=%d" % furniture)
    if shelf is not None:
        parts.append("shelf=%d" % shelf)
    return base + ("?" + "&".join(parts) if parts else "")


def node_deep_link(org_pk, lab_pk, node):
    if isinstance(node, LaboratoryRoom):
        return labview_deep_link(org_pk, lab_pk, labroom=node.pk)
    if isinstance(node, Furniture):
        return labview_deep_link(
            org_pk, lab_pk, labroom=node.labroom_id, furniture=node.pk
        )
    return labview_deep_link(
        org_pk,
        lab_pk,
        labroom=node.furniture.labroom_id,
        furniture=node.furniture_id,
        shelf=node.pk,
    )


def node_laboratory_pk(node):
    """El laboratorio de un nodo, para cuando el contexto no lo trae."""
    if isinstance(node, LaboratoryRoom):
        return node.laboratory_id
    if isinstance(node, Furniture):
        return node.labroom.laboratory_id
    return node.furniture.labroom.laboratory_id


class QRUrlBuilder:
    """Arma URLs de QR sin un ``reverse()`` por nodo."""

    def __init__(self, org_pk, lab_pk):
        self.templates = {
            kind: reverse(
                "laboratory:node_qr_svg",
                kwargs={"org_pk": org_pk, "lab_pk": lab_pk, "kind": kind, "pk": 0},
            )
            for kind in NODE_KINDS
        }

    def url(self, kind, pk):
        template = self.templates[kind]
        return template[: -len("0.svg")] + "%d.svg" % pk


def node_qr_url(org_pk, lab_pk, node):
    kind = KIND_BY_MODEL.get(type(node))
    if kind is None:
        return None
    return reverse(
        "laboratory:node_qr_svg",
        kwargs={"org_pk": org_pk, "lab_pk": lab_pk, "kind": kind, "pk": node.pk},
    )


def _same_target(stored_url, expected_url):
    stored, expected = urlparse(stored_url or ""), urlparse(expected_url)
    return (stored.path, stored.query) == (expected.path, expected.query)


@login_required
@permission_required("laboratory.view_laboratoryroom", raise_exception=True)
def node_qr_svg(request, org_pk, lab_pk, kind, pk):
    if kind not in NODE_KINDS:
        raise Http404()
    model, lab_path, related = NODE_KINDS[kind]
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    organization_can_change_laboratory(laboratory, organization, raise_exec=True)
    node = get_object_or_404(
        model.objects.select_related(*related), pk=pk, **{lab_path: lab_pk}
    )

    url = request.build_absolute_uri(node_deep_link(org_pk, lab_pk, node))
    qr = get_qr_by_instance(node, org_pk)
    if qr is None:
        qr = build_qr_instance(url, node, org_pk)
    elif not _same_target(qr.qr_url, url):
        # QR viejos apuntaban a la lista de salas: se rehacen hacia el labview.
        qr = update_qr_instance(url, node, org_pk)

    response = HttpResponse(qr.qr_image, content_type="image/svg+xml")
    response["Cache-Control"] = "private, max-age=3600"
    if request.GET.get("download"):
        name = slugify(str(node)) or kind
        response["Content-Disposition"] = 'attachment; filename="%s.svg"' % name
    return response
