# encoding: utf-8

"""
Free as freedom will be 26/8/2016

@author: luisza
"""

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import path
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from laboratory.forms import (
    ObjectForm,
    ObjectUpdateForm,
    EquipmentForm,
    ReactiveForm,
    ReactiveLimitForm,
    ObjectMaterialForm,
)
from laboratory.models import (
    Laboratory,
    BlockedListNotification,
    OrganizationStructure,
    MaterialCapacity,
    Object,
)
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import CreateView, DeleteView, UpdateView
from auth_and_perms.organization_utils import user_is_allowed_on_organization


# El listado unificado objectview_list se retiró (rendía vacío); cada tipo tiene su
# pantalla propia con ObjectCRUD, y ahí redirigen ahora crear/editar/borrar.
OBJECT_TYPE_LIST_URLNAMES = {
    Object.REACTIVE: "laboratory:sustance_list",
    Object.MATERIAL: "laboratory:object_view",
    Object.EQUIPMENT: "laboratory:equipment_list",
}


def get_object_list_url(type_id, org_pk, lab_pk):
    urlname = OBJECT_TYPE_LIST_URLNAMES.get(type_id, "laboratory:object_view")
    return reverse_lazy(urlname, args=(org_pk, lab_pk))


class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):

        @method_decorator(permission_required("laboratory.add_object"), name="dispatch")
        class ObjectCreateView(CreateView):
            permission_required = ("laboratory.add_object",)

            def get_success_url(self, *args, **kwargs):
                return get_object_list_url(self.object.type, self.org, self.lab)

            def get_form_kwargs(self):
                kwargs = super(ObjectCreateView, self).get_form_kwargs()
                kwargs["request"] = self.request
                return kwargs

            def form_valid(self, form):
                object = form.save(commit=False)
                organization = get_object_or_404(OrganizationStructure, pk=self.org)
                object.organization = organization
                changed_data = form.changed_data
                if object.type == Object.MATERIAL:
                    object.save()
                    is_container = object.is_container
                    if is_container:
                        capacity_data = {
                            "capacity": form.cleaned_data["capacity"],
                            "capacity_measurement_unit": form.cleaned_data[
                                "capacity_measurement_unit"
                            ],
                            "object": object,
                        }

                        MaterialCapacity.objects.create(**capacity_data)

                organilab_logentry(
                    self.request.user,
                    object,
                    ADDITION,
                    "object",
                    changed_data=changed_data,
                    change_message=_("Created object '%(name)s'")
                    % {"name": object.name},
                    relobj=self.lab,
                )
                return super(ObjectCreateView, self).form_valid(form)

        self.create = ObjectCreateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html",
        )

        @method_decorator(
            permission_required("laboratory.change_object"), name="dispatch"
        )
        class ObjectUpdateView(UpdateView):

            def get_success_url(self):
                return get_object_list_url(self.get_object().type, self.org, self.lab)

            def get_form_kwargs(self):
                kwargs = super(ObjectUpdateView, self).get_form_kwargs()
                kwargs["request"] = self.request
                return kwargs

            def form_valid(self, form):
                object = form.save()
                changed_data = form.changed_data

                capacity_form = None
                if object.type == Object.MATERIAL:
                    is_container = object.is_container
                    if is_container:

                        capacity_data = {
                            "capacity": form.cleaned_data["capacity"],
                            "capacity_measurement_unit": form.cleaned_data[
                                "capacity_measurement_unit"
                            ],
                            "object": object,
                        }
                        if hasattr(object, "materialcapacity"):
                            material_capacity = object.materialcapacity
                            material_capacity.capacity = capacity_data["capacity"]
                            material_capacity.capacity_measurement_unit = (
                                form.cleaned_data
                            )["capacity_measurement_unit"]
                            material_capacity.save()
                        else:
                            MaterialCapacity.objects.create(**capacity_data)

                organilab_logentry(
                    self.request.user,
                    object,
                    CHANGE,
                    "object",
                    changed_data=changed_data,
                    change_message=_("Updated object '%(name)s'")
                    % {"name": object.name},
                    relobj=self.lab,
                )
                return super(ObjectUpdateView, self).form_valid(object)

            def form_invalid(self, form):
                response = super().form_invalid(form)
                if self.request.accepts("text/html"):
                    return response
                else:
                    return JsonResponse(form.errors, status=400)

        capacity = None
        self.edit = ObjectUpdateView.as_view(
            model=self.model,
            form_class=ObjectUpdateForm,
            template_name=self.template_name_base + "_form.html",
        )

        @method_decorator(
            permission_required("laboratory.delete_object"), name="dispatch"
        )
        class ObjectDeleteView(DeleteView):

            def get_success_url(self):
                type_id = self.request.GET.get("type_id", "")
                return get_object_list_url(type_id, self.org, self.lab)

            def form_valid(self, form):
                success_url = self.get_success_url()
                organilab_logentry(
                    self.request.user,
                    self.object,
                    DELETION,
                    "object",
                    changed_data=["name", "code"],
                    change_message=_("Deleted object '%(name)s'")
                    % {"name": self.object.name},
                    relobj=self.lab,
                )
                self.object.delete()
                return HttpResponseRedirect(success_url)

        self.delete = ObjectDeleteView.as_view(
            model=self.model,
            success_url="/",
            template_name=self.template_name_base + "_delete.html",
        )

    def get_urls(self):
        return [
            path("create", self.create, name="objectview_create"),
            path("edit/<int:pk>", self.edit, name="objectview_update"),
            path("delete/<int:pk>", self.delete, name="objectview_delete"),
        ]


@login_required
def block_notifications(request, lab_pk, obj_pk):
    laboratory = Laboratory.objects.get(pk=lab_pk)
    object = Object.objects.get(pk=obj_pk)
    BlockedListNotification.objects.get_or_create(
        laboratory=laboratory, object=object, user=request.user
    )
    messages.success(
        request, "You won't be recieving notifications of this object anymore."
    )
    return render(request, "laboratory/block_object_notification.html")


@login_required
@permission_required("laboratory.view_object", raise_exception=True)
def view_equipment_list(request, org_pk, lab_pk):
    context = {
        "org_pk": org_pk,
        "lab_pk": lab_pk,
        "laboratory": lab_pk,
        "create_form": EquipmentForm(
            prefix="create",
            initial={
                "type": Object.EQUIPMENT,
                "organization": org_pk,
                "laboratory": lab_pk,
                "created_by": request.user.pk,
            },
            modal_id="#create_obj_form",
            laboratory_pk=lab_pk,
        ),
        "update_form": EquipmentForm(
            initial={"laboratory": lab_pk, "organization": org_pk, },
            prefix="update", modal_id="#update_obj_form", laboratory_pk=lab_pk
        ),
    }
    return render(request, "laboratory/equipment/list.html", context=context)


@login_required
@permission_required("laboratory.view_object", raise_exception=True)
def view_reactive_list(request, org_pk, lab_pk):
    context = {
        "org_pk": org_pk,
        "lab_pk": lab_pk,
        "laboratory": lab_pk,
        "create_form": ReactiveForm(
            prefix="create",
            initial={
                "type": Object.REACTIVE,
                "organization": org_pk,
                "laboratory": lab_pk,
                "created_by": request.user.pk,
            },
            modal_id="#create_obj_form",
            laboratory_pk=lab_pk,
        ),
        "update_form": ReactiveForm(
            prefix="update",
            initial={"laboratory": lab_pk},
            modal_id="#update_obj_form",
            laboratory_pk=lab_pk,
        ),
        "limit_form": ReactiveLimitForm(
            prefix="limit",
            initial={"laboratory": lab_pk},
            modal_id="#limit_obj_form",
            lab_pk=lab_pk,
        ),
    }
    return render(request, "laboratory/sustance/list.html", context=context)


@login_required
@permission_required("laboratory.view_object", raise_exception=True)
def object_view(request, org_pk=0, lab_pk=0):
    user_is_allowed_on_organization(request.user, org_pk)
    lab = get_object_or_404(Laboratory, pk=lab_pk)

    return render(
        request,
        "laboratory/object_list.html",
        context={
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "form_create": ObjectMaterialForm(prefix="create", render_type="as_p"),
            "form_update": ObjectMaterialForm(prefix="update", render_type="as_p"),
            "laboratory": lab_pk,
        },
    )
