from django.core.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _

from laboratory.forms import ReservedProductsForm
from reservations_management.models import ReservedProducts
from django.http import JsonResponse
from datetime import datetime, timedelta


def validate_molecular_formula(value):
    if not isValidate_molecular_formula(value):
        raise ValidationError(
            _('%(value)s is not a valid molecular formula'),
            params={'value': value}
        )


def isValidate_molecular_formula(value):
    # TODO:  HACER LA VALIDACIÓN
    if not value:
        return False
    return True


def validate_duplicate_initial_date(request):
    response = {'is_valid': False}

    if request.method == 'GET':
        form = ReservedProductsForm(request.GET)

        if form.is_valid():
            initial_date = form.cleaned_data['initial_date']

            filters = {
                'user_id': form.cleaned_data['user'],
                'status': form.cleaned_data['status'],
                'shelf_object': form.cleaned_data['obj']
            }

            products = ReservedProducts.objects.filter(**filters).distinct()

            for product in products:
                init_date = product.initial_date - timedelta(hours=6)
                db_initial_date = init_date.strftime("%m/%d/%Y %I:%M %p")
                if db_initial_date == initial_date:
                    return JsonResponse(response)

            response['is_valid'] = True
    return JsonResponse(response)
