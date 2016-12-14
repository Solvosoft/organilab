from django.core.exceptions import ValidationError
from pyEQL.chemical_formula import is_valid_formula
from django.utils.translation import ugettext_lazy as _


def validate_molecular_formula(value):
    if not is_valid_formula(value):
        raise ValidationError(
            _('%(value)s is not a valid molecular formula'),
            params={'value': value}
        )
