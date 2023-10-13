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
