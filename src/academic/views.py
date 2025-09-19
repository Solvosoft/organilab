import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from rest_framework import status

from academic.forms import (
    ProcedureForm,
    ProcedureStepForm,
    ObjectForm,
    ObservationForm,
    StepForm,
    ReservationForm,
    MyProcedureForm,
    CommentProcedureStepForm,
    AddObjectStepForm,
    ValidateProcedureReservationForm,
)
from academic.models import (
    Procedure,
    ProcedureStep,
    ProcedureRequiredObject,
    ProcedureObservations,
    MyProcedure,
    CommentProcedureStep,
)
from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)
from laboratory.models import (
    Object,
    Catalog,
    Furniture,
    ShelfObject,
    Laboratory,
    OrganizationStructure,
)
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import (
    ListView as DJListView,
    CreateView as DJCreateView,
    UpdateView as DJUpdateView,
)
from organilab import settings
from reservations_management.models import ReservedProducts
from . import convertions


@login_required
@permission_required("academic.add_procedurestep")
def add_steps_wrapper(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    procedure = get_object_or_404(Procedure, pk=pk)
    proc_step = ProcedureStep.objects.create(procedure=procedure)
    organilab_logentry(request.user, proc_step, ADDITION, relobj=org_pk)
    return redirect(
        reverse("academic:update_step", kwargs={"pk": proc_step.pk, "org_pk": org_pk})
    )


@permission_required("academic.view_myprocedure")
def get_my_procedures(request, org_pk, lab_pk):
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization)
    context = {
        "form": MyProcedureForm(),
        "laboratory": laboratory.pk,
        "org_pk": org_pk,
        "reservation_form": ReservationForm,
    }
    return render(request, "academic/procedure.html", context=context)


@permission_required("academic.add_myprocedure")
def create_my_procedures(request, org_pk, lab_pk, content_type, model):
    form = MyProcedureForm(request.POST)
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization)
    if form.is_valid():
        my_procedure = form.save(commit=False)
        content = ContentType.objects.get(app_label=content_type, model=model)
        my_procedure.content_type = content
        my_procedure.object_id = lab_pk
        my_procedure.organization = organization
        my_procedure.created_by = request.user
        my_procedure.save()
        organilab_logentry(
            request.user, my_procedure, ADDITION, "myprocedures", relobj=lab_pk
        )
        return redirect(
            reverse(
                "academic:get_my_procedures",
                kwargs={"lab_pk": lab_pk, "org_pk": org_pk},
            )
        )

    return render(
        request,
        "academic/procedure.html",
        context={"laboratory": lab_pk, "org_pk": org_pk},
    )


@permission_required("academic.delete_myprocedure")
def remove_my_procedure(request, org_pk, lab_pk, pk):
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization)
    my_procedure = get_object_or_404(MyProcedure, pk=pk)
    if my_procedure:
        organilab_logentry(
            request.user, my_procedure, DELETION, "myprocedures", relobj=lab_pk
        )
        my_procedure.delete()
        return redirect(
            reverse(
                "academic:get_my_procedures",
                kwargs={"lab_pk": lab_pk, "org_pk": org_pk},
            )
        )
    return redirect(
        reverse(
            "academic:get_my_procedures", kwargs={"lab_pk": lab_pk, "org_pk": org_pk}
        )
    )


def update_my_procedure_data(item, data):
    if "key" in item and "defaultValue" in item:
        if item["key"] in data:
            if item["type"] not in ["selectboxes", "select", "custom_select"]:
                item["defaultValue"] = data[item["key"]][0]
            elif item["type"] in ["select", "custom_select"]:
                # Save data from a select, allows multiple selection
                item["defaultValue"] = data[item["key"]]
            else:
                aux_list = {}
                for key in data[item["key"]]:
                    aux_list[key] = True
                    item["defaultValue"] = aux_list

    if "components" in item:
        for child in item["components"]:
            update_my_procedure_data(child, data)

    if "rows" in item and isinstance(item["rows"], (list, tuple)):
        for row in item["rows"]:
            for child in row:
                update_my_procedure_data(child, data)


@permission_required("academic.change_myprocedure")
def complete_my_procedure(request, org_pk, lab_pk, pk):
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization)
    my_procedure = get_object_or_404(MyProcedure, pk=pk)
    steps = ProcedureStep.objects.filter(procedure=my_procedure.custom_procedure)
    comments = CommentProcedureStep.objects.filter(
        procedure_step__procedure=my_procedure.custom_procedure
    )
    schema = my_procedure.schema
    form = json.dumps(schema, indent=2)
    context = {
        "schema": form,
        "my_procedure": my_procedure,
        "laboratory": lab_pk,
        "org_pk": org_pk,
        "form": CommentProcedureStepForm,
        "steps": steps,
        "comments": comments,
    }

    if request.method == "POST":
        data = dict(request.POST)
        my_procedure.status = request.POST.get("status")
        del data["csrfmiddlewaretoken"]
        del data["status"]

        result = {}

        for d in data.keys():
            x, y = d.find("[") + 1, d.find("]")
            result[d[x:y]] = data[d]
        update_my_procedure_data(schema, result)
        my_procedure.schema = schema
        my_procedure.save()
        return JsonResponse(
            {
                "url": reverse(
                    "academic:get_my_procedures",
                    kwargs={"lab_pk": lab_pk, "org_pk": org_pk},
                )
            }
        )

    return render(request, "academic/complete_my_procedure.html", context)


@method_decorator(permission_required("academic.view_procedure"), name="dispatch")
class ProcedureListView(DJListView):
    model = Procedure
    queryset = Procedure.objects.none()
    template_name = "academic/list.html"


@method_decorator(permission_required("academic.add_procedure"), name="dispatch")
class ProcedureCreateView(DJCreateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = "academic/procedure_create.html"

    def get_context_data(self, **kwargs):
        context = super(ProcedureCreateView, self).get_context_data()
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy(
            "academic:procedure_list",
            kwargs={
                "org_pk": self.org,
            },
        )
        return success_url

    def form_valid(self, form):
        procedure = form.save(commit=False)
        content_type = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )
        procedure.content_type = content_type
        procedure.object_id = self.org
        procedure.save()
        organilab_logentry(
            self.request.user,
            procedure,
            ADDITION,
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return super(ProcedureCreateView, self).form_valid(form)


@method_decorator(permission_required("academic.change_procedure"), name="dispatch")
class ProcedureUpdateView(DJUpdateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = "academic/procedure_create.html"

    def get_context_data(self, **kwargs):
        context = super(ProcedureUpdateView, self).get_context_data()
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy(
            "academic:procedure_list", kwargs={"org_pk": self.org}
        )
        return success_url

    def form_valid(self, form):
        procedure = form.save()
        organilab_logentry(
            self.request.user,
            procedure,
            CHANGE,
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return super(ProcedureUpdateView, self).form_valid(form)


@login_required
@permission_required("academic.view_procedure")
def procedureStepDetail(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    steps = Procedure.objects.filter(pk=pk).first()
    return render(
        request,
        "academic/detail.html",
        {"object": steps, "procedure": pk, "org_pk": org_pk},
    )


@method_decorator(permission_required("academic.add_procedurestep"), name="dispatch")
class ProcedureStepCreateView(FormView):
    form_class = StepForm
    template_name = "academic/procedure_steps.html"

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepCreateView, self).get_context_data()
        context["object_form"] = ObjectForm
        context["observation_form"] = ObservationForm
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        procedure = get_object_or_404(Procedure, pk=int(self.kwargs["pk"]))
        step = ProcedureStep.objects.create(
            procedure=procedure,
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
        )
        step.save()
        organilab_logentry(
            self.request.user,
            step,
            ADDITION,
            changed_data=form.changed_data,
            relobj=procedure.content_object,
        )

        return response

    def get_success_url(self):
        org = self.kwargs["org_pk"]
        success_url = reverse_lazy("academic:procedure_list", kwargs={"org_pk": org})
        return success_url


@method_decorator(permission_required("academic.change_procedurestep"), name="dispatch")
class ProcedureStepUpdateView(DJUpdateView):
    model = ProcedureStep
    form_class = ProcedureStepForm
    template_name = "academic/procedure_steps.html"

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepUpdateView, self).get_context_data()
        context["object_form"] = ObjectForm
        context["observation_form"] = ObservationForm
        context["step"] = ProcedureStep.objects.get(pk=int(self.kwargs["pk"]))
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy(
            "academic:procedure_list", kwargs={"org_pk": self.org}
        )
        return success_url

    def form_valid(self, form):
        procedurestep = form.save()
        organilab_logentry(
            self.request.user,
            procedurestep,
            CHANGE,
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return super(ProcedureStepUpdateView, self).form_valid(form)


@login_required
@permission_required("academic.add_procedurerequiredobject")
def save_object(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    """ Add a Required object """
    form = AddObjectStepForm(request.POST)
    step = get_object_or_404(ProcedureStep, pk=pk)
    state = status.HTTP_200_OK
    form_errors = None
    msg = _("There is no object in the inventory with this unit of measurement")
    if form.is_valid():
        unit = form.cleaned_data["unit"]
        obj = form.cleaned_data["object"]
        objects = ProcedureRequiredObject.objects.create(
            step=step,
            object=obj,
            quantity=form.cleaned_data["quantity"],
            measurement_unit=unit,
        )

        str_obj = f"{objects.object} {objects.quantity} {str(objects.measurement_unit)}"
        change_message = str_obj + " procedure required object has been added"
        organilab_logentry(
            request.user,
            objects,
            ADDITION,
            changed_data=form.changed_data,
            change_message=change_message,
            relobj=org_pk,
        )
    else:
        form_errors = form.errors
        state = status.HTTP_400_BAD_REQUEST
    return JsonResponse(
        {"data": get_objects(pk), "msg": msg, "form": form_errors}, status=state
    )


@login_required
@permission_required("academic.delete_procedurestep")
def delete_step(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    step = ProcedureStep.objects.get(pk=int(request.POST["pk"]))
    organilab_logentry(
        request.user, step, DELETION, relobj=step.procedure.content_object
    )
    step.delete()
    return JsonResponse({"data": True})


@permission_required("academic.delete_procedurerequiredobject")
def remove_object(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    obj = ProcedureRequiredObject.objects.get(pk=int(request.POST["pk"]))
    obj.delete()
    organilab_logentry(request.user, obj, DELETION)
    return JsonResponse({"data": get_objects(pk)})


def get_objects(pk):
    objects_list = ProcedureRequiredObject.objects.filter(step__id=pk)
    aux = []
    for data in objects_list:
        aux.append(
            {
                "obj": str(data.object),
                "unit": str(data.measurement_unit),
                "id": data.pk,
                "amount": data.quantity,
            }
        )
    result = json.dumps(aux)
    return result


@login_required
@permission_required("academic.add_procedureobservations")
def save_observation(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    step = get_object_or_404(ProcedureStep, pk=pk)
    form = ObservationForm(request.POST)
    result = status.HTTP_200_OK
    form_errors = {}
    if form.is_valid():
        objects = ProcedureObservations.objects.create(
            step=step, description=form.cleaned_data["procedure_description"]
        )
        objects.save()
        organilab_logentry(
            request.user, objects, ADDITION, changed_data=["description"]
        )
    else:
        form_errors = form.errors
        result = status.HTTP_400_BAD_REQUEST
    return JsonResponse(
        {"data": get_observations(pk), "errors": form_errors}, status=result
    )


def get_observations(pk):
    obsevations = ProcedureObservations.objects.filter(step__id=pk)
    aux = []
    for data in obsevations:
        aux.append({"description": data.description, "id": data.pk})
    result = json.dumps(aux)
    return result


@login_required
@permission_required("academic.delete_procedureobservations")
def remove_observation(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    obj = get_object_or_404(ProcedureObservations, pk=int(request.POST["pk"]))
    obj.delete()
    organilab_logentry(request.user, obj, DELETION)
    return JsonResponse({"data": get_observations(pk)})


@login_required
@permission_required("academic.view_procedure")
def get_procedure(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    procedure = get_object_or_404(Procedure, pk=pk)
    result_status = status.HTTP_200_OK
    msg = ""
    if not ProcedureRequiredObject.objects.filter(step__procedure=procedure).exists():
        result_status = status.HTTP_400_BAD_REQUEST
        msg = _(
            "The procedure don't has objects, please add some "
            "objects in the procedure steps"
        )

    return JsonResponse(
        {"title": procedure.title, "pk": procedure.pk, "msg": msg}, status=result_status
    )


@permission_required("academic.delete_procedure")
def delete_procedure(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    procedure = get_object_or_404(Procedure, pk=int(request.POST["pk"]))
    procedure.delete()
    organilab_logentry(request.user, procedure, DELETION)
    return JsonResponse({"data": True})


@permission_required("reservations_management.add_reservedproducts")
def generate_reservation(request, org_pk, lab_pk):
    lab = get_object_or_404(Laboratory, pk=lab_pk)
    org = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, org)
    organization_can_change_laboratory(lab, org)
    form = ValidateProcedureReservationForm(request.POST)
    form_error = None
    result = status.HTTP_400_BAD_REQUEST
    state = False
    obj_unknown = []

    if form.is_valid():
        procedure = form.cleaned_data["procedure"]
        procedure_obj = (
            ProcedureRequiredObject.objects.filter(step__procedure=procedure)
            .exclude(quantity__lte=0)
            .distinct("pk")
        )
        if procedure_obj.exists():

            for obj in procedure_obj:
                shelfobjects = ShelfObject.objects.filter(
                    in_where_laboratory=lab,
                    object=obj.object,
                    measurement_unit=obj.measurement_unit,
                ).aggregate(total=Coalesce(Sum("quantity"), 0.0))

                if shelfobjects["total"] < obj.quantity:
                    obj_unknown.append(obj.object.__str__())

            if obj_unknown:
                result = status.HTTP_400_BAD_REQUEST
                return JsonResponse(
                    {
                        "msg": _(
                            "The laboratory does not have enough of this object to be able to reserve it. <br>%(list)s"
                        )
                        % {"list": ",<br>".join(obj_unknown)}
                    },
                    status=result,
                )

            form = ReservationForm(request.POST)

            if not obj_unknown and form.is_valid():
                state = True
                result = status.HTTP_200_OK
                add_procedure_reservation(request, procedure_obj, form, lab, org)

        else:
            result = status.HTTP_400_BAD_REQUEST
            return JsonResponse({"msg": _("Don't has objects")}, status=result)

    else:
        result = status.HTTP_400_BAD_REQUEST
        form_error = form.errors

    return JsonResponse(
        {"state": state, "errors": obj_unknown, "form": form_error}, status=result
    )


def add_procedure_reservation(request, objects, form, lab, org):
    for obj in objects:
        shelf_objects = (
            ShelfObject.objects.filter(
                in_where_laboratory=lab,
                object=obj.object,
                measurement_unit=obj.measurement_unit,
            )
            .distinct()
            .order_by("quantity")
        )
        obj_quantity = obj.quantity
        total = 0
        for shelf_object in shelf_objects:
            shelf_object_total = shelf_object.quantity
            result = 0

            if total < obj_quantity:
                if obj_quantity <= shelf_object_total:
                    result = obj_quantity - total
                elif total + shelf_object_total > obj_quantity:
                    result = obj_quantity - total
                else:
                    result += shelf_object_total
                total += result
                reserved = ReservedProducts.objects.create(
                    shelf_object=shelf_object,
                    user=request.user,
                    initial_date=form.cleaned_data["initial_date"],
                    final_date=form.cleaned_data["final_date"],
                    amount_required=result,
                    laboratory=lab,
                    organization=org,
                )
                organilab_logentry(
                    request.user, reserved, ADDITION, changed_data=form.changed_data
                )
