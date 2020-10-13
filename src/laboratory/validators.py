from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _
from reservations_management.models import ReservedProducts
from django.http import JsonResponse


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
    is_valid = True
    if request.method == 'GET':
        products = ReservedProducts.objects.filter(user_id=request.GET['user'])
        for product in products:
            if product.initial_date == request.GET['initial_date'] and product.shelf_object.id == request.GET['obj']:
                is_valid = False
    return JsonResponse({'is_valid': is_valid})


# if __name__ == '__main__':
#     o = 155
#     i = "2020-10-14 11:30:00-06"
#     u = 19
#     boolvar = validate_duplicate_initial_date(o, i, u)
#     print(boolvar)