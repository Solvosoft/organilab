"""La pantalla del labview: un mapa digital del laboratorio sobre API.

La vista es deliberadamente delgada.  Resuelve el deep-link en el servidor,
entrega un estado inicial y deja que el JavaScript pida el árbol; todo lo demás
—la cuadrícula, la tabla, las acciones— son datos que llegan por JSON.

Vive en paralelo a ``laboratory:rooms_list``, que queda intacta hasta que Luis
valide esta.
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.utils.decorators import method_decorator

from laboratory.models import Laboratory
from laboratory.views.djgeneric import ListView
from laboratory.views.labview_helpers import (
    LabviewDeepLinkMixin,
    LabviewSuggestionsMixin,
    ShelfObjectModalFormsMixin,
)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("laboratory.view_laboratoryroom", raise_exception=True),
    name="dispatch",
)
class LabView(
    LabviewDeepLinkMixin,
    LabviewSuggestionsMixin,
    ShelfObjectModalFormsMixin,
    ListView,
):
    model = Laboratory
    template_name = "laboratory/labview/labview.html"

    def get_queryset(self):
        # El árbol lo sirve la API; la plantilla no itera nada del servidor.
        return Laboratory.objects.filter(pk=self.lab)

    def get_urls(self):
        """Las rutas que el JavaScript necesita, resueltas por Django.

        El ``0`` de las rutas por pk es el marcador que la biblioteca sustituye
        (``url.replace('/0/', '/<id>/')``), el mismo convenio de
        ``equipment_edit.html``.
        """
        org, lab = self.org, self.lab
        org_lab = {"org_pk": org, "lab_pk": lab}
        return {
            "tree": reverse("laboratory:api-labview-tree-list", kwargs=org_lab),
            "labroom": reverse("laboratory:api-labview-labroom-list", kwargs=org_lab),
            "labroom_detail": reverse(
                "laboratory:api-labview-labroom-detail", kwargs={**org_lab, "pk": 0}
            ),
            "furniture": reverse(
                "laboratory:api-labview-furniture-list", kwargs=org_lab
            ),
            "furniture_detail": reverse(
                "laboratory:api-labview-furniture-detail", kwargs={**org_lab, "pk": 0}
            ),
            "shelf": reverse("laboratory:api-labview-shelf-list", kwargs=org_lab),
            "shelf_detail": reverse(
                "laboratory:api-labview-shelf-detail", kwargs={**org_lab, "pk": 0}
            ),
            "shelfobject_table": reverse(
                "laboratory:api-labview-shelfobjecttable-list", kwargs=org_lab
            ),
            "search_labview": reverse(
                "laboratory:api-search-labview-get", kwargs=org_lab
            ),
            "shelfobject_details": reverse(
                "laboratory:api-shelfobject-details", kwargs={**org_lab, "pk": 0}
            ),
            "recipient_list": reverse(
                "laboratory:api-shelfobject-recipient-list",
                kwargs={**org_lab, "pk": 0},
            ),
            "generate_label": reverse(
                "laboratory:generate_shelfobject_label",
                kwargs={"org_pk": org, "lab_pk": lab, "pk": 0, "recipient": 0},
            ),
            "shelfobject_log": reverse(
                "laboratory:get_shelfobject_log", kwargs={**org_lab, "pk": 0}
            ),
            "equipment_detail": reverse(
                "laboratory:equipment_shelfobject_detail",
                kwargs={**org_lab, "pk": 0},
            ),
            "shelfobject_report": reverse(
                "laboratory:reports_shelf_objects", kwargs={**org_lab, "pk": 0}
            ),
            "shelfobject_create": reverse(
                "laboratory:api-shelfobject-create-shelfobject", kwargs=org_lab
            ),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_shelfobject_modal_forms())
        context["user"] = self.request.user
        context["search_by_url"] = self.search_by_url(self.request.GET)
        context["suggestions_tag"] = self.get_suggestions_tag()
        context["labview_urls"] = self.get_urls()
        context["breadcrumbs"] = [
            {"label": str(self.object_list.first() or "")},
        ]
        return context
