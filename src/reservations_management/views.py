import json

from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry, get_lab_ids
from laboratory.views.djgeneric import ListView, UpdateView
from .forms import ReservationActionForm
from .functions import (
    add_decrease_stock_task,
    _allocate_boxes_if_needed,
    _increase_box_stock,
    _increase_standard_stock,
)
from .models import (
    Reservations,
    ReservedProducts,
    ACCEPTED,
    DENIED,
    BORROWED,
    REQUESTED,
    RETURNED,
    CLOSED,
)


class ReservationsListView(PermissionRequiredMixin, ListView):
    model = Reservations
    paginate_by = 10
    permission_required = "reservations_management.view_reservations"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = OrganizationStructure.objects.filter(pk=self.kwargs["org_pk"]).first()
        user = self.request.user
        profile = getattr(user, "profile", None)
        lab_ids = get_lab_ids(org, profile)
        reservation_list = (
            ReservedProducts.objects.filter(
                reservation__isnull=False,
                laboratory__id__in=lab_ids,
            )
            .values_list("reservation__pk", flat=True)
            .distinct()
        )

        context["reservations"] = Reservations.objects.filter(
            pk__in=reservation_list, status=self.kwargs["status"]
        )
        return context


class ManageReservationView(PermissionRequiredMixin, UpdateView):
    template_name = "reservations_management/manage_reservation.html"
    form_class = ReservationActionForm
    model = Reservations
    permission_required = "reservations_management.change_reservations"

    def get_success_url(self):
        return reverse(
            "reservations_management:reservations_list",
            kwargs={"status": self.object.status, "org_pk": self.org},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.object.reservedproducts_set.select_related(
            "shelf_object", "shelf_object__object", "shelf_object__measurement_unit"
        ).all()
        context["has_partial"] = self.object.reservedproducts_set.exclude(
            status=REQUESTED
        ).exists()
        return context

    def form_valid(self, form):
        reservation = form.save(commit=False)
        action = self.request.POST.get("action")
        org = get_object_or_404(OrganizationStructure, pk=self.kwargs["org_pk"])
        reservation.organization = org
        reservation.created_by = self.request.user

        if action == "accept":
            reservation.status = ACCEPTED
            reservation.save()
            for product in reservation.reservedproducts_set.filter(status=REQUESTED):
                if (
                    product.final_date >= timezone.now()
                    and product.initial_date > timezone.now()
                ):
                    _allocate_boxes_if_needed(product)
                    add_decrease_stock_task(product)
                    product.status = BORROWED
                    product.save(update_fields=["status"])
                else:
                    product.status = DENIED
                    product.save(update_fields=["status"])
        elif action == "reject":
            reservation.status = DENIED
            reservation.save()
            reservation.reservedproducts_set.exclude(
                status__in=[BORROWED, RETURNED]
            ).update(status=DENIED)
        else:
            reservation.save()

        organilab_logentry(
            self.request.user,
            self.object,
            CHANGE,
            changed_data=["status"],
            change_message=_("Updated reservation status to '%(status)s'")
            % {"status": self.object.get_status_display()},
            relobj=self.object,
        )
        return redirect(self.get_success_url())


class ProductActionView(PermissionRequiredMixin, View):
    """Accept or deny an individual ReservedProduct."""

    http_method_names = ["post"]
    permission_required = "reservations_management.change_reservedproducts"

    def get_product(self):
        return get_object_or_404(
            ReservedProducts,
            pk=self.kwargs["product_pk"],
            reservation__pk=self.kwargs["pk"],
        )

    def post(self, request, *args, **kwargs):
        product = self.get_product()
        action = request.POST.get("action")

        if action == "accept" and product.status == REQUESTED:
            if (
                product.final_date >= timezone.now()
                and product.initial_date > timezone.now()
            ):
                _allocate_boxes_if_needed(product)
                add_decrease_stock_task(product)
                product.status = BORROWED
            else:
                product.status = DENIED
            product.save(update_fields=["status"])

        elif action == "reject" and product.status == REQUESTED:
            product.status = DENIED
            product.save(update_fields=["status"])

        return redirect(
            reverse(
                "reservations_management:manage_reservation",
                kwargs={"org_pk": kwargs["org_pk"], "pk": kwargs["pk"]},
            )
        )


class ReturnProductView(PermissionRequiredMixin, View):
    http_method_names = ["post"]
    permission_required = "reservations_management.change_reservedproducts"

    def get_product(self):
        return get_object_or_404(
            ReservedProducts,
            pk=self.kwargs["product_pk"],
            reservation__pk=self.kwargs["pk"],
        )

    def post(self, request, *args, **kwargs):
        product = self.get_product()

        if product.initial_date > timezone.now():
            return JsonResponse(
                {
                    "success": False,
                    "error": str(
                        _(
                            "The reservation has not started yet. Returns are not allowed before the initial date."
                        )
                    ),
                }
            )

        org = get_object_or_404(OrganizationStructure, pk=kwargs["org_pk"])

        if product.shelf_object.is_box:
            try:
                boxes_to_return = json.loads(request.POST.get("boxes_to_return", "[]"))
            except (json.JSONDecodeError, ValueError):
                return JsonResponse(
                    {"success": False, "error": str(_("Invalid data."))}
                )

            if not boxes_to_return:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(_("Select at least one box to return.")),
                    }
                )

            reserved_map = {b["code"]: b["units"] for b in product.reserved_boxes}
            for item in boxes_to_return:
                if item["code"] not in reserved_map:
                    return JsonResponse(
                        {"success": False, "error": str(_("Invalid box code."))}
                    )
                if not isinstance(item["units"], (int, float)) or item["units"] < 0:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": str(
                                _("Units must be greater than 0 for box %(code)s.")
                                % {"code": item["code"]}
                            ),
                        }
                    )
                if item["units"] > reserved_map[item["code"]]:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": str(
                                _("Units exceed reserved amount for box %(code)s.")
                                % {"code": item["code"]}
                            ),
                        }
                    )

            success = _increase_box_stock(request.user, product, org, boxes_to_return)
        else:
            try:
                amount = float(request.POST.get("amount_returned", 0))
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "error": str(_("Invalid amount."))}
                )

            if amount < 0 or amount > product.amount_required:
                return JsonResponse(
                    {
                        "success": False,
                        "error": str(
                            _("Amount must be between 0 and %(max)s.")
                            % {"max": product.amount_required}
                        ),
                    }
                )

            success = _increase_standard_stock(request.user, product, amount)

        if success:
            return JsonResponse({"success": True})
        return JsonResponse(
            {
                "success": False,
                "error": str(
                    _("Could not process the return. Please verify the values.")
                ),
            }
        )


class CloseReservationView(PermissionRequiredMixin, View):
    http_method_names = ["post"]
    permission_required = "reservations_management.change_reservations"

    def post(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservations, pk=kwargs["pk"])
        reservation.status = CLOSED
        reservation.save(update_fields=["status"])
        organilab_logentry(
            request.user,
            reservation,
            CHANGE,
            changed_data=["status"],
            change_message=_("Closed reservation"),
            relobj=reservation,
        )
        return redirect(
            reverse(
                "reservations_management:reservations_list",
                kwargs={"org_pk": kwargs["org_pk"], "status": reservation.status},
            )
        )
