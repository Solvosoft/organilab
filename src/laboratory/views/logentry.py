from django.shortcuts import render


def get_logentry_from_organization(request, pk):
    return render(request, 'laboratory/logentry_list.html', context={'organization': pk})