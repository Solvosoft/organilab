from django.shortcuts import render


def get_logentry_from_organization(request, org_pk):
    return render(request, 'laboratory/logentry_list.html', context={'org_pk': org_pk})


get_logentry_from_organization.can_use_inactive_organization = True
