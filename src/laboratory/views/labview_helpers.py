"""Lo que comparten la vista de laboratorio antigua y el labview nuevo.

Aquí viven la resolución del deep-link, la lista blanca del buscador por
etiquetas y los formularios de los modales de objeto.  Se extraen de
``LaboratoryRoomsList`` sin cambiar una línea de comportamiento: las dos vistas
llaman a lo mismo, de modo que mientras convivan no puedan divergir.
"""

from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.template.loader import render_to_string

from laboratory.shelfobject.forms import (
    ContainerManagementForm,
    DecreaseShelfObjectForm,
    EditMaterialForm,
    EditReactiveForm,
    IncreaseShelfObjectForm,
    MoveShelfObjectForm,
    MoveShelfobjectWithContainerForm,
    ReserveShelfObjectForm,
    ShelfObjectBoxForm,
    ShelfObjectEquipmentForm,
    ShelfObjectMaterialForm,
    ShelfObjectReactiveForm,
    ShelfObjectRefuseEquipmentForm,
    ShelfObjectRefuseMaterialForm,
    ShelfObjectRefuseReactiveForm,
    TransferInShelfObjectApproveWithContainerForm,
    TransferOutShelfObjectForm,
)
from laboratory.forms import RecipientSizeForm
from laboratory.shelfobject.serializers import SearchShelfObjectSerializer


def display_shelfobject(data, name):
    return "%s %s" % (data["object__code"], data[name])


class LabviewDeepLinkMixin:
    """Resuelve ``?labroom=&furniture=&shelf=&shelfobject=`` en el servidor.

    Rellena la cadena **hacia arriba**: dado un estante deduce su mueble y su
    sala, de modo que un QR pegado en un estante abra el mapa ya desplegado
    hasta él.  Es un contrato, no un detalle: lo usan los QR ya impresos y los
    enlaces del mapa de peligros.
    """

    def get_labroom_data(self, serializer, result):
        if "labroom" in serializer.validated_data:
            result["labroom"] = [serializer.validated_data["labroom"].pk]

    def get_furniture_data(self, serializer, result):
        if "furniture" in serializer.validated_data:
            furniture = serializer.validated_data["furniture"]
            result["furniture"] = {"furniture": [furniture.pk]}

            if "labroom" not in serializer.validated_data:
                result["labroom"] = [furniture.labroom.pk]

    def get_shelf_data(self, serializer, result):
        if "shelf" in serializer.validated_data:
            shelf = serializer.validated_data["shelf"]
            result["shelf"] = {"shelf": [shelf.pk]}

            if "furniture" not in serializer.validated_data:
                result["furniture"] = {"furniture": [shelf.furniture.pk]}

            if "labroom" not in serializer.validated_data:
                result["labroom"] = [shelf.furniture.labroom.pk]

    def get_shelfobject_data(self, serializer, result):
        if "shelfobject" in serializer.validated_data:
            shelfobject = serializer.validated_data["shelfobject"]
            result["shelfobject"] = {"shelfobject": [shelfobject.pk]}
            result["shelfobject"]["filter_shelfobject"] = True

            if "shelf" not in serializer.validated_data:
                result["shelf"] = {"shelf": [shelfobject.shelf.pk]}

            if "furniture" not in serializer.validated_data:
                result["furniture"] = {"furniture": [shelfobject.shelf.furniture.pk]}

            if "labroom" not in serializer.validated_data:
                result["labroom"] = [shelfobject.shelf.furniture.labroom.pk]

    def search_by_url(self, kwargs):
        result = {}

        if any([i in kwargs for i in ["labroom", "furniture", "shelf", "shelfobject"]]):
            serializer = SearchShelfObjectSerializer(
                data=kwargs, context={"source_laboratory_id": self.lab}
            )

            if serializer.is_valid():
                self.get_labroom_data(serializer, result)
                self.get_furniture_data(serializer, result)
                self.get_shelf_data(serializer, result)
                self.get_shelfobject_data(serializer, result)
            else:
                raise Http404()
        return result


class LabviewSuggestionsMixin:
    """La lista blanca del buscador por etiquetas."""

    def get_obj_colors(self):
        return {
            "labroom": "#b8e4ff",
            "furniture": "#ff85d5",
            "shelf": "#ffe180",
            "shelfobject": "#95fab9",
            "object": "#f4fab4",
        }

    def get_whitelist_by_object(
        self,
        model,
        filters,
        color,
        value="name",
        filter_values=None,
        display_fnc=lambda x, y: x[y],
    ):
        suggestions_tag = []
        contenttype = ContentType.objects.filter(
            app_label="laboratory", model=model
        ).first()

        if filter_values is None:
            filter_values = ["pk", value]
        MODEL = contenttype.model_class()
        queryset = MODEL.objects.filter(**filters).values(*filter_values).distinct()
        whitelist = [
            {
                "pk": x["pk"],
                "value": "%d: %s" % (x["pk"], display_fnc(x, value)),
                "objtype": model,
                "color": color,
            }
            for x in queryset
        ]

        if whitelist:
            suggestions_tag = suggestions_tag + whitelist
        return suggestions_tag

    def get_suggestions_tag(self):
        color_by_obj = self.get_obj_colors()
        suggestions_tag = self.get_whitelist_by_object(
            "laboratoryroom", {"laboratory__pk": self.lab}, color_by_obj["labroom"]
        )
        suggestions_tag += self.get_whitelist_by_object(
            "furniture",
            {"labroom__laboratory__pk": self.lab},
            color_by_obj["furniture"],
        )
        suggestions_tag += self.get_whitelist_by_object(
            "shelf",
            {"furniture__labroom__laboratory__pk": self.lab},
            color_by_obj["shelf"],
        )
        suggestions_tag += self.get_whitelist_by_object(
            "shelfobject",
            {"in_where_laboratory__pk": self.lab, "containershelfobject": None},
            color_by_obj["shelfobject"],
            filter_values=["pk", "object__name", "object__code"],
            value="object__name",
            display_fnc=display_shelfobject,
        )
        suggestions_tag += self.get_whitelist_by_object(
            "object",
            {
                "shelfobject__in_where_laboratory": self.lab,
                "shelfobject__containershelfobject": None,
            },
            color_by_obj["object"],
            value="name",
        )
        return suggestions_tag


class ShelfObjectModalFormsMixin:
    """Los formularios que alimentan ``shelfobject/action_modal.html``.

    El labview reutiliza esos modales por ``{% include %}`` en vez de
    reescribir las acciones de objeto, así que necesita exactamente el mismo
    contexto que la vista antigua.
    """

    def get_shelfobject_modal_forms(self):
        return {
            "reserve_object_form": ReserveShelfObjectForm(prefix="reserve"),
            "transfer_out_object_form": TransferOutShelfObjectForm(
                users=self.request.user, lab_send=self.lab, org=self.org
            ),
            "increase_object_form": IncreaseShelfObjectForm(prefix="increase"),
            "decrease_object_form": DecreaseShelfObjectForm(prefix="decrease"),
            "move_object_form": MoveShelfObjectForm(
                group_name="groupmoveso", prefix="move"
            ),
            "move_object_container_form": MoveShelfobjectWithContainerForm(
                group_name="groupmovesocontainer",
                modal_id="#movesocontainerform",
                set_container_advanced_options=True,
                prefix="movewithcontainer",
            ),
            "equipment_form": ShelfObjectEquipmentForm(
                initial={"objecttype": 2}, org_pk=self.org, prefix="ef"
            ),
            "equipment_refuse_form": ShelfObjectRefuseEquipmentForm(
                initial={"objecttype": 2}, org_pk=self.org, prefix="erf"
            ),
            "reactive_form": ShelfObjectReactiveForm(
                initial={"objecttype": 0},
                org_pk=self.org,
                prefix="rf",
                modal_id="#reactive_form",
            ),
            "manage_container_form": ContainerManagementForm(
                modal_id="#managecontainermodal", prefix="mc"
            ),
            "reactive_refuse_form": ShelfObjectRefuseReactiveForm(
                initial={"objecttype": 0},
                org_pk=self.org,
                prefix="rff",
                modal_id="#reactive_refuse_form",
            ),
            "material_form": ShelfObjectMaterialForm(
                initial={"objecttype": 1}, org_pk=self.org, prefix="mf"
            ),
            "box_form": ShelfObjectBoxForm(
                initial={"objecttype": 0}, org_pk=self.org, prefix="bf"
            ),
            "update_box_form": ShelfObjectBoxForm(
                initial={"objecttype": 0},
                org_pk=self.org,
                prefix="ubf",
                modal_id="#edit_box_form",
                object_readonly=True,
            ),
            "material_refuse_form": ShelfObjectRefuseMaterialForm(
                initial={"objecttype": 1}, org_pk=self.org, prefix="mff"
            ),
            "transfer_in_approve_with_container_form": (
                TransferInShelfObjectApproveWithContainerForm(
                    modal_id="#transfer_in_approve_with_container_id_modal",
                    set_container_advanced_options=True,
                )
            ),
            "edit_form": EditReactiveForm(prefix="edit"),
            "edit_material_form": EditMaterialForm(prefix="edit_material"),
            "recipient_form": RecipientSizeForm(prefix="recipient"),
            "options": ["Reservation", "Add", "Transfer", "Substract"],
            "colors_tooltip": render_to_string(
                "laboratory/shelfobject/colors_tooltip.html", request=self.request
            ),
        }
