from django.core.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _
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
    from pyEQL.chemical_formula import is_valid_formula
    if not is_valid_formula(value):
        return False
    return True


def validate_duplicate_initial_date(request):
    if request.method == 'GET':
        products = ReservedProducts.objects.filter(user_id=request.GET['user']).filter(status=request.GET['status']).filter(shelf_object=request.GET['obj'])
        for product in products:
            init_date = product.initial_date - timedelta(hours=6)
            db_initial_date = init_date.strftime("%m/%d/%Y %I:%M %p")
            if db_initial_date == request.GET['initial_date']:
                return JsonResponse({'is_valid': False})
    return JsonResponse({'is_valid': True})
