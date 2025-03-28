from risk_management.models import Regent


def get_regents_from_organization(org):
    return list(Regent.objects.filter(organization__pk=org).
                values_list('user__pk', flat=True))
