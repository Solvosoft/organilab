# encoding: utf-8

"""
Free as freedom will be 2/9/2016

@author: luisza
"""
from django.contrib import messages
from django.contrib.admin.models import ADDITION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from djreservation.models import Product

from laboratory.models import ShelfObject
from djreservation.views import ProductReservationView
from django.utils.translation import gettext_lazy as _
from laboratory.utils import organilab_logentry


@method_decorator(permission_required("laboratory.add_shelfobject"), name="dispatch")
class ShelfObjectReservation(ProductReservationView):
    base_model = ShelfObject
    modelpk = None
    amount_field = "quantity"
    extra_display_field = ["limit_quantity", "measurement_unit"]

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "reservation"):
            return super(ShelfObjectReservation, self).dispatch(
                request, *args, **kwargs
            )
        return redirect(reverse("add_user_reservation"))

    def form_valid(self, form):
        self.object = Product(
            amount=form.cleaned_data["amount"],
            amount_field=self.amount_field,
            reservation=self.request.reservation,
            content_object=self.instance,
        )
        self.object.save()
        organilab_logentry(
            self.request.user,
            self.object,
            ADDITION,
            "product",
            changed_data=form.changed_data,
        )
        messages.success(self.request, _("Product added successful"))
        return self.get_success_view()
