from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _


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